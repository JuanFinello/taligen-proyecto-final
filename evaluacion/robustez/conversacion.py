"""Test 7 (decisión 118): conversación. ¿El agente arrastra bien lo que tiene que arrastrar y suelta lo que no? Ocho
conversaciones nuevas de 3 turnos, en seis grupos: reemplazar un filtro («¿y Limpieza?» después de Perfumería), sumar
uno («¿y solo el Norte?»), quitar uno («¿y en toda la cadena?»), referirse a la respuesta anterior («esa sucursal»),
corregir («perdón, quise decir…») y cambiar de tema, con aviso y sin aviso. Un turno que arrastra un filtro viejo, o
que pierde uno que tenía que heredar, da otro número y falla.

Los valores esperados salen de SQL escrito acá, sin el procesador, y se guardan antes de correr el agente. Se califica
con el código del evaluador, turno por turno: misma medida y mismo valor (o ranking), consulta reproducible y que la
puerta lo mande al agente. A diferencia del evaluador, cada turno se califica solo con sus propias consultas: si
reusa un número de un turno anterior, tiene que ser el que corresponde a este turno. Es una medición: lo que falla se
reporta, no se ajusta.

Uso: .venv/bin/python evaluacion/robustez/conversacion.py [--veces N] [ids]      (~US$ 0,03 por vez)
Deja salidas/conversacion/ (esperados.json antes de correr, resultado.md) y copia el resultado a trazas/conversacion.md."""
import asyncio
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(RAIZ / "analista"), str(RAIZ / "evaluacion")]

import duckdb  # noqa: E402

import registro  # noqa: E402
from evaluador import falla, fallos, reproducible, ruteo  # noqa: E402
from procesador_capa_semantica import BASE  # noqa: E402
from puerta import atender  # noqa: E402

CARPETA = Path("salidas/conversacion")
PARALELO = 5
AF2025, AF2026 = ("2024-05-01", "2025-04-30"), ("2025-05-01", "2026-04-30")
T3_AF2026 = ("2025-11-01", "2026-01-31")
MES = lambda a, m, fin: (f"{a}-{m:02d}-01", f"{a}-{m:02d}-{fin}")

# Cada turno: (texto, medida, filtros) · filtros: categoria, subcategoria, region, sucursal, periodo (desde, hasta)
# Medida «ranking_sucursal_N»: las N sucursales que más vendieron (ventas netas) en el período.
CONVERSACIONES = [
    ("V1", "reemplazar", [
        ("¿Cuánto vendió Perfumería en el AF2026?", "ventas_netas", {"categoria": "Perfumería", "periodo": AF2026}),
        ("¿Y Bebidas?", "ventas_netas", {"categoria": "Bebidas", "periodo": AF2026}),
        ("¿Y en unidades?", "unidades", {"categoria": "Bebidas", "periodo": AF2026})]),
    ("V2", "sumar", [
        ("¿Cuánto vendió Bebidas en el AF2025?", "ventas_netas", {"categoria": "Bebidas", "periodo": AF2025}),
        ("¿Y solo en la región Norte?", "ventas_netas", {"categoria": "Bebidas", "region": "Norte", "periodo": AF2025}),
        ("¿Y de eso, solo Gaseosas?", "ventas_netas",
         {"categoria": "Bebidas", "subcategoria": "Gaseosas", "region": "Norte", "periodo": AF2025})]),
    ("V3", "quitar", [
        ("¿Cuánto vendió Lácteos en la región Sur en abril de 2026?", "ventas_netas",
         {"categoria": "Lácteos", "region": "Sur", "periodo": MES(2026, 4, 30)}),
        ("¿Y en todas las regiones?", "ventas_netas", {"categoria": "Lácteos", "periodo": MES(2026, 4, 30)}),
        ("¿Y sumando todas las categorías?", "ventas_netas", {"periodo": MES(2026, 4, 30)})]),
    ("V4", "referencia", [
        ("¿Qué sucursal vendió más en el AF2026?", "ranking_sucursal_1", {"periodo": AF2026}),
        ("¿Y cuánto vendió esa sucursal en el AF2025?", "ventas_netas", {"sucursal": "S02", "periodo": AF2025}),
        ("¿Qué margen tuvo en el AF2026?", "margen_pct", {"sucursal": "S02", "periodo": AF2026})]),
    ("V5", "referencia", [
        ("¿Cuánto vendió Almacén en marzo de 2026?", "ventas_netas", {"categoria": "Almacén", "periodo": MES(2026, 3, 31)}),
        ("¿Y en el mes anterior?", "ventas_netas", {"categoria": "Almacén", "periodo": MES(2026, 2, 28)}),
        ("¿Y un año antes?", "ventas_netas", {"categoria": "Almacén", "periodo": MES(2025, 2, 28)})]),
    ("V6", "corregir", [
        ("¿Cuántas unidades vendió la región Centro en enero de 2026?", "unidades",
         {"region": "Centro", "periodo": MES(2026, 1, 31)}),
        ("Perdón, quise decir la región Sur.", "unidades", {"region": "Sur", "periodo": MES(2026, 1, 31)}),
        ("¿Y en pesos?", "ventas_netas", {"region": "Sur", "periodo": MES(2026, 1, 31)})]),
    ("V7", "cambio de tema con aviso", [
        ("¿Qué margen tuvo Frescos en la región Centro en el AF2025?", "margen_pct",
         {"categoria": "Frescos", "region": "Centro", "periodo": AF2025}),
        ("Otra cosa: ¿cuántas sucursales tiene la región Sur?", "sucursales_abiertas", {"region": "Sur"}),
        ("¿Cuánto vendió la cadena en diciembre de 2025?", "ventas_netas", {"periodo": MES(2025, 12, 31)})]),
    ("V8", "cambio de tema sin aviso", [
        ("¿Qué margen bruto en pesos tuvo Almacén en el T3 del AF2026?", "margen_bruto",
         {"categoria": "Almacén", "periodo": T3_AF2026}),
        ("¿Cuánto vendió la sucursal S11 en enero de 2026?", "ventas_netas", {"sucursal": "S11", "periodo": MES(2026, 1, 31)}),
        ("¿Y en febrero?", "ventas_netas", {"sucursal": "S11", "periodo": MES(2026, 2, 28)})]),
]
FORMULAS = {
    "ventas_netas": "SUM(v.importe_neto)",
    "unidades": "SUM(v.unidades)",
    "margen_bruto": "SUM(v.importe_neto) - SUM(v.costo)",
    "margen_pct": "(SUM(v.importe_neto) - SUM(v.costo)) / SUM(v.importe_neto) * 100",
}
TOLERANCIA = {"ventas_netas": 0.5, "margen_bruto": 0.5, "unidades": 0, "margen_pct": 0.005, "sucursales_abiertas": 0}


def chequeo(con, medida, filtros):
    """El chequeo de un turno, con su valor calculado con SQL escrito a mano."""
    donde, parametros = [], []
    for campo, columna in [("categoria", "p.categoria"), ("subcategoria", "p.subcategoria"),
                           ("region", "s.region"), ("sucursal", "v.sucursal_id")]:
        if campo in filtros:
            donde.append(f"{columna} = ?")
            parametros.append(filtros[campo])
    if medida == "sucursales_abiertas":
        valor = con.execute("SELECT COUNT(*) FROM sucursales s WHERE s.region = ?", [filtros["region"]]).fetchone()[0]
        return {"medida": medida, "tipo": "valor", "esperado": valor, "tolerancia": 0}
    donde.append("v.fecha BETWEEN ? AND ?")
    parametros += list(filtros["periodo"])
    desde = ("FROM ventas v JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id "
             "WHERE " + " AND ".join(donde))
    if medida.startswith("ranking_sucursal_"):
        n = int(medida.rsplit("_", 1)[1])
        filas = con.execute(f"SELECT v.sucursal_id {desde} GROUP BY 1 ORDER BY SUM(v.importe_neto) DESC LIMIT {n}",
                            parametros).fetchall()
        return {"medida": "ventas_netas", "tipo": "ranking", "dimension": "sucursal", "esperado": [f[0] for f in filas]}
    valor = con.execute(f"SELECT {FORMULAS[medida]} {desde}", parametros).fetchone()[0]
    chequeo = {"medida": medida, "tipo": "valor", "esperado": round(float(valor), 4), "tolerancia": TOLERANCIA[medida]}
    # Como en esperados.yaml (decisión 37): si agrupa en vez de filtrar, vale la fila del filtro más específico, y solo
    # si además da el valor esperado (una fila de Gaseosas sin el filtro de región da otro número y falla igual)
    for campo in ("sucursal", "subcategoria", "categoria", "region"):
        if campo in filtros:
            chequeo["fila"] = {campo: filtros[campo]}
            break
    return chequeo


def esperados():
    with duckdb.connect(BASE, read_only=True) as con:
        return {id_: [chequeo(con, m, f) for _, m, f in turnos] for id_, _, turnos in CONVERSACIONES}


def calificar(respuestas, chequeos):
    """Turno por turno, cada uno con sus propias consultas."""
    lineas = []
    for numero, (respuesta, ch) in enumerate(zip(respuestas, chequeos), 1):
        malos = ruteo(respuesta)
        if not malos and (motivo := reproducible(respuesta)):
            malos = ["consulta: " + motivo]
        if not malos:
            malos = fallos([ch], respuesta["consultas"], respuesta)
        lineas.append({"turno": numero, "paso": not falla(malos), "detalle": " · ".join(malos),
                       "texto": respuesta["texto"]})
    return lineas


async def correr(id_, turnos, chequeos, vez, semaforo):
    async with semaforo:
        registro.CASO.set(f"{id_}-{vez}")
        respuestas = await atender([t for t, _, _ in turnos])
        lineas = calificar(respuestas, chequeos)
        print(f"· {id_} (corrida {vez}): " + "".join("✓" if l["paso"] else "✗" for l in lineas), flush=True)
        return {"id": id_, "vez": vez, "turnos": lineas}


def costo():
    return sum(l["costo_usd"] for l in registro.leer(registro.LLAMADAS) if l.get("corrida") == registro.CORRIDA)


async def main(ids, veces):
    CARPETA.mkdir(parents=True, exist_ok=True)
    todos = esperados()
    (CARPETA / "esperados.json").write_text(json.dumps(todos, ensure_ascii=False, indent=2))  # antes de correr
    casos = [c for c in CONVERSACIONES if not ids or c[0] in ids]
    semaforo = asyncio.Semaphore(PARALELO)
    inicio = time.monotonic()
    trabajos = [(c, v) for v in range(1, veces + 1) for c in casos]
    correr_uno = lambda c, v: correr(c[0], c[2], todos[c[0]], v, semaforo)
    resultados = [await correr_uno(*trabajos[0])]  # el primero solo: escribe el caché del prefijo
    resultados += await asyncio.gather(*(correr_uno(c, v) for c, v in trabajos[1:]))
    reloj = time.monotonic() - inicio

    turnos_todos = [l for r in resultados for l in r["turnos"]]
    enteras = [r for r in resultados if all(l["paso"] for l in r["turnos"])]
    lineas = ["# Test 7: conversación (decisión 118)", "",
              f"Comando: `.venv/bin/python evaluacion/robustez/conversacion.py{f' --veces {veces}' if veces > 1 else ''}` · "
              f"{len(casos)} conversaciones de 3 turnos × {veces} · US$ {costo():.3f} · {reloj:.0f} s", "",
              f"**Turnos correctos: {sum(l['paso'] for l in turnos_todos)} de {len(turnos_todos)}** · "
              f"conversaciones enteras: {len(enteras)} de {len(resultados)}", "",
              "## Por grupo", "", "| Grupo | Turnos 2 y 3 (los que dependen de la conversación) |", "|---|---|"]
    for grupo in dict.fromkeys(g for _, g, _ in casos):
        ls = [l for r in resultados for l in r["turnos"] if l["turno"] > 1
              and next(g for i, g, _ in casos if i == r["id"]) == grupo]
        lineas.append(f"| {grupo} | {sum(l['paso'] for l in ls)} de {len(ls)} |")
    lineas += ["", "## Cada conversación", "", "| Conv. | Grupo | Turno | Pregunta | Esperado | Corridas |",
               "|---|---|---|---|---|---|"]
    for id_, grupo, turnos in casos:
        rs = sorted((r for r in resultados if r["id"] == id_), key=lambda r: r["vez"])
        for n, ((texto, _, _), ch) in enumerate(zip(turnos, todos[id_]), 1):
            esperado = (", ".join(ch["esperado"]) if ch["tipo"] == "ranking"
                        else f"{ch['esperado']:,.2f}".replace(",", "_").replace(".", ",").replace("_", "."))
            lineas.append(f"| {id_ if n == 1 else ''} | {grupo if n == 1 else ''} | {n} | {texto} | "
                          f"{ch['medida']} {esperado} | " + "".join("✓" if r["turnos"][n - 1]["paso"] else "✗" for r in rs) + " |")
    malas = [(r, l) for r in resultados for l in r["turnos"] if not l["paso"]]
    if malas:
        lineas += ["", "## Los turnos que fallaron: por qué y qué respondió", ""]
        for r, l in sorted(malas, key=lambda x: (x[0]["id"], x[0]["vez"], x[1]["turno"])):
            lineas += [f"**{r['id']}, corrida {r['vez']}, turno {l['turno']}**: {l['detalle']}", "",
                       "> " + l["texto"].replace("\n", "\n> "), ""]
    texto = "\n".join(lineas) + "\n"
    (CARPETA / "resultado.md").write_text(texto)
    (CARPETA / "resultados.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2, default=str))
    Path("trazas/conversacion.md").write_text(texto)
    print(texto)


if __name__ == "__main__":
    args = sys.argv[1:]
    veces = 1
    if "--veces" in args:
        i = args.index("--veces")
        veces = int(args[i + 1])
        del args[i:i + 2]
    if args == ["--esperados"]:
        print(json.dumps(esperados(), ensure_ascii=False, indent=1))
    else:
        asyncio.run(main(args, veces))
