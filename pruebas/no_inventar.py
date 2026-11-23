"""Test 4: no inventar. Preguntas por cosas que la base no tiene: medidas que no existen, valores que no están en la
base y datos que no se registran (pronóstico, venta perdida, competencia). Ninguna repite P19 ni P20, que ya mide el
evaluador.

Pasa como el enunciado pide para P20 (chequeo «sin_dato» del evaluador): dice que no está y no responde con un número
de otra cosa (sin valor en el registro ni cifras de sus consultas en el texto). Antes de correr el agente, se verifica
con SQL escrito acá que de verdad no está, y se guarda.

Uso: .venv/bin/python pruebas/no_inventar.py [--veces N]      (~US$ 0,02 por vez)
Deja salidas/no_inventar/ (ausencias.json antes de correr, resultado.md) y copia el resultado a trazas/no_inventar.md."""
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import duckdb  # noqa: E402

import registro  # noqa: E402
from evaluador import falla, fallos, reproducible, ruteo  # noqa: E402
from procesador_capa_semantica import BASE  # noqa: E402
from puerta import atender  # noqa: E402

CARPETA = Path("salidas/no_inventar")
PARALELO = 5

# (id, grupo, pregunta, por qué no hay dato)
CASOS = [
    ("N01", "medida que no existe", "¿Cuántas personas compraron en Los Ceibos en marzo de 2026?", "no hay clientes ni tickets"),
    ("N02", "medida que no existe", "¿Cuál fue la ganancia neta del AF2026, después de sueldos y alquileres?", "solo hay margen bruto"),
    ("N03", "medida que no existe", "¿Cuánto vendimos por el canal online en el AF2026?", "no hay canal de venta"),
    ("N04", "medida que no existe", "¿Cuál fue la satisfacción de los clientes (NPS) en el AF2026?", "no hay encuestas"),
    ("N05", "no está en la base", "¿Cuánto vendió la sucursal S99 en el AF2026?", "hay S01 a S40"),
    ("N06", "no está en la base", "¿Cuánto vendimos en la región Este en el AF2026?", "regiones: Norte, Sur, Centro, Oeste"),
    ("N07", "no está en la base", "¿Cuál fue el margen de Electrónica en el AF2026?", "no existe esa categoría"),
    ("N08", "no está en la base", "¿Cuánto vendió la Coca-Cola 2,25 L en el AF2026?", "la marca no está (la parecida es Cola Andina)"),
    ("N09", "no está en la base", "¿Cuánto vendimos en el AF2030?", "la base va de mayo de 2024 a abril de 2026"),
    ("N10", "no se registra", "¿Cuánto vamos a vender en el AF2027?", "es un pronóstico"),
    ("N11", "no se registra", "¿Cuánto dejamos de vender por los faltantes en el AF2026?", "la venta que no se hizo no queda en la base"),
    ("N12", "no se registra", "¿Cuál es nuestra participación de mercado frente a la competencia?", "no hay datos de la competencia"),
]


def ausencias():
    """Lo que se puede verificar con SQL: que esas tablas, columnas y valores no están."""
    with duckdb.connect(BASE, read_only=True) as con:
        uno = lambda sql: con.execute(sql).fetchone()[0]
        columnas = {c for t, in con.execute("SHOW TABLES").fetchall() for c, *_ in con.execute(f"DESCRIBE {t}").fetchall()}
        tablas = {t for t, in con.execute("SHOW TABLES").fetchall()}
        return {
            "tablas": sorted(tablas),
            "sin clientes, tickets, canal, sueldos, encuestas ni competencia": not any(
                p in c for c in columnas | tablas for p in ("cliente", "ticket", "canal", "sueldo", "alquiler", "encuesta", "nps", "competencia", "mercado")),
            "S99 no existe": uno("SELECT count(*) FROM sucursales WHERE sucursal_id = 'S99'") == 0,
            "sucursales": [uno("SELECT min(sucursal_id) FROM sucursales"), uno("SELECT max(sucursal_id) FROM sucursales")],
            "región Este no existe": uno("SELECT count(*) FROM sucursales WHERE region ILIKE '%este%' AND region <> 'Oeste'") == 0,
            "categoría Electrónica no existe": uno("SELECT count(*) FROM productos WHERE categoria ILIKE '%electr%'") == 0,
            "Coca-Cola no existe": uno("SELECT count(*) FROM productos WHERE descripcion ILIKE '%coca%' OR marca ILIKE '%coca%'") == 0,
            "ventas desde/hasta": [str(uno("SELECT min(fecha) FROM ventas")), str(uno("SELECT max(fecha) FROM ventas"))],
            "AF2030 y AF2027 sin ventas": uno("SELECT count(*) FROM ventas v JOIN fechas f USING (fecha) WHERE f.anio_fiscal IN (2027, 2030)") == 0,
        }


def calificar(r):
    malos = fallos([{"tipo": "sin_dato"}], r["consultas"], r) + ruteo(r)
    if (motivo := reproducible(r)):
        malos.append("consulta: " + motivo)
    return not falla(malos), " · ".join(malos)


async def correr(caso, vez, semaforo):
    id_, grupo, texto, _ = caso
    async with semaforo:
        registro.CASO.set(f"{id_}-{vez}")
        r = (await atender([texto]))[0]
        paso, detalle = calificar(r)
        print(f"· {id_} ({vez}): {'✓' if paso else '✗'} {detalle}", flush=True)
        datos = r.get("registro")
        return {"id": id_, "grupo": grupo, "pregunta": texto, "vez": vez, "paso": paso, "detalle": detalle,
                "tipo": r.get("tipo"), "texto": r["texto"], "supuestos": list(datos.supuestos) if datos else []}


def costo():
    return sum(l["costo_usd"] for l in registro.leer(registro.LLAMADAS) if l.get("corrida") == registro.CORRIDA)


async def main(veces):
    CARPETA.mkdir(parents=True, exist_ok=True)
    a = ausencias()
    (CARPETA / "ausencias.json").write_text(json.dumps(
        {"verificado": datetime.now().isoformat(timespec="seconds"), **a}, ensure_ascii=False, indent=2))
    print("Ausencias verificadas con SQL antes de correr el agente:", json.dumps(a, ensure_ascii=False), flush=True)
    if not all(v for v in a.values() if isinstance(v, bool)):
        sys.exit("Algún dato que se suponía ausente está en la base: revisar los casos antes de correr.")
    semaforo = asyncio.Semaphore(PARALELO)
    inicio = time.monotonic()
    trabajos = [(c, v) for v in range(1, veces + 1) for c in CASOS]
    resultados = [await correr(*trabajos[0], semaforo)]  # la primera sola: deja la caché del prefijo armada
    resultados += await asyncio.gather(*(correr(c, v, semaforo) for c, v in trabajos[1:]))
    reloj = time.monotonic() - inicio

    si = lambda x: "✓" if x else "✗"
    lineas = ["# Test 4: no inventar", "",
              f"Comando: `.venv/bin/python pruebas/no_inventar.py{f' --veces {veces}' if veces > 1 else ''}` · {len(CASOS)} preguntas × "
              f"{veces} · US$ {costo():.3f} · {reloj:.0f} s", "",
              "Pasa si dice que no hay dato y no responde con un número de otra cosa (como P20 en el enunciado). La "
              "ausencia se verificó con SQL antes de correr (`salidas/no_inventar/ausencias.json`).", "",
              f"**{sum(r['paso'] for r in resultados)} de {len(resultados)}** pasan.", "",
              "| Caso | Grupo | Pregunta | Por qué no hay dato | Resultado |", "|---|---|---|---|---|"]
    for id_, grupo, texto, porque in CASOS:
        rs = [r for r in resultados if r["id"] == id_]
        res = f"{sum(r['paso'] for r in rs)}/{len(rs)}" + "".join(f" · {r['detalle']}" for r in rs if r["detalle"])
        lineas.append(f"| {id_} | {grupo} | {texto} | {porque} | {res} |")
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
    Path("trazas/no_inventar.md").write_text(texto)
    print(texto)


if __name__ == "__main__":
    args = sys.argv[1:]
    asyncio.run(main(int(args[args.index("--veces") + 1]) if "--veces" in args else 1))
