"""Test 3 (decisión 96): fechas difíciles. ¿El agente entiende *cuándo*? El año fiscal empieza en mayo, la base termina
el 30-04-2026 y hoy es noviembre de 2026 (glosario: «el último mes» se cuenta desde el último dato, no desde hoy).

Cuatro grupos: relativas a hoy, el borde fiscal, ambiguas (calendario o fiscal, o sin año) y fuera de la base. Los
valores esperados salen de SQL escrito acá, sin el procesador, y se guardan antes de correr el agente. Se califica con el
código del evaluador: valor (misma medida y número), lecturas (las dos, o una declarada en supuestos, decisión 76),
sin_dato (no responde con otro número), y «valor_o_sin_dato» para las que admiten dos respuestas honestas (contar desde
el último dato, o decir que no hay datos para esa fecha).

Uso: .venv/bin/python evaluacion/pruebas/fechas.py [--veces N]      (~US$ 0,05 por vez)
Deja salidas/fechas/ (esperados.json antes de correr, resultado.md) y copia el resultado a trazas/fechas.md."""
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(RAIZ / "analista"), str(RAIZ / "evaluacion")]

import duckdb  # noqa: E402

import registro  # noqa: E402
from evaluador import falla, fallos, reproducible, ruteo  # noqa: E402
from procesador_capa_semantica import BASE  # noqa: E402
from puerta import atender  # noqa: E402

CARPETA = Path("salidas/fechas")
PARALELO = 5

# (id, grupo, pregunta, cómo se califica, períodos de ventas netas: (desde, hasta) o lista de lecturas)
CASOS = [
    ("F01", "relativa", "¿Cuánto vendimos el último mes?", "valor", ("2026-04-01", "2026-04-30")),
    ("F02", "relativa", "¿Cuánto vendimos el mes pasado?", "valor_o_sin_dato", ("2026-04-01", "2026-04-30")),
    ("F03", "relativa", "¿Cuánto llevamos vendido en este año fiscal?", "valor_o_sin_dato", ("2025-05-01", "2026-04-30")),
    ("F04", "borde fiscal", "¿Cuánto vendimos en el primer mes del AF2026?", "valor", ("2025-05-01", "2025-05-31")),
    ("F05", "borde fiscal", "¿Cuánto vendimos en el AF2026 hasta octubre inclusive?", "valor", ("2025-05-01", "2025-10-31")),
    ("F06", "borde fiscal", "¿Cuánto vendimos en el último mes del AF2025?", "valor", ("2025-04-01", "2025-04-30")),
    ("F07", "ambigua", "¿Cuánto vendimos el año pasado?", "lecturas", [("2025-01-01", "2025-12-31"), ("2024-05-01", "2025-04-30")]),
    ("F08", "ambigua", "¿Cuánto vendimos en abril?", "lecturas", [("2026-04-01", "2026-04-30"), ("2025-04-01", "2025-04-30")]),
    ("F09", "ambigua", "¿Cuánto vendimos en el T2 de 2025?", "lecturas",
     [("2025-04-01", "2025-06-30"), ("2025-08-01", "2025-10-31"), ("2024-08-01", "2024-10-31")]),
    ("F10", "rango", "¿Cuánto vendimos en la primera quincena de marzo de 2026?", "valor", ("2026-03-01", "2026-03-15")),
    ("F11", "rango", "¿Cuánto vendimos entre el 10 y el 20 de enero de 2026?", "valor", ("2026-01-10", "2026-01-20")),
    ("F12", "fuera de la base", "¿Cuánto vendimos ayer?", "valor_o_sin_dato", ("2026-04-30", "2026-04-30")),
    ("F13", "fuera de la base", "¿Cuánto vendimos en el AF2027?", "sin_dato", None),
    ("F14", "fuera de la base", "¿Cuánto vendimos en marzo de 2024?", "sin_dato", None),
]
QUE_PASA = {"valor": "da ese número", "lecturas": "da las lecturas o declara la elegida",
            "sin_dato": "dice que no hay datos, sin otro número",
            "valor_o_sin_dato": "cuenta desde el último dato y lo dice, o dice que no hay datos"}


def esperados():
    with duckdb.connect(BASE, read_only=True) as con:
        neto = lambda desde, hasta: round(con.execute(
            "SELECT SUM(importe_neto) FROM ventas WHERE fecha BETWEEN ? AND ?", [desde, hasta]).fetchone()[0], 2)
        salida = {}
        for id_, _, _, forma, periodos in CASOS:
            if forma == "lecturas":
                salida[id_] = [neto(*p) for p in periodos]
            elif periodos:
                salida[id_] = neto(*periodos)
        return salida


def chequeos(forma, esperado):
    valor = [{"medida": "ventas_netas", "tipo": "valor", "esperado": esperado, "tolerancia": 0.5}]
    if forma == "valor":
        return [valor]
    if forma == "lecturas":
        return [[{"medida": "ventas_netas", "tipo": "lecturas", "esperados": esperado, "tolerancia": 0.5}]]
    if forma == "sin_dato":
        return [[{"tipo": "sin_dato"}]]
    return [valor, [{"tipo": "sin_dato"}]]  # valor_o_sin_dato: alcanza con una de las dos


def calificar(forma, esperado, r):
    """(pasó, detalle). Con dos formas válidas, pasa si cumple alguna."""
    intentos = []
    for lista in chequeos(forma, esperado):
        malos = fallos(lista, r["consultas"], r) + ruteo(r)
        if (motivo := reproducible(r)):
            malos.append("consulta: " + motivo)
        if not falla(malos):
            return True, ("sin dato" if lista[0]["tipo"] == "sin_dato" and forma != "sin_dato" else "")
        intentos.append(" · ".join(malos))
    return False, " | ".join(intentos)


async def correr(caso, vez, e, semaforo):
    id_, grupo, texto, forma, _ = caso
    async with semaforo:
        registro.CASO.set(f"{id_}-{vez}")
        r = (await atender([texto]))[0]
        paso, detalle = calificar(forma, e.get(id_), r)
        print(f"· {id_} ({vez}): {'✓' if paso else '✗'} {detalle}", flush=True)
        datos = r.get("registro")
        return {"id": id_, "grupo": grupo, "pregunta": texto, "forma": forma, "vez": vez, "paso": paso, "detalle": detalle,
                "tipo": r.get("tipo"), "texto": r["texto"], "supuestos": list(datos.supuestos) if datos else []}


def costo():
    return sum(l["costo_usd"] for l in registro.leer(registro.LLAMADAS) if l.get("corrida") == registro.CORRIDA)


async def main(veces):
    CARPETA.mkdir(parents=True, exist_ok=True)
    e = esperados()
    (CARPETA / "esperados.json").write_text(json.dumps({"calculados": datetime.now().isoformat(timespec="seconds"), **e}, indent=2))
    print("Esperados guardados antes de correr el agente:", CARPETA / "esperados.json", flush=True)
    semaforo = asyncio.Semaphore(PARALELO)
    inicio = time.monotonic()
    trabajos = [(c, v) for v in range(1, veces + 1) for c in CASOS]
    resultados = [await correr(*trabajos[0], e, semaforo)]
    resultados += await asyncio.gather(*(correr(c, v, e, semaforo) for c, v in trabajos[1:]))
    reloj = time.monotonic() - inicio

    si = lambda x: "✓" if x else "✗"
    miles = lambda x: f"$ {x:,.0f}".replace(",", ".")
    lineas = ["# Test 3: fechas difíciles (decisión 96)", "",
              f"Comando: `.venv/bin/python evaluacion/pruebas/fechas.py{f' --veces {veces}' if veces > 1 else ''}` · {len(CASOS)} preguntas × "
              f"{veces} · US$ {costo():.3f} · {reloj:.0f} s · base hasta el 30-04-2026, hoy noviembre de 2026", "",
              f"**{sum(r['paso'] for r in resultados)} de {len(resultados)}** pasan.", "",
              "| Caso | Grupo | Pregunta | Pasa si… | Esperado (SQL a mano) | Resultado |", "|---|---|---|---|---|---|"]
    for id_, grupo, texto, forma, _ in CASOS:
        rs = [r for r in resultados if r["id"] == id_]
        esp = e.get(id_)
        esp = " o ".join(miles(x) for x in esp) if isinstance(esp, list) else (miles(esp) if esp else "—")
        res = f"{sum(r['paso'] for r in rs)}/{len(rs)}" + "".join(f" · {r['detalle']}" for r in rs if r["detalle"] and r["paso"])
        lineas.append(f"| {id_} | {grupo} | {texto} | {QUE_PASA[forma]} | {esp} | {res} |")
    lineas += ["", "## Por grupo", "", "| Grupo | Pasan |", "|---|---|"]
    for grupo in dict.fromkeys(c[1] for c in CASOS):
        rs = [r for r in resultados if r["grupo"] == grupo]
        lineas.append(f"| {grupo} | {sum(r['paso'] for r in rs)} de {len(rs)} |")
    lineas += ["", "## Respuestas (primera corrida, y todas las que fallaron)", ""]
    for r in resultados:
        if r["vez"] == 1 or not r["paso"]:
            lineas += [f"**{r['id']} ({r['vez']}) {si(r['paso'])}** {r['pregunta']}" + (f" — {r['detalle']}" if r["detalle"] else ""), "",
                       "> " + r["texto"].replace("\n", "\n> ")]
            if r["supuestos"]:
                lineas.append("> *Supuestos:* " + " · ".join(r["supuestos"]))
            lineas.append("")
    texto = "\n".join(lineas) + "\n"
    (CARPETA / "resultado.md").write_text(texto)
    (CARPETA / "resultados.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2))
    Path("trazas/fechas.md").write_text(texto)
    print(texto)


if __name__ == "__main__":
    args = sys.argv[1:]
    asyncio.run(main(int(args[args.index("--veces") + 1]) if "--veces" in args else 1))
