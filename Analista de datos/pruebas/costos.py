"""Test 9 (decisión 100): costo y tiempo como distribución, no como total. Lee registros/llamadas.jsonl (cada llamada al
modelo, decisión 45) y agrupa por caso (una pregunta, un turno, un informe en una corrida). Para cada tipo de pregunta:
mediana, p95 y máximo del costo y del tiempo, y cuánto del prompt sale del caché. No llama al modelo.

El tipo de cada caso sale de su id: las preguntas y los informes, de TIPOS en esperados.yaml; las variantes del test 2,
del de su original; las fechas del test 3, del declarado en pruebas/matriz_puerta.py; las conversaciones, aparte.
El tiempo es el de reloj del caso: del comienzo de su primera llamada al final de la última (los analistas de un
informe corren en paralelo, así que sumar sus tiempos lo exageraría).

Uso: .venv/bin/python pruebas/costos.py [desde AAAA-MM-DD]      (por defecto, desde el 2026-11-18: el diseño actual)
Deja salidas/costos/resultado.md y lo copia a trazas/costos.md."""
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml  # noqa: E402

import registro  # noqa: E402
from matriz_puerta import DECLARADOS  # noqa: E402

CARPETA = Path("salidas/costos")
ORDEN = ["puntual", "comparativa", "ranking", "ambigua", "sin_dato", "conversación (turno)", "diagnostico", "informe"]


def tipo_de(caso, tipos, fechas):
    """El tipo de un caso por su id («P07», «P07-sinonimos-2», «F08-1», «C2», «I1»…), o None si no es de una pregunta."""
    if not caso:
        return None
    base = caso.split("-")[0].split(" ")[0]
    if base in fechas:
        return fechas[base]
    if re.fullmatch(r"C\d+", base):
        return "conversación (turno)"
    t = tipos.get(base)
    return t if isinstance(t, str) and t != "agente" else None


def percentil(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, round(p / 100 * (len(xs) - 1)))]


def main(desde):
    CARPETA.mkdir(parents=True, exist_ok=True)
    with open("Data/preguntas/esperados.yaml") as f:
        tipos = yaml.safe_load(f)["TIPOS"]
    fechas = {i.split(" ")[1]: t for i, _, t in DECLARADOS if i.startswith("fechas")}
    casos = defaultdict(list)
    llamadas = [l for l in registro.leer(registro.LLAMADAS) if l["fecha"] >= desde]
    for l in llamadas:
        casos[(l["corrida"], l.get("caso"))].append(l)

    por_tipo = defaultdict(list)
    for (corrida, caso), ls in casos.items():
        tipo = tipo_de(caso, tipos, fechas)
        if not tipo or not any(l["agente"] in ("analista", "coordinador") for l in ls):
            continue  # solo clasificaciones (el test 8) o casos sin tipo (ataques, simulaciones)
        fin = max(datetime.fromisoformat(l["fecha"]) for l in ls)
        primera = min(ls, key=lambda l: l["fecha"])
        inicio = datetime.fromisoformat(primera["fecha"]) - timedelta(seconds=primera["segundos_modelo"] + primera["segundos_tools"])
        if re.fullmatch(r"C\d+", (caso or "").split("-")[0]):
            n_turnos = sum(1 for l in ls if l["agente"] == "clasificador")
            por_tipo[tipo].append({"costo": sum(l["costo_usd"] for l in ls) / max(n_turnos, 1),
                                   "segundos": (fin - inicio).total_seconds() / max(n_turnos, 1), "llamadas": len(ls) / max(n_turnos, 1)})
        else:
            por_tipo[tipo].append({"costo": sum(l["costo_usd"] for l in ls), "segundos": (fin - inicio).total_seconds(), "llamadas": len(ls)})

    dinero = lambda x: (f"US$ {x:.4f}" if x < 1 else f"US$ {x:.2f}").replace(".", ",")
    miles = lambda n: f"{n:,}".replace(",", ".")
    seg = lambda x: f"{x:.0f} s"
    lineas = ["# Test 9: costo y tiempo por tipo de pregunta (decisión 100)", "",
              f"Comando: `.venv/bin/python pruebas/costos.py {desde}` · {miles(len(llamadas))} llamadas al modelo desde el {desde}, "
              f"agrupadas en {miles(sum(len(v) for v in por_tipo.values()))} casos con tipo · sin modelo", "",
              "| Tipo | Casos | Costo mediano | p95 | Máximo | Tiempo mediano | p95 | Máximo | Llamadas (mediana) |",
              "|---|---|---|---|---|---|---|---|---|"]
    for t in ORDEN:
        xs = por_tipo.get(t)
        if not xs:
            continue
        c, s = [x["costo"] for x in xs], [x["segundos"] for x in xs]
        lineas.append(f"| {t} | {len(xs)} | {dinero(statistics.median(c))} | {dinero(percentil(c, 95))} | {dinero(max(c))} | "
                      f"{seg(statistics.median(s))} | {seg(percentil(s, 95))} | {seg(max(s))} | {statistics.median(x['llamadas'] for x in xs):.0f} |")
    # El caché (decisión 72): de los tokens de entrada, cuántos se leyeron del caché
    lineas += ["", "## El caché del prefijo (decisión 72)", "", "| Quién | Llamadas | Tokens de entrada leídos del caché | Costo |", "|---|---|---|---|"]
    for agente in ("clasificador", "analista", "coordinador"):
        ls = [l for l in llamadas if l["agente"] == agente]
        entrada = sum(l["tokens_entrada"] + l["cache_escrito"] + l["cache_leido"] for l in ls)
        leido = sum(l["cache_leido"] for l in ls)
        porcentaje = f"{leido / entrada * 100:.1f} %".replace(".", ",")
        lineas.append(f"| {agente} | {miles(len(ls))} | {porcentaje} | {dinero(sum(l['costo_usd'] for l in ls))} |")
    # Una proyección simple, con las medianas: 50 preguntas por día hábil y los informes programados
    med = {t: statistics.median(x["costo"] for x in xs) for t, xs in por_tipo.items()}
    preguntas = statistics.median([med[t] for t in ("puntual", "comparativa", "ranking") if t in med])
    lineas += ["", "## Qué costaría usarlo", "",
               f"- Una pregunta típica (mediana de puntual, comparativa y ranking): **{dinero(preguntas)}**.",
               f"- 50 preguntas por día hábil, un año (250 días): **{dinero(preguntas * 50 * 250)}**.",
               f"- Un diagnóstico: {dinero(med.get('diagnostico', 0))}; un informe: {dinero(med.get('informe', 0))}.",
               "- Los informes programados de un año (52 semanales, 12 mensuales, 4 trimestrales y 1 anual, decisión 65): "
               f"**{dinero(med.get('informe', 0) * 69)}** con la mediana de un informe."]
    texto = "\n".join(lineas) + "\n"
    (CARPETA / "resultado.md").write_text(texto)
    Path("trazas/costos.md").write_text(texto)
    print(texto)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "2026-11-18")
