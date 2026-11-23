"""Califica con código los informes que se miden (I1, I2, I3): ¿dicen lo que tienen que decir? Hasta ahora se leían
(decisión 110). Lee lo esperado de Data/preguntas/esperados_informes.yaml y el texto de cada informe.json; no llama al
modelo. Sirve para comparar versiones del diseño: agrupa las corridas por la huella que anota correr_todo.py.

Uso: .venv/bin/python chequeos_informes.py [--guardar] salidas/completa-A …   (sin carpetas: las versiones registradas)
Con --guardar escribe la tabla en trazas/comparacion_informes.md (el registro de todas las comparaciones)."""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

from controles import numeros_del_texto

with open("Data/preguntas/esperados_informes.yaml") as f:
    ESPERADOS = yaml.safe_load(f)
with open("Data/preguntas/versiones_informes.yaml") as f:
    VERSIONES = yaml.safe_load(f)  # huella → qué es


def cumple(chequeo, redaccion):
    """¿El informe cumple el chequeo? Mira el título solo o el título, la bajada y las razones."""
    titulo = redaccion["titulo"]
    puntos = [p if isinstance(p, str) else p["texto"] for p in redaccion.get("puntos", [])]  # antes de la 104, texto solo
    texto = " ".join([titulo, redaccion.get("bajada", ""), *puntos])
    tipo = chequeo["tipo"]
    if tipo == "texto":
        return bool(re.search(chequeo["patron"], texto, re.I))
    if tipo == "titulo":
        return bool(re.search(chequeo["patron"], titulo, re.I))
    if tipo == "titulo_sin":
        return not re.search(chequeo["patron"], titulo, re.I)
    if tipo == "cifra":
        escritos = [abs(valor) for valor, _, _ in numeros_del_texto(re.sub(r"\[C\d+\]", "", texto))]
        return any(abs(e - v) <= chequeo["tolerancia"] for e in escritos for v in chequeo["valores"])
    raise ValueError(f"tipo de chequeo desconocido: {tipo}")


def calificar(id_, redaccion):
    """[(nombre del chequeo, cumple)] de un informe."""
    return [(c["nombre"], cumple(c, redaccion)) for c in ESPERADOS[id_] + ESPERADOS["TODOS"]]


def version_de(corrida):
    resumen = corrida / "resumen.md"  # una corrida cortada no lo llega a escribir
    hallada = re.search(r"Versión del diseño `(\w+)`", resumen.read_text()) if resumen.exists() else None
    return hallada.group(1) if hallada else "?"


def main(carpetas, guardar=False, solo_registradas=False):
    # versión → caso → chequeo → [cumple en cada corrida]
    notas = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    corridas = defaultdict(list)
    for corrida in map(Path, carpetas):
        casos = [i for i in ("I1", "I2", "I3") if (corrida / i / "informe.json").exists()]
        if not casos:  # la corrida se cortó (por ejemplo, sin crédito) o no incluía informes: no cuenta
            continue
        version = version_de(corrida)
        corridas[version].append(corrida.name)
        for id_ in casos:
            for nombre, ok in calificar(id_, json.loads((corrida / id_ / "informe.json").read_text())["redaccion"]):
                notas[version][id_][nombre].append(ok)
    # en el orden del registro; las que no están, al final
    versiones = [v for v in VERSIONES if v in notas] + ([] if solo_registradas else [v for v in notas if v not in VERSIONES])
    nombre = lambda v: VERSIONES.get(v, {}).get("nombre", v)
    lineas = ["| Caso | Chequeo | " + " | ".join(nombre(v) for v in versiones) + " |",
              "|---|---|" + "---|" * len(versiones)]
    totales = {v: [0, 0] for v in versiones}
    for id_ in ("I1", "I2", "I3"):
        for chequeo in [c["nombre"] for c in ESPERADOS[id_] + ESPERADOS["TODOS"]]:
            celdas = []
            for v in versiones:
                veces = notas[v][id_].get(chequeo, [])
                celdas.append(f"{sum(veces)} de {len(veces)}")
                totales[v][0] += sum(veces)
                totales[v][1] += len(veces)
            lineas.append(f"| {id_} | {chequeo} | " + " | ".join(celdas) + " |")
    lineas.append("| | **Total** | " + " | ".join(f"**{a} de {b}** ({100 * a / b:.0f} %)" for a, b in totales.values()) + " |")
    detalle = ["| Versión | Huella | Decisión | Corridas | Qué es |", "|---|---|---|---|---|"] + [
        f"| {nombre(v)} | `{v}` | {VERSIONES.get(v, {}).get('decision', '–')} | {len(corridas[v])} | "
        f"{VERSIONES.get(v, {}).get('detalle', '')} |" for v in versiones]
    tabla = "\n".join(detalle + [""] + lineas)
    print(tabla)
    if guardar:
        texto = ("# Comparación de versiones del diseño en los informes medidos (I1, I2, I3)\n\n"
                 "Lo arma `chequeos_informes.py --guardar` (decisión 110) con los chequeos de "
                 "`Data/preguntas/esperados_informes.yaml`: cada celda dice en cuántas corridas el informe cumplió. "
                 "Sin modelo: lee los `informe.json` de `salidas/completa-*`. Las corridas cortadas no cuentan.\n\n"
                 + tabla + "\n\nCorridas usadas:\n\n"
                 + "\n".join(f"- {nombre(v)}: " + ", ".join(sorted(corridas[v])) for v in versiones) + "\n")
        Path("trazas/comparacion_informes.md").write_text(texto)
        print("\nGuardado en trazas/comparacion_informes.md")


if __name__ == "__main__":
    argumentos = sys.argv[1:]
    guardar = "--guardar" in argumentos
    carpetas = [a for a in argumentos if a != "--guardar"]
    # Sin carpetas: todas las corridas, pero solo las versiones del registro (las demás son pruebas de otros días)
    main(carpetas or sorted(map(str, Path(".").glob("salidas/completa-*"))), guardar, solo_registradas=not carpetas)
