"""Fase 2 del año simulado (decisión 89): la tasa de detección de verificar_base.py. Es *mutation testing* aplicado a
los datos: la calidad de una verificación se mide por el porcentaje de fallas inyectadas que encuentra.

Para cada semilla: una copia del año simulado (salidas/anio/limpia.duckdb, de evaluacion/pruebas/anio_simulado.py) con un error
de carga de cada tipo del catálogo, en un lugar del AF2027 sorteado. Un tipo cuenta como detectado si el control que le
corresponde marca más filas que en la base sin errores (la base ya trae avisos propios, como el cierre de S07).

Además, 6 errores «ciegos», sin control propio, de a uno por copia: cuenta si salta cualquier control.

Uso: .venv/bin/python evaluacion/pruebas/deteccion.py [N]      (N semillas, 30 por defecto; ~9 s cada una, unos 4 minutos; sin modelo)
Deja salidas/deteccion/resultado.md y lo copia a trazas/deteccion.md."""
import random
import shutil
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(RAIZ / "analista"), str(RAIZ / "evaluacion")]

import duckdb  # noqa: E402

from verificar_base import verificar  # noqa: E402

ANIO = Path("salidas/anio/limpia.duckdb")
CARPETA = Path("salidas/deteccion")
COPIA = CARPETA / "copia.duckdb"
NUEVO = "fecha >= DATE '2026-05-01'"  # los errores van en el lote nuevo

# (id, qué es, control que lo tiene que ver, nivel)
CATALOGO = [
    ("dia_duplicado", "un día de una sucursal cargado dos veces", "ventas: una fila por fecha, sucursal, producto y tipo", "error"),
    ("sku_inexistente", "ventas de un producto que no está en el maestro", "ventas: cada fila encuentra su productos", "error"),
    ("neto_no_cierra", "el descuento restado dos veces en un día de una sucursal", "ventas: neto = bruto − descuento", "error"),
    ("devolucion_positiva", "devoluciones de un día con el signo cambiado", "ventas: devoluciones con unidades negativas y ventas con positivas", "error"),
    ("promo_vencida", "ventas con una promoción que ya había terminado", "ventas: la promoción es de ese producto y estaba vigente", "error"),
    ("stock_negativo", "una foto de stock con unidades negativas", "stock: sin unidades negativas", "error"),
    ("fiscal_mal", "el mes fiscal corrido en un mes del calendario", "fechas: año, mes y trimestre fiscal", "error"),
    ("categoria_mal_escrita", "presupuesto de una categoría mal escrita («Almacen»)", "presupuesto: categorías que existen en productos", "error"),
    ("dia_faltante", "un día de una sucursal sin cargar", "ventas: días sin ventas de una sucursal abierta (¿carga incompleta?)", "aviso"),
    ("foto_faltante", "una semana de stock de una sucursal sin cargar", "stock: semanas sin foto de una sucursal abierta", "aviso"),
    ("costo_x10", "el costo de un producto ×10 durante un mes", "ventas: el costo por unidad de un producto salta contra sus meses vecinos", "aviso"),
    ("presupuesto_x10", "el presupuesto de una celda (mes, sucursal, categoría) ×10",
     "presupuesto: presupuesto ÷ ventas salta contra sus meses vecinos (decisión 84)", "aviso"),
    ("importes_x100", "los importes de un día de una sucursal en centavos (×100)",
     "ventas: las ventas de un día de una sucursal saltan contra el mismo día de las semanas vecinas", "aviso"),
    ("unidades_x1000", "las unidades de un producto en una sucursal y un día cargadas en miles",
     "ventas: una fila con más de 50 veces las unidades habituales de su producto", "aviso"),
]

# Errores para los que no se escribió ningún control: cuenta como detectado si cualquier control marca más filas.
# Contra el problema del oráculo (decisión 88): el catálogo de arriba se armó conociendo los controles
CIEGOS = [
    ("sucursal_cambiada", "un día de una sucursal cargado con el código de otra"),
    ("carga_parcial", "un día de una sucursal cargado sin una categoría"),
    ("foto_repetida", "la foto de stock de una sucursal repite la de la semana anterior"),
    ("presupuesto_corrido", "el presupuesto de una sucursal cargado con los números del mes siguiente"),
    ("precio_5pct", "un día de una sucursal con los importes 5 % más altos (lista de precios vieja)"),
    ("dia_en_otra_fecha", "un día de una sucursal cargado con la fecha del día siguiente"),
]


def conteos(ruta):
    """{control: filas marcadas} de los errores y de los avisos."""
    resultados, _, raras = verificar(str(ruta))
    return {**{n: m for n, m in resultados}, **{n: c for n, c, _ in raras}}


def lugares(con):
    """Los lugares posibles del lote nuevo, una sola vez. Las listas largas se cortan en un orden pseudoaleatorio y fijo
    (por hash), no por fecha: cortadas por fecha, solo entraban los primeros meses del año (revisión del 19-11)."""
    q = lambda sql: con.execute(sql).fetchall()
    return {
        "dias": q(f"SELECT DISTINCT fecha, sucursal_id FROM ventas WHERE {NUEVO} ORDER BY 1, 2"),
        "dias_con_devolucion": q(f"SELECT DISTINCT fecha, sucursal_id FROM ventas WHERE {NUEVO} AND tipo_movimiento = 'devolucion' ORDER BY 1, 2"),
        "dias_con_descuento": q(f"SELECT DISTINCT fecha, sucursal_id FROM ventas WHERE {NUEVO} AND descuento > 0 ORDER BY 1, 2"),
        "filas_stock": q("SELECT semana, sucursal_id, sku FROM stock_semanal WHERE semana >= DATE '2026-05-04' AND stock_unidades > 0 "
                         "ORDER BY HASH(semana, sucursal_id, sku) LIMIT 200000"),
        "fotos": q("SELECT DISTINCT semana, sucursal_id FROM stock_semanal WHERE semana >= DATE '2026-05-04' ORDER BY 1, 2"),
        "meses_sku": q(f"SELECT DISTINCT DATE_TRUNC('month', fecha)::DATE, sku FROM ventas WHERE {NUEVO} ORDER BY 1, 2"),
        "celdas": q("SELECT mes, sucursal_id, categoria FROM presupuesto WHERE mes >= DATE '2026-05-01' ORDER BY 1, 2, 3"),
        "filas_venta": q(f"SELECT fecha, sucursal_id, sku FROM ventas WHERE {NUEVO} AND tipo_movimiento = 'venta' ORDER BY HASH(fecha, sucursal_id, sku) LIMIT 300000"),
        "promos": q("SELECT promocion_id, sku, fecha_desde, fecha_hasta FROM promociones ORDER BY 1"),
        "meses": [(2026, m) for m in range(5, 13)] + [(2027, m) for m in range(1, 5)],
    }


def plantar(con, rng, L):
    """Un error de cada tipo, en un lugar sorteado. Devuelve dónde quedó cada uno."""
    donde = {}
    f, s = rng.choice(L["dias"])
    con.execute("INSERT INTO ventas SELECT * FROM ventas WHERE fecha = ? AND sucursal_id = ?", [f, s])
    donde["dia_duplicado"] = f"{s} {f}"
    f, s, sku = rng.choice(L["filas_venta"])
    con.execute("INSERT INTO ventas SELECT fecha, sucursal_id, 'P9' || RIGHT(sku, 3), tipo_movimiento, unidades, importe_bruto, "
                "descuento, importe_neto, costo, NULL FROM ventas WHERE fecha = ? AND sucursal_id = ? AND sku = ? AND tipo_movimiento = 'venta'",
                [f, s, sku])
    donde["sku_inexistente"] = f"{s} {f} P9{sku[-3:]}"
    f, s = rng.choice(L["dias_con_descuento"])
    con.execute("UPDATE ventas SET importe_neto = importe_neto - descuento WHERE fecha = ? AND sucursal_id = ? AND descuento > 0", [f, s])
    donde["neto_no_cierra"] = f"{s} {f}"
    f, s = rng.choice(L["dias_con_devolucion"])
    con.execute("UPDATE ventas SET unidades = -unidades, importe_bruto = -importe_bruto, importe_neto = -importe_neto, costo = -costo "
                "WHERE fecha = ? AND sucursal_id = ? AND tipo_movimiento = 'devolucion'", [f, s])
    donde["devolucion_positiva"] = f"{s} {f}"
    pid, sku, desde, hasta = rng.choice(L["promos"])
    filas = con.execute(f"SELECT fecha, sucursal_id FROM ventas WHERE {NUEVO} AND sku = ? AND tipo_movimiento = 'venta' "
                        "AND fecha > ? ORDER BY 1, 2 LIMIT 50", [sku, hasta]).fetchall()
    if filas:
        f, s = rng.choice(filas)
        con.execute("UPDATE ventas SET promocion_id = ? WHERE fecha = ? AND sucursal_id = ? AND sku = ? AND tipo_movimiento = 'venta'",
                    [pid, f, s, sku])
        donde["promo_vencida"] = f"{s} {f} {sku} con {pid} (terminó el {hasta})"
    semana, s, sku = rng.choice(L["filas_stock"])
    con.execute("UPDATE stock_semanal SET stock_unidades = -stock_unidades WHERE semana = ? AND sucursal_id = ? AND sku = ?", [semana, s, sku])
    donde["stock_negativo"] = f"{s} {semana} {sku}"
    anio, mes = rng.choice(L["meses"])
    con.execute("UPDATE fechas SET mes_fiscal = mes_fiscal % 12 + 1 WHERE anio = ? AND mes = ?", [anio, mes])
    donde["fiscal_mal"] = f"{anio}-{mes:02d}"
    mes, s, _ = rng.choice(L["celdas"])
    con.execute("INSERT INTO presupuesto SELECT mes, sucursal_id, 'Almacen', importe_presupuesto FROM presupuesto "
                "WHERE mes = ? AND sucursal_id = ? AND categoria = 'Almacén'", [mes, s])
    donde["categoria_mal_escrita"] = f"{s} {mes}"
    f, s = rng.choice(L["dias"])
    con.execute("DELETE FROM ventas WHERE fecha = ? AND sucursal_id = ?", [f, s])
    donde["dia_faltante"] = f"{s} {f}"
    semana, s = rng.choice(L["fotos"])
    con.execute("DELETE FROM stock_semanal WHERE semana = ? AND sucursal_id = ?", [semana, s])
    donde["foto_faltante"] = f"{s} {semana}"
    mes, sku = rng.choice(L["meses_sku"])
    con.execute("UPDATE ventas SET costo = costo * 10 WHERE sku = ? AND DATE_TRUNC('month', fecha) = ?", [sku, mes])
    donde["costo_x10"] = f"{sku} {mes:%Y-%m}"
    mes, s, c = rng.choice(L["celdas"])
    con.execute("UPDATE presupuesto SET importe_presupuesto = importe_presupuesto * 10 WHERE mes = ? AND sucursal_id = ? AND categoria = ?",
                [mes, s, c])
    donde["presupuesto_x10"] = f"{s} {c} {mes:%Y-%m}"
    f, s = rng.choice(L["dias"])
    con.execute("UPDATE ventas SET importe_bruto = importe_bruto * 100, descuento = descuento * 100, importe_neto = importe_neto * 100 "
                "WHERE fecha = ? AND sucursal_id = ?", [f, s])
    donde["importes_x100"] = f"{s} {f}"
    f, s, sku = rng.choice(L["filas_venta"])
    con.execute("UPDATE ventas SET unidades = unidades * 1000 WHERE fecha = ? AND sucursal_id = ? AND sku = ? AND tipo_movimiento = 'venta'",
                [f, s, sku])
    donde["unidades_x1000"] = f"{s} {f} {sku}"
    return donde


def plantar_ciego(con, rng, L, id_):
    """Un error ciego, solo: así, el control que salte es por él."""
    if id_ == "sucursal_cambiada":
        f, s = rng.choice(L["dias"])
        otra = rng.choice(sorted({d[1] for d in L["dias"]} - {s}))
        con.execute("DELETE FROM ventas WHERE fecha = ? AND sucursal_id = ?", [f, otra])  # el día de la otra se pisa
        con.execute("UPDATE ventas SET sucursal_id = ? WHERE fecha = ? AND sucursal_id = ?", [otra, f, s])
        return f"{s} {f} cargado como {otra}"
    if id_ == "carga_parcial":
        f, s = rng.choice(L["dias"])
        categoria = rng.choice(["Almacén", "Bebidas", "Frescos", "Lácteos", "Limpieza", "Perfumería"])
        con.execute("DELETE FROM ventas WHERE fecha = ? AND sucursal_id = ? AND sku IN (SELECT sku FROM productos WHERE categoria = ?)",
                    [f, s, categoria])
        return f"{s} {f} sin {categoria}"
    if id_ == "foto_repetida":
        semana, s = rng.choice([x for x in L["fotos"] if str(x[0]) > "2026-05-04"])
        con.execute("""UPDATE stock_semanal st SET stock_unidades = a.stock_unidades FROM stock_semanal a
                       WHERE st.semana = ? AND st.sucursal_id = ? AND a.semana = st.semana - 7 AND a.sucursal_id = st.sucursal_id
                       AND a.sku = st.sku""", [semana, s])
        return f"{s} {semana}"
    if id_ == "presupuesto_corrido":
        mes, s, _ = rng.choice([x for x in L["celdas"] if str(x[0]) < "2027-04-01"])
        con.execute("""UPDATE presupuesto p SET importe_presupuesto = n.importe_presupuesto FROM presupuesto n
                       WHERE p.mes = ? AND p.sucursal_id = ? AND n.mes = p.mes + INTERVAL 1 MONTH AND n.sucursal_id = p.sucursal_id
                       AND n.categoria = p.categoria""", [mes, s])
        return f"{s} {mes:%Y-%m}"
    if id_ == "precio_5pct":
        f, s = rng.choice(L["dias"])
        con.execute("UPDATE ventas SET importe_bruto = ROUND(importe_bruto * 1.05, 2), descuento = ROUND(descuento * 1.05, 2) "
                    "WHERE fecha = ? AND sucursal_id = ?", [f, s])
        con.execute("UPDATE ventas SET importe_neto = importe_bruto - descuento WHERE fecha = ? AND sucursal_id = ?", [f, s])
        return f"{s} {f}"
    if id_ == "dia_en_otra_fecha":
        f, s = rng.choice([x for x in L["dias"] if str(x[0]) < "2027-04-30"])
        con.execute("DELETE FROM ventas WHERE fecha = ? + 1 AND sucursal_id = ?", [f, s])
        con.execute("UPDATE ventas SET fecha = fecha + 1 WHERE fecha = ? AND sucursal_id = ?", [f, s])
        return f"{s} {f} cargado como el día siguiente"
    raise ValueError(id_)


def main(n):
    if not ANIO.exists():
        sys.exit("Falta el año simulado: correr antes .venv/bin/python evaluacion/pruebas/anio_simulado.py")
    CARPETA.mkdir(parents=True, exist_ok=True)
    inicio = time.monotonic()
    base = conteos(ANIO)
    with duckdb.connect(str(ANIO), read_only=True) as con:
        L = lugares(con)
    detectados = {t[0]: 0 for t in CATALOGO}
    plantados = {t[0]: 0 for t in CATALOGO}
    se_le_escapo = {t[0]: [] for t in CATALOGO}
    ciegos = {i: [] for i, _ in CIEGOS}
    for semilla in range(n):
        shutil.copy(ANIO, COPIA)
        with duckdb.connect(str(COPIA)) as con:
            donde = plantar(con, random.Random(semilla), L)
        despues = conteos(COPIA)
        for id_, _, control, _ in CATALOGO:
            if id_ not in donde:
                continue
            plantados[id_] += 1
            if despues.get(control, 0) > base.get(control, 0):
                detectados[id_] += 1
            else:
                se_le_escapo[id_].append(donde[id_])
        print(f"· semilla {semilla}: {sum(despues.get(c, 0) > base.get(c, 0) for i, _, c, _ in CATALOGO if i in donde)} de {len(donde)}",
              flush=True)
        for k, (id_, _) in enumerate(CIEGOS):  # uno por copia: juntos, un control que salta por uno contaría para todos
            shutil.copy(ANIO, COPIA)
            with duckdb.connect(str(COPIA)) as con:
                lugar = plantar_ciego(con, random.Random(1000 * (k + 1) + semilla), L, id_)
            despues = conteos(COPIA)
            saltaron = [c for c in despues if despues[c] > base.get(c, 0)]
            ciegos[id_].append((lugar, saltaron))
    COPIA.unlink()
    segundos = time.monotonic() - inicio

    lineas = ["# Tasa de detección de `verificar_base.py` (decisión 89)", "",
              f"Comando: `.venv/bin/python evaluacion/pruebas/deteccion.py {n}` · {n} semillas · {segundos:.0f} s, sin modelo · "
              "sobre el año simulado (decisión 88), con los errores en el AF2027", "",
              "| Error de carga | Nivel esperado | Control | Detectado |", "|---|---|---|---|"]
    for id_, que, control, nivel in CATALOGO:
        p, d = plantados[id_], detectados[id_]
        lineas.append(f"| {que} | {nivel} | {control} | **{d} de {p}** ({d / p * 100:.0f} %) |" if p else f"| {que} | {nivel} | {control} | sin lugar |")
    total_p, total_d = sum(plantados.values()), sum(detectados.values())
    lineas += ["", f"**Total: {total_d} de {total_p} ({total_d / total_p * 100:.1f} %).**"]
    escapes = {i: v for i, v in se_le_escapo.items() if v}
    if escapes:
        lineas += ["", "## Los que se escaparon", ""]
        lineas += [f"- {i}: " + "; ".join(v[:5]) + (f" (y {len(v) - 5} más)" if len(v) > 5 else "") for i, v in escapes.items()]
    lineas += ["", "## Errores sin control propio (contra el problema del oráculo)", "",
               "Errores comunes de carga elegidos sin buscar un control que los atrape (no es un oráculo independiente: los eligió quien conoce los controles): cuenta como detectado si cualquier control marca más filas.", "",
               "| Error de carga | Detectado | Por qué control |", "|---|---|---|"]
    for id_, que in CIEGOS:
        r = ciegos[id_]
        d = sum(1 for _, s in r if s)
        por = sorted({c for _, s in r for c in s})
        lineas.append(f"| {que} | **{d} de {len(r)}** ({d / len(r) * 100:.0f} %) | {'; '.join(por) or '—'} |")
    texto = "\n".join(lineas) + "\n"
    (CARPETA / "resultado.md").write_text(texto)
    Path("trazas/deteccion.md").write_text(texto)
    print(texto)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 30)
