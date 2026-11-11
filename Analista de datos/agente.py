"""Agente mínimo: Haiku responde una pregunta usando las tools del servidor MCP.
Uso: .venv/bin/python agente.py "¿Cuál fue el margen bruto de Perfumería en el AF2026?"
     .venv/bin/python agente.py "¿primer turno?" "¿Y en la región Sur?" …   (una conversación, un turno por argumento)
     .venv/bin/python agente.py --traza trazas/P17.md "¿pregunta?" …         (además guarda la traza en ese archivo)"""
import asyncio
import json
import sys
from datetime import date
from pathlib import Path

import anthropic
from mcp import ClientSession, StdioServerParameters, stdio_client

MODELO = "claude-haiku-5-5"
MAX_VUELTAS = 10  # llamadas al modelo por pregunta; medido (2026-11-11): las preguntas usan 2 o 3

with open("Data/capa_semantica/glosario.md") as f:
    SISTEMA = ("Sos un analista de datos de Almacenes del Sur. Respondé en español. "
               "Cada número tiene que salir de la tool calcular: no calcules ni inventes números. "
               "consultar_sql es solo para lo que calcular no cubre (listados como promociones vigentes), nunca para medidas. "
               "Empezá llamando a ver_modelo para conocer las medidas y dimensiones.\n"
               "- Al nombrar sucursales o proveedores, mostrá código y nombre (agrupá por las dos dimensiones).\n"
               "- Si comparás ventas de dos períodos, informá la variación total y la comparable (comparables=True).\n\n"
               + f.read())


async def responder(pregunta, historial=None):
    """Responde una pregunta. Con historial (los mensajes de los turnos anteriores), sigue esa conversación (decisión 31)."""
    # Paso 1: lanzar el servidor MCP y pedirle la lista de tools
    servidor = StdioServerParameters(command=".venv/bin/python", args=["servidor_mcp.py"])
    async with (stdio_client(servidor) as (lectura, escritura), ClientSession(lectura, escritura) as mcp,
                anthropic.AsyncAnthropic() as claude):
        await mcp.initialize()
        tools = [{"name": t.name, "description": t.description, "input_schema": t.input_schema}
                 for t in (await mcp.list_tools()).tools]

        # Paso 2: el loop. Haiku contesta; si pide una tool, la corremos y le devolvemos el resultado
        mensajes = [*(historial or []), {"role": "user", "content": pregunta}]
        consultas = []  # cada llamada a calcular que salió bien: qué pidió y qué volvió (con el SQL)
        for _ in range(MAX_VUELTAS):
            respuesta = await claude.messages.create(model=MODELO, max_tokens=16000, system=SISTEMA,
                                                     tools=tools, messages=mensajes)
            mensajes.append({"role": "assistant", "content": respuesta.content})

            # Si no pidió ninguna tool, terminó: lo que escribió es la respuesta final
            if respuesta.stop_reason != "tool_use":
                texto = "".join(b.text for b in respuesta.content if b.type == "text")
                return {"pregunta": pregunta, "texto": texto, "consultas": consultas, "mensajes": mensajes}

            # Paso 3: correr cada tool que pidió, vía MCP, y juntar los resultados en un solo mensaje
            resultados = []
            for bloque in respuesta.content:
                if bloque.type != "tool_use":
                    continue
                print(f"→ {bloque.name}({json.dumps(bloque.input, ensure_ascii=False)})")
                resultado = await mcp.call_tool(bloque.name, bloque.input)
                if bloque.name != "ver_modelo" and not resultado.is_error:  # queda registrada (con su SQL)
                    consultas.append({"tool": bloque.name, "argumentos": bloque.input, "resultado": json.loads(resultado.content[0].text)})
                resultados.append({"type": "tool_result", "tool_use_id": bloque.id,
                                   "content": resultado.content[0].text, "is_error": resultado.is_error})
            mensajes.append({"role": "user", "content": resultados})

        # Si se trabó pidiendo tools sin terminar, corta en vez de seguir gastando (decisión 26)
        texto = f"No pude responder: se alcanzó el límite de {MAX_VUELTAS} llamadas al modelo sin una respuesta final."
        mensajes.append({"role": "assistant", "content": texto})  # el historial queda completo para el turno siguiente
        return {"pregunta": pregunta, "texto": texto, "consultas": consultas, "mensajes": mensajes}


async def conversar(turnos):
    """Una conversación: cada turno recibe el historial de los anteriores. El límite de vueltas es por turno."""
    historial, respuestas = [], []
    for turno in turnos:
        respuesta = await responder(turno, historial)
        historial = respuesta["mensajes"]
        respuestas.append(respuesta)
    return respuestas


def sqls(resultado):
    """Los SQL de un resultado con sus parámetros: uno, o uno por parte (actual/anterior, ventas/presupuesto)."""
    sql, parametros = resultado.get("sql"), resultado.get("parametros")
    if sql is None and isinstance(resultado.get("actual"), dict):  # comparación sin agrupar: un SQL por período
        return [(f"{parte}: ", resultado[parte]["sql"], resultado[parte]["parametros"]) for parte in ("actual", "anterior")]
    if isinstance(sql, dict):
        return [(f"{parte}: ", texto, (parametros or {}).get(parte)) for parte, texto in sql.items()]
    return [("", sql, parametros)] if sql else []


def resumen(resultado):
    """Los números principales de un resultado, para leer la traza sin abrir el JSON."""
    partes = [f"{clave} = {resultado[clave]['valor']}" for clave in ("actual", "anterior") if isinstance(resultado.get(clave), dict)]
    partes += [f"{clave} = {resultado[clave]}" for clave in ("valor", "variacion", "unidad_variacion", "comparables", "total")
               if resultado.get(clave) is not None]
    for clave in ("filas", "productos"):
        if isinstance(resultado.get(clave), list):
            partes.append(f"{len(resultado[clave])} {clave}" + (" (truncado)" if resultado.get("truncado") else ""))
    return " · ".join(partes)


def guardar_traza(respuestas, ruta):
    """Traza legible de una pregunta o conversación (decisión 36): cada turno con su respuesta y sus consultas con SQL."""
    turnos = [r["pregunta"] for r in respuestas]
    lineas = [f"# Traza: {' → '.join(turnos)}", "",
              f"Generada el {date.today()} con `{MODELO}`. Para volver a correrla:", "",
              "```", ".venv/bin/python agente.py " + " ".join(json.dumps(t, ensure_ascii=False) for t in turnos), "```"]
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
    if ruta_traza:
        guardar_traza(respuestas, ruta_traza)
        print(f"\nTraza guardada en {ruta_traza}")
