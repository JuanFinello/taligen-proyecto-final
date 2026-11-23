"""Test 6: consistencia (pass^k, como τ-bench). Los 21 casos del evaluador, cada uno N veces sin cambiar nada en el
medio. Un caso aprueba solo si acierta las N (una conversación, todos sus turnos). Se informa también la curva pass^k
para k = 1…N (estimador sin sesgo por caso: C(aciertos, k) / C(N, k)): la distancia entre pass^1 y pass^N es lo
inestable. Califica con evaluador.evaluar (misma medida, mismo valor, consulta reproducible y ruteo al agente).
Es una medición: si algo falla, se reporta, no se ajusta. La reserva (decisión 80) va aparte.

Uso: .venv/bin/python evaluacion/pruebas/consistencia.py [--veces N] [ids]      (N = 10 por defecto; ~US$ 0,30, de a 5)
Deja salidas/consistencia/resultado.md y lo copia a trazas/consistencia.md."""
import asyncio
import json
import sys
import time
from math import comb
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(RAIZ / "analista"), str(RAIZ / "evaluacion")]

import registro  # noqa: E402
from evaluador import CONVERSACIONES, ESPERADOS, PREGUNTAS, RESERVA, evaluar  # noqa: E402
from puerta import atender  # noqa: E402

CARPETA = Path("salidas/consistencia")
PARALELO = 5


async def correr(id_, vez, semaforo):
    async with semaforo:
        registro.CASO.set(f"{id_}-{vez}")
        respuestas = await atender(CONVERSACIONES.get(id_) or [PREGUNTAS[id_]])
        paso, lineas = evaluar(id_, respuestas)
        registro.anotar_evaluacion(id_, paso)
        print(f"· {id_} (corrida {vez}): {'✓' if paso else '✗'}", flush=True)
        return {"id": id_, "vez": vez, "paso": paso, "detalle": lineas,
                "respuestas": [r["texto"] for r in respuestas]}


def costo():
    return sum(l["costo_usd"] for l in registro.leer(registro.LLAMADAS) if l.get("corrida") == registro.CORRIDA)


def pass_k(aciertos, n, k):
    """Probabilidad de acertar k corridas seguidas, estimada sin sesgo con n corridas (τ-bench)."""
    return comb(aciertos, k) / comb(n, k)


def curva(grupo, aciertos, n):
    return [sum(pass_k(aciertos[i], n, k) for i in grupo) / len(grupo) for k in range(1, n + 1)]


async def main(ids, veces):
    CARPETA.mkdir(parents=True, exist_ok=True)
    semaforo = asyncio.Semaphore(PARALELO)
    inicio = time.monotonic()
    trabajos = [(i, v) for v in range(1, veces + 1) for i in ids]
    resultados = [await correr(*trabajos[0], semaforo)]  # el primero solo: escribe el caché del prefijo
    resultados += await asyncio.gather(*(correr(i, v, semaforo) for i, v in trabajos[1:]))
    reloj = time.monotonic() - inicio

    aciertos = {i: sum(r["paso"] for r in resultados if r["id"] == i) for i in ids}
    trabajo, reserva = [i for i in ids if i not in RESERVA], [i for i in ids if i in RESERVA]
    lineas = ["# Test 6: consistencia, pass^k (decisión 117)", "",
              f"Comando: `.venv/bin/python evaluacion/pruebas/consistencia.py --veces {veces}` · {len(ids)} casos × {veces} · "
              f"US$ {costo():.3f} · {reloj:.0f} s", ""]
    for nombre, grupo in [("De trabajo", trabajo), ("Reserva (no se ajusta nada por ellas)", reserva)]:
        if not grupo:
            continue
        c = curva(grupo, aciertos, veces)
        lineas += [f"**{nombre}: {sum(aciertos[i] == veces for i in grupo)} de {len(grupo)} aciertan las {veces} veces** · "
                   f"aciertos totales {sum(aciertos[i] for i in grupo)} de {len(grupo) * veces} "
                   f"(pass^1 = {c[0]:.0%}, pass^{veces} = {c[-1]:.0%})", ""]
    lineas += ["## Curva pass^k", "", "| k | " + " | ".join(str(k) for k in range(1, veces + 1)) + " |",
               "|---|" + "---|" * veces]
    for nombre, grupo in [("Trabajo", trabajo), ("Reserva", reserva)]:
        if grupo:
            lineas.append(f"| {nombre} | " + " | ".join(f"{x:.0%}" for x in curva(grupo, aciertos, veces)) + " |")
    lineas += ["", "## Por caso", "", "| Caso | Pregunta | Aciertos | Corridas |", "|---|---|---|---|"]
    for i in trabajo + reserva:
        rs = sorted((r for r in resultados if r["id"] == i), key=lambda r: r["vez"])
        texto = PREGUNTAS.get(i) or " → ".join(CONVERSACIONES[i])
        lineas.append(f"| {i}{' (reserva)' if i in RESERVA else ''} | {texto} | {aciertos[i]} de {veces} | "
                      + "".join("✓" if r["paso"] else "✗" for r in rs) + " |")
    malas = sorted((r for r in resultados if not r["paso"]), key=lambda r: (ids.index(r["id"]), r["vez"]))
    if malas:
        lineas += ["", "## Las que fallaron: por qué y qué respondió", ""]
        for r in malas:
            lineas += [f"**{r['id']}, corrida {r['vez']}**: " + " · ".join(r["detalle"]), ""]
            for n, t in enumerate(r["respuestas"], 1):
                prefijo = f"Turno {n}: " if len(r["respuestas"]) > 1 else ""
                lineas += ["> " + (prefijo + t).replace("\n", "\n> "), ""]
    texto = "\n".join(lineas) + "\n"
    (CARPETA / "resultado.md").write_text(texto)
    (CARPETA / "resultados.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2, default=str))
    Path("trazas/consistencia.md").write_text(texto)
    print(texto)


if __name__ == "__main__":
    args = sys.argv[1:]
    veces = 10
    if "--veces" in args:
        i = args.index("--veces")
        veces = int(args[i + 1])
        del args[i:i + 2]
    asyncio.run(main(args or list(ESPERADOS), veces))
