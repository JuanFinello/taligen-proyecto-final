"""Agente mínimo: Haiku responde una pregunta usando las tools del servidor MCP.
Uso: .venv/bin/python agente.py "¿Cuál fue el margen bruto de Perfumería en el AF2026?"
     .venv/bin/python agente.py "¿primer turno?" "¿Y en la región Sur?" …   (una conversación, un turno por argumento)
     .venv/bin/python agente.py --traza trazas/P17.md "¿pregunta?" …         (además guarda la traza en ese archivo)"""
import asyncio
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

import anthropic
from mcp import ClientSession, StdioServerParameters, stdio_client
from mcp.client.stdio import get_default_environment

import registro
import salida
from hooks import al_terminar, antes_de_tool, despues_de_tool, pedido_de_correccion, tools_de
from procesador_capa_semantica import sqls

MODELO = "claude-haiku-5-5"
MAX_VUELTAS = 10  # llamadas al modelo por pregunta; medido (2026-11-11): las preguntas usan 2 o 3
MAX_CORRECCIONES = 2  # veces que se le devuelve una respuesta con números sin respaldo (decisión 49)

# El glosario no se lee del disco: lo sirve el servidor MCP como prompt, y se suma al abrir la sesión
INSTRUCCIONES = ("Sos un analista de datos de Almacenes del Sur. Respondé en español. "
                 "Cada número tiene que salir de la tool calcular: no calcules ni inventes números. "
                 "consultar_sql es solo para lo que calcular no cubre (listados como promociones vigentes), nunca para medidas. "
                 "Empezá llamando a ver_modelo para conocer las medidas y dimensiones.\n"
                 "- Al nombrar sucursales o proveedores, mostrá código y nombre (agrupá por las dos dimensiones).\n"
                 "- Si comparás ventas de dos períodos, informá la variación total y la comparable (comparables=True).\n\n")
# El servidor no hereda el entorno: si se eligió otra base (BASE_ALMACENES), se la pasa
SERVIDOR = StdioServerParameters(command=".venv/bin/python", args=["servidor_mcp.py"],
                                 env={**get_default_environment(), **{k: v for k, v in os.environ.items()
                                                                      if k == "BASE_ALMACENES"}})


async def pedir_glosario(mcp):
    """El glosario, pedido al servidor MCP como prompt."""
    return (await mcp.get_prompt("glosario")).messages[0].content.text


async def glosario_del_servidor():
    """Para quien no tiene una sesión abierta (el coordinador): abre una solo para pedir el glosario."""
    async with stdio_client(SERVIDOR) as (lectura, escritura), ClientSession(lectura, escritura) as mcp:
        await mcp.initialize()
        return await pedir_glosario(mcp)


# Caché (semana 5, decisión 72). Tools + sistema son iguales en todas las llamadas: una marca fija al final del sistema
# los guarda. La conversación crece en cada vuelta del loop: el caché automático (cache_control en la llamada) pone la
# marca en el último bloque, así cada vuelta lee lo de la anterior y paga entero solo lo nuevo
CACHE = {"type": "ephemeral"}


def con_cache(texto):
    """El prompt de sistema como bloque con su marca de caché."""
    return [{"type": "text", "text": texto, "cache_control": CACHE}]


async def responder(pregunta, historial=None, tipo=None):
    """Responde una pregunta. Con historial (los mensajes de los turnos anteriores), sigue esa conversación (decisión 31).
    tipo: el que reconoció la puerta (decisión 78); solo va al registro, el agente no lo ve."""
    # Paso 1: lanzar el servidor MCP y pedirle la lista de tools
    async with (stdio_client(SERVIDOR) as (lectura, escritura), ClientSession(lectura, escritura) as mcp,
                anthropic.AsyncAnthropic() as claude):
        await mcp.initialize()
        sistema = con_cache(INSTRUCCIONES + await pedir_glosario(mcp))
        # Ordenadas por nombre: las tools van primero en el prefijo y cualquier cambio de orden rompe el caché
        tools = tools_de("analista", sorted(({"name": t.name, "description": t.description, "input_schema": t.input_schema}
                                             for t in (await mcp.list_tools()).tools), key=lambda t: t["name"]))

        # Paso 2: el loop. Haiku contesta; si pide una tool, la corremos y le devolvemos el resultado
        mensajes = [*(historial or []), {"role": "user", "content": pregunta}]
        consultas = []  # cada llamada a calcular que salió bien: qué pidió y qué volvió (con el SQL)
        correcciones, sueltos = 0, []
        for vuelta in range(1, MAX_VUELTAS + 1):
            inicio = time.monotonic()
            # La respuesta final sale con el esquema de salida.py (decisión 73); mientras pide tools, el loop sigue igual
            respuesta = await claude.messages.create(model=MODELO, max_tokens=16000, system=sistema, tools=tools,
                                                     messages=mensajes, cache_control=CACHE,
                                                     output_config=salida.FORMATO)
            segundos_modelo = time.monotonic() - inicio
            mensajes.append({"role": "assistant", "content": respuesta.content})

            # Si no pidió ninguna tool, terminó: lo que escribió es la respuesta final
            if respuesta.stop_reason != "tool_use":
                final, motivo = salida.leer("".join(b.text for b in respuesta.content if b.type == "text"))
                if final is None:  # cortada (max_tokens) o rechazada: el esquema no se cumple
                    registro.anotar("analista", pregunta, vuelta, respuesta, segundos_modelo, errores=["salida"])
                    return {"pregunta": pregunta, "texto": f"No pude responder: {motivo}.", "consultas": consultas,
                            "mensajes": mensajes, "registro": None, "problemas_registro": [motivo]}
                # Hook al terminar: cada número tiene que salir de una consulta (o de la pregunta). Si no, se le
                # devuelve el motivo para que corrija, como el error de una tool. Se controla todo lo que escribió
                sueltos = al_terminar("\n".join([final.texto, *final.supuestos, *final.cuentas]), mensajes)
                registro.anotar("analista", pregunta, vuelta, respuesta, segundos_modelo,
                                errores=["numeros_sin_respaldo"] if sueltos else [], sin_respaldo=sueltos)
                if sueltos and correcciones < MAX_CORRECCIONES:
                    correcciones += 1
                    mensajes.append({"role": "user", "content": pedido_de_correccion(sueltos)})
                    continue
                # El registro se valida antes de guardarse; si no pasa, no se guarda y queda el motivo
                datos, problemas = salida.validar(final, pregunta, consultas, sueltos, tipo)
                if datos:
                    salida.guardar(datos)
                return {"pregunta": pregunta, "texto": final.texto, "consultas": consultas, "mensajes": mensajes,
                        "numeros_sin_respaldo": sueltos, "registro": datos, "problemas_registro": problemas}

            # Paso 3: correr cada tool que pidió, vía MCP, y juntar los resultados en un solo mensaje
            resultados, pedidas, errores, inicio = [], [], [], time.monotonic()
            for bloque in respuesta.content:
                if bloque.type != "tool_use":
                    continue
                print(f"→ {bloque.name}({json.dumps(bloque.input, ensure_ascii=False)})")
                pedidas.append(bloque.name)
                # Hook antes: si frena, la tool no corre y el modelo recibe el motivo como error
                motivo = antes_de_tool("analista", bloque.name, bloque.input)
                if motivo:
                    errores.append(f"{bloque.name}: frenada: {motivo}")
                    resultados.append({"type": "tool_result", "tool_use_id": bloque.id, "content": motivo, "is_error": True})
                    continue
                resultado = await mcp.call_tool(bloque.name, bloque.input)
                if resultado.is_error:
                    errores.append(f"{bloque.name}: {resultado.content[0].text[:200]}")  # con el motivo, para la traza
                # Hook después: lo que salió bien queda registrado, con su SQL
                if consulta := despues_de_tool(bloque.name, bloque.input, resultado):
                    consultas.append(consulta)
                resultados.append({"type": "tool_result", "tool_use_id": bloque.id,
                                   "content": resultado.content[0].text, "is_error": resultado.is_error})
            mensajes.append({"role": "user", "content": resultados})
            registro.anotar("analista", pregunta, vuelta, respuesta, segundos_modelo,
                            time.monotonic() - inicio, pedidas, errores)

        # Si se trabó pidiendo tools sin terminar, corta en vez de seguir gastando (decisión 26)
        texto = f"No pude responder: se alcanzó el límite de {MAX_VUELTAS} llamadas al modelo sin una respuesta final."
        mensajes.append({"role": "assistant", "content": texto})  # el historial queda completo para el turno siguiente
        return {"pregunta": pregunta, "texto": texto, "consultas": consultas, "mensajes": mensajes, "registro": None,
                "problemas_registro": ["sin respuesta final"]}


async def conversar(turnos):
    """Una conversación: cada turno recibe el historial de los anteriores. El límite de vueltas es por turno."""
    historial, respuestas = [], []
    for turno in turnos:
        respuesta = await responder(turno, historial)
        historial = respuesta["mensajes"]
        respuestas.append(respuesta)
    return respuestas


def resumen(resultado):
    """Los números principales de un resultado, para leer la traza sin abrir el JSON."""
    partes = [f"{clave} = {resultado[clave]['valor']}" for clave in ("actual", "anterior") if isinstance(resultado.get(clave), dict)]
    partes += [f"{clave} = {resultado[clave]}" for clave in ("valor", "variacion", "unidad_variacion", "comparables", "total")
               if resultado.get(clave) is not None]
    for clave in ("filas", "productos"):
        if isinstance(resultado.get(clave), list):
            partes.append(f"{len(resultado[clave])} {clave}" + (" (truncado)" if resultado.get("truncado") else ""))
    return " · ".join(partes)


def guardar_traza(respuestas, ruta, comando="agente.py"):
    """Traza legible de una pregunta o conversación (decisión 36): cada turno con su respuesta y sus consultas con SQL."""
    turnos = [r["pregunta"] for r in respuestas]
    lineas = [f"# Traza: {' → '.join(turnos)}", "",
              f"Generada el {date.today()} con `{MODELO}`. Para volver a correrla:", "",
              "```", f".venv/bin/python {comando} " + " ".join(json.dumps(t, ensure_ascii=False) for t in turnos), "```"]
    for numero, respuesta in enumerate(respuestas, 1):
        titulo = f"Turno {numero}: " if len(respuestas) > 1 else ""
        lineas += ["", f"## {titulo}{respuesta['pregunta']}", "", "### Respuesta", "", respuesta["texto"], "",
                   f"### Consultas ({len(respuesta['consultas'])})"]
        if not respuesta["consultas"]:
            lineas += ["", "Ninguna en este turno."]
        for i, consulta in enumerate(respuesta["consultas"], 1):
            lineas += ["", f"**{i}. `{consulta['tool']}`** `{json.dumps(consulta['argumentos'], ensure_ascii=False)}`"]
            if resumen(consulta["resultado"]):
                lineas += ["", f"Resultado: {resumen(consulta['resultado'])}"]
            for parte, sql, parametros in sqls(consulta["resultado"]):
                lineas += ["", f"{parte}parámetros `{json.dumps(parametros, ensure_ascii=False, default=str)}`" if parametros else parte.rstrip(": "),
                           "```sql", sql, "```"]
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    Path(ruta).write_text("\n".join(lineas) + "\n")


if __name__ == "__main__":
    argumentos = sys.argv[1:]
    ruta_traza = None
    if argumentos[:1] == ["--traza"]:
        ruta_traza, argumentos = argumentos[1], argumentos[2:]
    if not argumentos:
        sys.exit('Uso: .venv/bin/python agente.py [--traza archivo.md] "¿pregunta?" ["¿turno siguiente?" …]')
    respuestas = asyncio.run(conversar(argumentos))
    for numero, respuesta in enumerate(respuestas, 1):
        if len(respuestas) > 1:
            print(f"\n===== Turno {numero}: {respuesta['pregunta']}")
        print(respuesta["texto"])
        if respuesta.get("problemas_registro"):
            print("⚠ registro no guardado: " + "; ".join(respuesta["problemas_registro"]))
    if ruta_traza:
        guardar_traza(respuestas, ruta_traza)
        print(f"\nTraza guardada en {ruta_traza}")
