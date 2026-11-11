"""Evaluador: corre el agente con las preguntas de esperados.yaml y compara sus consultas contra lo esperado.
Uso: .venv/bin/python evaluador.py                    (todas, una vez)
     .venv/bin/python evaluador.py P03 P05            (solo esas)
     .venv/bin/python evaluador.py --veces 5 P03      (cada una 5 veces: Haiku varía entre corridas)"""
import asyncio
import json
import sys

import yaml

from agente import responder

with open("Data/preguntas/esperados.yaml") as f:
    ESPERADOS = yaml.safe_load(f)
with open("Data/preguntas/preguntas.json") as f:
    PREGUNTAS = {p["id"]: p["texto"] for p in json.load(f)}


def cumple(chequeo, consulta):
    """¿Esta consulta del agente usó la medida esperada y dio el valor esperado?"""
    argumentos, resultado = consulta["argumentos"], consulta["resultado"]
    if argumentos["medida"] != chequeo["medida"]:
        return False
    if chequeo["tipo"] == "valor":
        return resultado.get("valor") is not None and abs(resultado["valor"] - chequeo["esperado"]) <= chequeo["tolerancia"] + 1e-9
    if chequeo["tipo"] == "variacion":
        return ("variacion" in resultado and resultado["comparables"] == chequeo["comparables"]
                and abs(resultado["variacion"] - chequeo["esperado"]) <= chequeo["tolerancia"] + 1e-9)
    if chequeo["tipo"] == "ranking":
        codigos = [fila.get(chequeo["dimension"]) for fila in resultado.get("filas", [])]
        return codigos[:len(chequeo["esperado"])] == chequeo["esperado"]
    raise ValueError(f"Tipo de chequeo desconocido: {chequeo['tipo']}")


def diagnostico(chequeo, consultas):
    """Para un chequeo que no pasó: ¿no usó la medida, o la usó y el número no dio?"""
    if not any(c["argumentos"]["medida"] == chequeo["medida"] for c in consultas):
        usadas = sorted({c["argumentos"]["medida"] for c in consultas}) or ["ninguna"]
        return f"no usó {chequeo['medida']} (usó: {', '.join(usadas)})"
    return f"usó {chequeo['medida']}, pero no dio {chequeo['esperado']}"


def main(ids, veces=1):
    aprobadas = 0
    for id_ in ids:
        print(f"\n===== {id_}: {PREGUNTAS[id_]}", flush=True)
        pasadas = 0
        for vez in range(1, veces + 1):
            respuesta = asyncio.run(responder(PREGUNTAS[id_]))
            fallos = [diagnostico(ch, respuesta["consultas"]) for ch in ESPERADOS[id_]
                      if not any(cumple(ch, c) for c in respuesta["consultas"])]
            pasadas += not fallos
            marca = "✓" if not fallos else "✗ " + " · ".join(fallos)
            print(marca if veces == 1 else f"  corrida {vez}: {marca}", flush=True)
        if veces > 1:
            print(f"{'✓' if pasadas == veces else '✗'} {id_}: {pasadas} de {veces}")
        aprobadas += pasadas == veces  # una pregunta aprueba solo si pasa todas las veces
    print(f"\nResultado: {aprobadas} de {len(ids)} pasan" + (f" (las {veces} veces)" if veces > 1 else ""))


if __name__ == "__main__":
    argumentos = sys.argv[1:]
    veces = 1
    if "--veces" in argumentos:
        i = argumentos.index("--veces")
        veces = int(argumentos[i + 1])
        del argumentos[i:i + 2]
    main(argumentos or list(ESPERADOS), veces)
