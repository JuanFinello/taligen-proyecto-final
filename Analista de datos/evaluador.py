"""Evaluador: corre el agente con las preguntas de esperados.yaml y compara sus consultas contra lo esperado.
Uso: .venv/bin/python evaluador.py            (todas)
     .venv/bin/python evaluador.py P03 P05    (solo esas)"""
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
        return "valor" in resultado and abs(resultado["valor"] - chequeo["esperado"]) <= chequeo["tolerancia"] + 1e-9
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


def main(ids):
    aprobadas = 0
    for id_ in ids:
        print(f"\n===== {id_}: {PREGUNTAS[id_]}", flush=True)
        respuesta = asyncio.run(responder(PREGUNTAS[id_]))
        fallos = [diagnostico(ch, respuesta["consultas"]) for ch in ESPERADOS[id_]
                  if not any(cumple(ch, c) for c in respuesta["consultas"])]
        if fallos:
            print("✗ " + " · ".join(fallos))
        else:
            aprobadas += 1
            print("✓")
    print(f"\nResultado: {aprobadas} de {len(ids)} pasan")


if __name__ == "__main__":
    main(sys.argv[1:] or list(ESPERADOS))
