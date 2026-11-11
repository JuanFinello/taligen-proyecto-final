"""Evaluador: corre el agente con las preguntas y conversaciones de esperados.yaml y compara sus consultas contra lo esperado.
Uso: .venv/bin/python evaluador.py                    (todas, una vez)
     .venv/bin/python evaluador.py P03 P05 C1         (solo esas; C1–C5 son conversaciones, se evalúa cada turno)
     .venv/bin/python evaluador.py --veces 5 P03      (cada una 5 veces: Haiku varía entre corridas)"""
import asyncio
import json
import sys

import yaml

from agente import conversar, responder

with open("Data/preguntas/esperados.yaml") as f:
    ESPERADOS = yaml.safe_load(f)
with open("Data/preguntas/preguntas.json") as f:
    PREGUNTAS = {p["id"]: p["texto"] for p in json.load(f)}
with open("Data/preguntas/conversaciones.json") as f:
    CONVERSACIONES = {c["id"]: c["turnos"] for c in json.load(f)}


def cumple(chequeo, consulta):
    """¿Esta consulta del agente usó la medida esperada y dio el valor esperado?"""
    argumentos, resultado = consulta["argumentos"], consulta["resultado"]
    if argumentos.get("medida") != chequeo["medida"]:  # una consulta SQL no tiene medida: no cumple
        return False
    cerca = lambda v: v is not None and abs(v - chequeo["esperado"]) <= chequeo["tolerancia"] + 1e-9
    # Con `fila` (por ejemplo {categoria: Almacén}), también vale esa fila de una consulta agrupada: Haiku a veces
    # agrupa en vez de filtrar y lee la fila que corresponde. Solo esa fila, no cualquiera (decisión 37)
    filas = [f for f in resultado.get("filas", []) if chequeo.get("fila")
             and all(f.get(dimension) == valor for dimension, valor in chequeo["fila"].items())]
    if chequeo["tipo"] == "valor":  # también vale el de un período de una comparación, o el total de una agrupación
        periodos = [resultado[k] for k in ("actual", "anterior") if isinstance(resultado.get(k), dict)]
        if any(cerca(f.get(k)) for f in filas for k in ("valor", "actual", "anterior")):
            return True
        return any(cerca(r.get("valor")) for r in [resultado, *periodos]) or cerca(resultado.get("total"))
    if chequeo["tipo"] == "variacion":
        if resultado.get("comparables") == chequeo["comparables"] and any(cerca(f.get("variacion")) for f in filas):
            return True
        return ("variacion" in resultado and resultado["comparables"] == chequeo["comparables"]
                and abs(resultado["variacion"] - chequeo["esperado"]) <= chequeo["tolerancia"] + 1e-9)
    if chequeo["tipo"] == "ranking":
        codigos = [fila.get(chequeo["dimension"]) for fila in resultado.get("filas", [])]
        return codigos[:len(chequeo["esperado"])] == chequeo["esperado"]
    if chequeo["tipo"] == "grupo":  # agrupó por esa dimensión y la fila de ese código tiene esa variación
        if chequeo["dimension"] not in (argumentos.get("agrupar_por") or []):
            return False
        return any(fila.get(chequeo["dimension"]) == chequeo["codigo"] and cerca(fila.get("variacion"))
                   for fila in resultado.get("filas", []))
    raise ValueError(f"Tipo de chequeo desconocido: {chequeo['tipo']}")


def diagnostico(chequeo, consultas):
    """Para un chequeo que no pasó: ¿no usó la medida, o la usó y el número no dio?"""
    if not any(c["argumentos"].get("medida") == chequeo["medida"] for c in consultas):
        usadas = sorted({c["argumentos"].get("medida", "sql") for c in consultas}) or ["ninguna"]
        return f"no usó {chequeo['medida']} (usó: {', '.join(usadas)})"
    return f"usó {chequeo['medida']}, pero no dio {chequeo['esperado']}"


def fallos(chequeos, consultas):
    malos = []
    for chequeo in chequeos:
        if chequeo["tipo"] == "ninguna_consulta":  # pregunta sin dato en la base: no tiene que consultar nada
            if consultas:
                malos.append(f"consultó igual ({', '.join(c['argumentos'].get('medida', 'sql') for c in consultas)})")
        elif not any(cumple(chequeo, c) for c in consultas):
            malos.append(diagnostico(chequeo, consultas))
    return malos


def correr(id_):
    """Una corrida de una pregunta o de una conversación: devuelve (pasó, líneas para mostrar)."""
    if id_ not in CONVERSACIONES:
        malos = fallos(ESPERADOS[id_], asyncio.run(responder(PREGUNTAS[id_]))["consultas"])
        return not malos, ["✓" if not malos else "✗ " + " · ".join(malos)]
    # Conversación: se evalúa turno por turno, así se ve si heredó lo anterior (decisión 32)
    respuestas = asyncio.run(conversar(CONVERSACIONES[id_]))
    paso, lineas, hasta_ahora = True, [], []
    for numero, (respuesta, chequeos) in enumerate(zip(respuestas, ESPERADOS[id_]["turnos"]), 1):
        # Valen sus consultas y las de turnos anteriores (puede reusar un número ya consultado); como el valor
        # esperado depende de los filtros, un turno que pierde un filtro igual falla
        hasta_ahora += respuesta["consultas"]
        if not chequeos:
            lineas.append(f"turno {numero}: – sin chequeo numérico")
            continue
        malos = fallos(chequeos, hasta_ahora)
        paso = paso and not malos
        lineas.append(f"turno {numero}: " + ("✓" if not malos else "✗ " + " · ".join(malos)))
    return paso, lineas


def main(ids, veces=1):
    aprobadas = 0
    for id_ in ids:
        print(f"\n===== {id_}: {PREGUNTAS.get(id_) or ' → '.join(CONVERSACIONES[id_])}", flush=True)
        pasadas = 0
        for vez in range(1, veces + 1):
            paso, lineas = correr(id_)
            pasadas += paso
            for linea in lineas:
                print(linea if veces == 1 else f"  corrida {vez}: {linea}", flush=True)
        if veces > 1:
            print(f"{'✓' if pasadas == veces else '✗'} {id_}: {pasadas} de {veces}")
        aprobadas += pasadas == veces  # aprueba solo si pasa todas las veces (una conversación: todos sus turnos)
    print(f"\nResultado: {aprobadas} de {len(ids)} pasan" + (f" (las {veces} veces)" if veces > 1 else ""))


if __name__ == "__main__":
    argumentos = sys.argv[1:]
    veces = 1
    if "--veces" in argumentos:
        i = argumentos.index("--veces")
        veces = int(argumentos[i + 1])
        del argumentos[i:i + 2]
    main(argumentos or list(ESPERADOS), veces)
