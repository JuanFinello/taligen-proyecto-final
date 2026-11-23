"""Una sola puerta de entrada (decisión 78). El enunciado pide reconocer el tipo de cada pregunta («los archivos traen
solo el texto») y dice que una pregunta puntual se resuelve con un agente simple, y un diagnóstico o un informe hay
que descomponerlo. La puerta clasifica cada pregunta o turno con una llamada corta (ruteo: técnica del módulo 6, tool
forzada con enum, primero el motivo y después la etiqueta, validada con pydantic) y el código elige el camino:
diagnóstico e informe van al coordinador (informes.py); los demás tipos, al agente (agente.py), como hasta ahora.

Uso: .venv/bin/python analista/puerta.py                     (chat: una pregunta por vez; «?» muestra de dónde salió)
     .venv/bin/python analista/puerta.py [--traza archivo.md] "¿pregunta?" ["¿turno siguiente?" …]
     .venv/bin/python analista/puerta.py --medir [P09 C1 …]   (solo clasifica los casos de TIPOS en esperados.yaml y compara)"""
import asyncio
import contextlib
import json
import sys
import time
from pathlib import Path
from typing import Literal, Optional

import anthropic
import yaml
from pydantic import BaseModel, ValidationError

import informes
import registro
from agente import con_cache, glosario_del_servidor, guardar_traza, responder, resumen
from explicar import explicar
from sugerir import sugerencias
from procesador_capa_semantica import sqls, ver_modelo

MODELO = "claude-haiku-5-5"
TIPOS = ("puntual", "comparativa", "ranking", "diagnostico", "ambigua", "sin_dato", "informe")
AL_COORDINADOR = {"diagnostico", "informe"}

TOOL = {"name": "clasificar", "strict": True,
        "description": "Registra el tipo de la pregunta. No la respondas.",
        "input_schema": {"type": "object", "additionalProperties": False, "required": ["motivo", "tipo"], "properties": {
            # Primero el motivo: con la tool forzada, Haiku 5.5 no piensa antes de llamarla (módulo 6, 2.2)
            "motivo": {"type": "string", "description": "Primero razoná en una o dos oraciones: qué medida, qué "
                       "período y qué filtros pide, si dice dónde mirar, si la base lo tiene y si tiene más de una lectura."},
            "tipo": {"type": "string", "enum": list(TIPOS), "description": (
                "puntual: un valor de una medida, o un listado de lo que la base tiene (qué promociones hubo, qué productos), "
                "con su período y filtros. "
                "comparativa: la variación de una medida contra otro período o contra el presupuesto. "
                "ranking: ordenar grupos por una medida y quedarse con los primeros; también qué grupo de una "
                "dimensión que la pregunta nombra (proveedor, subcategoría…) explica una suba o una caída. "
                "diagnostico: pregunta por qué pasó algo, qué pasó con algo o si una conclusión es cierta, sin decir "
                "qué dimensión mirar: hay que buscar la causa haciendo varias consultas y cruzando dimensiones. "
                "ambigua: tiene más de una lectura razonable que cambia el número (calendario fiscal o comercial, "
                "medida o alcance) y ni la pregunta ni los turnos anteriores la resuelven. "
                "sin_dato: pide algo que la base no tiene (mirá el modelo de datos). "
                "informe: pide un informe o un reporte.")}}}}

INSTRUCCIONES = ("Clasificás preguntas de negocio sobre Almacenes del Sur antes de que alguien las responda. No las "
                 "respondas: llamá a clasificar con el tipo. Si es un turno de una conversación, los turnos anteriores "
                 "vienen arriba y el turno hereda de ellos el período, los filtros y la medida.\n\n"
                 "## Modelo de datos (lo que la base tiene)\n" + json.dumps(ver_modelo(), ensure_ascii=False) + "\n\n")


class Clasificacion(BaseModel):
    motivo: str
    tipo: Optional[Literal[TIPOS]]  # None: no se pudo clasificar (negativa o salida inválida); va al agente


_sistema = None


async def sistema():
    """Instrucciones, modelo de datos y glosario, en un bloque fijo con marca de caché. Se arma una vez por proceso."""
    global _sistema
    if _sistema is None:
        _sistema = con_cache(INSTRUCCIONES + await glosario_del_servidor())
    return _sistema


def con_anteriores(texto, anteriores):
    if not anteriores:
        return texto
    return ("Turnos anteriores de la conversación:\n" + "\n".join(f"- {a}" for a in anteriores)
            + f"\n\nTurno a clasificar: {texto}")


async def clasificar(texto, anteriores, claude):
    """El tipo de una pregunta o turno. anteriores: los turnos previos de la conversación (solo las preguntas)."""
    inicio = time.monotonic()
    respuesta = await claude.messages.create(model=MODELO, max_tokens=1000, system=await sistema(), tools=[TOOL],
                                             tool_choice={"type": "tool", "name": "clasificar"},
                                             messages=[{"role": "user", "content": con_anteriores(texto, anteriores)}])
    bloque = next((b for b in respuesta.content if b.type == "tool_use"), None)
    try:
        clasificacion = Clasificacion.model_validate(bloque.input) if bloque else None
    except ValidationError:
        clasificacion = None
    if clasificacion is None or clasificacion.tipo is None:
        # Haiku 5.5 puede negarse (stop_reason «refusal», módulo 6, 5.5) y entonces no hay tool. Va al agente, el
        # camino de siempre, y queda anotado: frenar la pregunta por no poder clasificarla sería peor
        clasificacion = Clasificacion(motivo=f"no se pudo clasificar (fin: {respuesta.stop_reason})", tipo=None)
    registro.anotar("clasificador", texto, 1, respuesta, time.monotonic() - inicio,
                    errores=[] if clasificacion.tipo else ["clasificacion"])
    return clasificacion


def contexto_para_coordinador(clasificacion, anteriores):
    """Lo que recibe el coordinador antes del pedido: el tipo y, en una conversación, los turnos con su respuesta."""
    partes = [f"(Tipo de pedido, según la puerta: {clasificacion.tipo}.)"]
    if anteriores:
        partes.append("Turnos anteriores de la conversación (el pedido hereda su período, filtros y medida):\n"
                      + "\n".join(f"- Pregunta: {p}\n  Respuesta: {r}" for p, r in anteriores))
    return "\n\n".join(partes) + "\n\nPedido: "


def al_historial(turno, resultado):
    """Un turno del coordinador, para el historial del agente en los turnos siguientes: la pregunta, las consultas
    que corrieron sus analistas (cada una como la llamada a la tool que fue, con su resultado) y el texto. Sin las
    consultas, el agente veía números en el historial que no salían de ninguna tool: si los repetía, el hook de fin
    los frenaba y se confundía (probado: en «¿Y cuánto vendió la región Sur?» rehízo el diagnóstico)."""
    mensajes = [{"role": "user", "content": turno}]
    if resultado["consultas"]:
        mensajes += [
            {"role": "assistant", "content": [{"type": "tool_use", "id": f"coordinador_{c['id']}", "name": c["tool"],
                                               "input": c["argumentos"]} for c in resultado["consultas"]]},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": f"coordinador_{c['id']}",
                                          "content": json.dumps(c["resultado"], ensure_ascii=False, default=str)}
                                         for c in resultado["consultas"]]}]
    # Sin la línea de la ruta (salidas/20261117-…): el hook tomaría sus dígitos por números sin respaldo
    texto = "\n".join(l for l in resultado["texto"].splitlines() if not l.startswith(("Diagnóstico: ", "PDF: ")))
    # Con quién lo respondió: si no, el agente lo toma como propio y a veces se pone a «corregirlo» en el turno siguiente
    return mensajes + [{"role": "assistant", "content": f"(Respondido como {resultado['tipo']} por el coordinador, con "
                                                        f"las consultas de arriba.)\n\n{texto.strip()}"}]


class Conversacion:
    """Una conversación que recuerda sus turnos: cada uno va por su camino y hereda lo anterior. La usan atender (los
    turnos de una vez) y el chat (de a uno, decisión 83)."""
    def __init__(self, carpeta=None, nombre="Informe", varios_turnos=False):
        self.carpeta, self.nombre, self.varios_turnos = carpeta, nombre, varios_turnos
        self.historial, self.anteriores = [], []

    async def turno(self, turno):
        """La respuesta de un turno, con tipo, motivo y ruta."""
        numero = len(self.anteriores) + 1
        async with anthropic.AsyncAnthropic() as claude:
            clasificacion = await clasificar(turno, [p for p, _ in self.anteriores], claude)
        print(f"[{clasificacion.tipo}] {clasificacion.motivo}", flush=True)
        if clasificacion.tipo in AL_COORDINADOR:
            destino = (self.carpeta or f"salidas/{registro.CORRIDA}") + (f"-t{numero}" if self.varios_turnos else "")
            try:
                resultado = await informes.atender(turno, destino, self.nombre,
                                                   contexto_para_coordinador(clasificacion, self.anteriores),
                                                   clasificacion.tipo)
            except informes.NoSeEntrega as motivo:
                resultado = {"texto": f"No pude responder: {motivo}.", "consultas": [], "salida": None}
            self.historial = [*self.historial, *al_historial(turno, {**resultado, "tipo": clasificacion.tipo})]
            respuesta = {"pregunta": turno, "mensajes": self.historial, "ruta": "coordinador", **resultado}
        else:
            respuesta = {**await responder(turno, self.historial, clasificacion.tipo), "ruta": "agente"}
            self.historial = respuesta["mensajes"]
        respuesta.update(tipo=clasificacion.tipo, motivo=clasificacion.motivo)
        self.anteriores.append((turno, respuesta["texto"]))
        return respuesta


async def atender(turnos, carpeta=None, nombre="Informe"):
    """Una pregunta o una conversación, cada turno por su camino. Cada respuesta lleva tipo, motivo y ruta."""
    conversacion = Conversacion(carpeta, nombre, len(turnos) > 1)
    return [await conversacion.turno(t) for t in turnos]


def tipos_esperados():
    """[(id, turno, texto, tipo esperado)] de TIPOS en esperados.yaml. «agente» = cualquier tipo que vaya al agente."""
    with open("Data/preguntas/esperados.yaml") as f:
        esperados = yaml.safe_load(f)["TIPOS"]
    textos = {p["id"]: p["texto"] for archivo in ("preguntas", "pedidos_de_informe")
              for p in json.load(open(f"Data/preguntas/{archivo}.json"))}
    conversaciones = {c["id"]: c["turnos"] for c in json.load(open("Data/preguntas/conversaciones.json"))}
    casos = []
    for id_, tipo in esperados.items():
        if id_ in conversaciones:
            casos += [(id_, n, conversaciones[id_][:n], t) for n, t in enumerate(tipo, 1)]
        else:
            casos.append((id_, None, [textos[id_]], tipo))
    return casos


async def medir(ids=()):
    """Solo la puerta: clasifica cada caso y lo compara con lo esperado. Lo que importa es la ruta; el tipo, aparte."""
    casos = [c for c in tipos_esperados() if not ids or c[0] in ids]
    semaforo = asyncio.Semaphore(5)
    async with anthropic.AsyncAnthropic() as claude:
        async def uno(caso):
            async with semaforo:
                id_, _, turnos, _ = caso
                registro.CASO.set(id_)
                return await clasificar(turnos[-1], turnos[:-1], claude)
        # El primero va solo y escribe el caché; los demás lo leen (decisión 74)
        resultados = [await uno(casos[0])] + list(await asyncio.gather(*(uno(c) for c in casos[1:])))
    ruta_bien = tipo_bien = con_tipo = 0
    for (id_, n, turnos, esperado), c in zip(casos, resultados):
        ruta_esperada = "coordinador" if esperado in AL_COORDINADOR else "agente"
        ruta = "coordinador" if c.tipo in AL_COORDINADOR else "agente"
        ruta_bien += ruta == ruta_esperada
        if esperado != "agente":
            con_tipo += 1
            tipo_bien += c.tipo == esperado
        marca = "✓" if ruta == ruta_esperada and esperado in ("agente", c.tipo) else ("~" if ruta == ruta_esperada else "✗")
        print(f"{marca} {id_}{f' t{n}' if n else '':<4} esperado {esperado:<12} dio {c.tipo:<12} · {turnos[-1][:60]}"
              + (f"\n      motivo: {c.motivo}" if marca != "✓" else ""))
    print(f"\nRuta: {ruta_bien} de {len(casos)} · tipo: {tipo_bien} de {con_tipo}")
    registro.resumen_corrida(registro.leer(registro.LLAMADAS), registro.CORRIDA)


def de_donde_salio(respuesta):
    """Cada consulta de una respuesta: en castellano, su resultado y el SQL que lo produjo (decisión 83)."""
    lineas = []
    for numero, consulta in enumerate(respuesta["consultas"], 1):
        lineas += ["", f"── Consulta {consulta.get('id', f'C{numero}')} ──", explicar(consulta)]
        if consulta["tool"] == "calcular" and resumen(consulta["resultado"]):
            lineas.append(f"Resultado: {resumen(consulta['resultado'])}")
        for parte, sql, parametros in sqls(consulta["resultado"]):
            lineas += [f"SQL {parte}".rstrip(": ") + (f" · parámetros {parametros}" if parametros else ""), sql]
    if respuesta.get("salida"):
        lineas += ["", f"Completo, con su traza: {respuesta['salida']}"]
    return "\n".join(lineas) if lineas else "Esta respuesta no usó consultas."


def costo_del_caso(caso):
    lineas = [l for l in registro.leer(registro.LLAMADAS) if l.get("corrida") == registro.CORRIDA and l.get("caso") == caso]
    return sum(l["costo_usd"] for l in lineas)


async def chat():
    """El chat en la terminal (decisión 83): una pregunta por vez, la conversación hereda lo anterior, y «?» muestra
    de dónde salió la última respuesta. Lo que va imprimiendo el agente (tools, planes) va a un .log, no a la pantalla."""
    conversacion = Conversacion(varios_turnos=True)
    log = Path(f"salidas/chat-{registro.CORRIDA}.log")
    log.parent.mkdir(parents=True, exist_ok=True)
    print("Analista de Almacenes del Sur. Preguntá lo que necesites (ventas, margen, presupuesto, stock, promociones),\n"
          "pedí un informe o un diagnóstico. «?» muestra de dónde salió la última respuesta; un número, una de las\n"
          "preguntas sugeridas; «salir» termina.")
    ultima, total, propuestas = None, 0.0, []
    while True:
        try:
            texto = input("\n› ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if texto.lower() in ("salir", "chau", "exit", "q"):
            break
        if not texto:
            continue
        if texto in ("?", "¿?", "de dónde salió", "fuente", "fuentes"):
            print(de_donde_salio(ultima) if ultima else "Todavía no hay respuestas.")
            continue
        if texto.isdigit():  # una de las preguntas sugeridas (decisión 86)
            if not 1 <= int(texto) <= len(propuestas):
                print(f"No hay una sugerencia {texto}." + (f" Elegí entre 1 y {len(propuestas)}, o escribí tu pregunta."
                                                            if propuestas else " Escribí tu pregunta."))
                continue
            texto = propuestas[int(texto) - 1]
            print(f"→ {texto}")
        caso = f"chat-t{len(conversacion.anteriores) + 1}"
        registro.CASO.set(caso)
        print("…", flush=True)
        inicio = time.monotonic()
        with open(log, "a") as archivo, contextlib.redirect_stdout(archivo):
            print(f"\n===== {caso}: {texto}")
            ultima = await conversacion.turno(texto)
        costo = costo_del_caso(caso)
        total += costo
        print(f"\n{ultima['texto']}\n")
        print(f"[{ultima['tipo'] or 'sin clasificar'} → {ultima['ruta']} · {len(ultima['consultas'])} consulta{'s' * (len(ultima['consultas']) != 1)} · "
              f"US$ {costo:.4f} · {time.monotonic() - inicio:.0f} s]  «?» para ver de dónde salió")
        propuestas = sugerencias(ultima)
        if propuestas:
            print("\n¿Seguimos? (escribí el número)\n" + "\n".join(f"  {i}. {x}" for i, x in enumerate(propuestas, 1)))
    print(f"\nConversación: {len(conversacion.anteriores)} preguntas · US$ {total:.4f} · detalle en {log}")


if __name__ == "__main__":
    argumentos = sys.argv[1:]
    if argumentos[:1] == ["--medir"]:
        sys.exit(asyncio.run(medir(argumentos[1:])))
    ruta_traza = None
    if argumentos[:1] == ["--traza"]:
        ruta_traza, argumentos = argumentos[1], argumentos[2:]
    if not argumentos:
        sys.exit(asyncio.run(chat()))
    respuestas = asyncio.run(atender(argumentos))
    for numero, respuesta in enumerate(respuestas, 1):
        print(f"\n===== {f'Turno {numero}: ' if len(respuestas) > 1 else ''}{respuesta['pregunta']}"
              f"  [{respuesta['tipo']} → {respuesta['ruta']}]")
        print(respuesta["texto"])
        if respuesta.get("problemas_registro"):
            print("⚠ registro no guardado: " + "; ".join(respuesta["problemas_registro"]))
    if ruta_traza:
        # Los turnos del coordinador entran con su texto y sus consultas; su recorrido completo, en la carpeta que nombran
        guardar_traza(respuestas, ruta_traza, "analista/puerta.py")
        print(f"\nTraza guardada en {ruta_traza}")
