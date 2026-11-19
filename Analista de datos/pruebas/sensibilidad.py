"""Fase 3 (decisión 91): la sensibilidad de verificar_base.py. ¿Cuál es el error más chico que detecta, y cuántas falsas
alarmas daría con otro umbral?

Los controles por salto comparan un valor con la mediana de sus vecinos (presupuesto ÷ ventas de una celda, costo
unitario de un producto en un mes, ventas de un día de una sucursal) y avisan si el cociente pasa de 3 veces
(VECES_SOSPECHOSO, decisión 84). Multiplicar el dato por k multiplica su cociente por k, y los vecinos no cambian. Así que
no hace falta sortear: con el cociente natural r de cada lugar de la base, un error ×k se detecta si k·r ≥ umbral, y la
curva de detección sale exacta sobre todos los lugares, no sobre una muestra. Para confirmar que la cuenta coincide con
el control de verdad, se inyectan errores reales en una copia y se corre la función del control.

Se hace sobre la base real (dos años), sin las celdas que ya están marcadas (el error de carga de enero de 2026), que
son las únicas que no son datos normales.

Uso: .venv/bin/python pruebas/sensibilidad.py      (~1 minuto, sin modelo)
Deja salidas/sensibilidad/resultado.md y lo copia a trazas/sensibilidad.md."""
import random
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import duckdb  # noqa: E402

from procesador_capa_semantica import VECES_SOSPECHOSO, celdas_de_presupuesto_sospechosas  # noqa: E402
from verificar_base import UMBRALES as UMBRAL_DE  # noqa: E402

ORIGINAL = "Data/base/almacenes_del_sur.duckdb"
CARPETA = Path("salidas/sensibilidad")
TAMANIOS = [1.25, 1.5, 2, 3, 5, 10]
FALTANTE = [0.10, 0.25, 0.50, 0.67, 0.75, 0.90]
UMBRALES = [1.5, 2, 2.5, 3, 4]

# El cociente natural de cada lugar contra sus vecinos: el mismo SQL de los controles, sin el filtro del umbral
COCIENTES = {
    "presupuesto": ("presupuesto de una celda (mes, sucursal, categoría)", """
        WITH vendido AS (SELECT date_trunc('month', v.fecha) AS mes, v.sucursal_id, p.categoria, SUM(v.importe_neto) AS ventas
                         FROM ventas v JOIN productos p ON v.sku = p.sku GROUP BY 1, 2, 3),
             celdas AS (SELECT pz.mes, pz.sucursal_id, pz.categoria, pz.importe_presupuesto / vd.ventas AS cociente
                        FROM presupuesto pz JOIN vendido vd ON vd.mes = pz.mes AND vd.sucursal_id = pz.sucursal_id
                        AND vd.categoria = pz.categoria WHERE vd.ventas > 0)
        SELECT a.cociente / (SELECT median(b.cociente) FROM celdas b WHERE b.sucursal_id = a.sucursal_id
                             AND b.categoria = a.categoria AND b.mes <> a.mes
                             AND b.mes BETWEEN a.mes - INTERVAL 2 MONTH AND a.mes + INTERVAL 2 MONTH) FROM celdas a"""),
    "costo": ("costo de un producto en un mes", """
        WITH m AS (SELECT sku, DATE_TRUNC('month', fecha) AS mes, SUM(costo) / SUM(unidades) AS cu
                   FROM ventas WHERE tipo_movimiento = 'venta' GROUP BY 1, 2)
        SELECT a.cu / (SELECT MEDIAN(b.cu) FROM m b WHERE b.sku = a.sku AND b.mes <> a.mes
                       AND b.mes BETWEEN a.mes - INTERVAL 2 MONTH AND a.mes + INTERVAL 2 MONTH) FROM m a"""),
    "dia": ("importes de un día de una sucursal", """
        WITH d AS (SELECT sucursal_id, fecha, SUM(importe_neto) AS x FROM ventas GROUP BY 1, 2)
        SELECT a.x / (SELECT MEDIAN(b.x) FROM d b WHERE b.sucursal_id = a.sucursal_id AND b.fecha <> a.fecha
                      AND DAYOFWEEK(b.fecha) = DAYOFWEEK(a.fecha) AND b.fecha BETWEEN a.fecha - 28 AND a.fecha + 28) FROM d a"""),
}


def cocientes(con):
    """{control: [r de cada lugar normal]}: sin vacíos y sin lo que ya está marcado con el umbral actual."""
    salida = {}
    for clave, (_, sql) in COCIENTES.items():
        r = [x for (x,) in con.execute(sql).fetchall() if x is not None and x > 0]
        salida[clave] = [x for x in r if 1 / VECES_SOSPECHOSO < x < VECES_SOSPECHOSO]
        salida[clave + "_marcados"] = len(r) - len(salida[clave])
        salida[clave + "_todos"] = r
    return salida


def unidades(con):
    """Para las unidades ×k: el cociente de cada fila de venta contra 50 veces la mediana de su producto."""
    return [x for (x,) in con.execute("""
        SELECT v.unidades / (50.0 * m.med) FROM ventas v
        JOIN (SELECT sku, MEDIAN(unidades) AS med FROM ventas WHERE tipo_movimiento = 'venta' GROUP BY 1) m USING (sku)
        WHERE v.tipo_movimiento = 'venta' USING SAMPLE 200000 ROWS (reservoir, 7)""").fetchall()]


def confirmar(n=10):
    """Inyecta errores de presupuesto ×2 y ×3 en celdas sorteadas de una copia, corre la función del control y compara
    con lo que predice la cuenta (k·r ≥ 3). Cada inyección se deshace antes de la siguiente."""
    copia = CARPETA / "copia.duckdb"
    shutil.copy(ORIGINAL, copia)
    rng = random.Random(91)
    coinciden, casos = 0, []
    with duckdb.connect(str(copia)) as con:
        celdas = con.execute("""
            WITH vendido AS (SELECT date_trunc('month', v.fecha)::DATE AS mes, v.sucursal_id, p.categoria, SUM(v.importe_neto) AS ventas
                             FROM ventas v JOIN productos p ON v.sku = p.sku GROUP BY 1, 2, 3),
                 celdas AS (SELECT pz.mes, pz.sucursal_id, pz.categoria, pz.importe_presupuesto / vd.ventas AS cociente
                            FROM presupuesto pz JOIN vendido vd ON vd.mes = pz.mes AND vd.sucursal_id = pz.sucursal_id
                            AND vd.categoria = pz.categoria)
            SELECT a.mes, a.sucursal_id, a.categoria, a.cociente / (SELECT median(b.cociente) FROM celdas b
                   WHERE b.sucursal_id = a.sucursal_id AND b.categoria = a.categoria AND b.mes <> a.mes
                   AND b.mes BETWEEN a.mes - INTERVAL 2 MONTH AND a.mes + INTERVAL 2 MONTH)
            FROM celdas a ORDER BY 1, 2, 3""").fetchall()
        normales = [c for c in celdas if c[3] and 1 / VECES_SOSPECHOSO < c[3] < VECES_SOSPECHOSO]
        for k in (2, 3):
            for mes, suc, cat, r in rng.sample(normales, n):
                con.execute("BEGIN")
                con.execute("UPDATE presupuesto SET importe_presupuesto = importe_presupuesto * ? "
                            "WHERE mes = ? AND sucursal_id = ? AND categoria = ?", [k, mes, suc, cat])
                marcada = any((a, m, s, c) == (mes.year, mes.month, suc, cat)
                              for a, m, s, c, *_ in celdas_de_presupuesto_sospechosas(con))
                con.execute("ROLLBACK")
                predicho = k * r >= VECES_SOSPECHOSO
                coinciden += marcada == predicho
                casos.append((k, f"{suc} {cat} {mes:%Y-%m}", round(r, 3), predicho, marcada))
    copia.unlink()
    return coinciden, casos


def miles(n):
    return f"{n:,}".replace(",", ".")


def pct(x):
    return f"{x * 100:.0f} %" if x >= 0.005 or x == 0 else "<1 %"


def main():
    CARPETA.mkdir(parents=True, exist_ok=True)
    inicio = time.monotonic()
    with duckdb.connect(ORIGINAL, read_only=True) as con:
        r = cocientes(con)
        u = unidades(con)
    coinciden, casos = confirmar()
    segundos = time.monotonic() - inicio

    lineas = ["# Sensibilidad de `verificar_base.py` (decisión 91)", "",
              f"Comando: `.venv/bin/python pruebas/sensibilidad.py` · {segundos:.0f} s, sin modelo · base real (AF2025 y AF2026)", "",
              "La curva de detección es exacta sobre todos los lugares normales de la base: un error ×k en un lugar con "
              "cociente natural r contra sus vecinos se detecta si k·r ≥ 3.", "",
              "## 1. El error más chico que detecta, con el umbral de cada control", "",
              "Umbrales de `verificar_base.py`: " + ", ".join(f"{COCIENTES[c][0]}: {str(u).replace('.', ',')}" for c, u in UMBRAL_DE.items())
              + f" (decisión 92). El agente sigue avisando desde {VECES_SOSPECHOSO} en el presupuesto (decisión 84).", "",
              "| Error | Lugares | " + " | ".join(f"×{str(k).replace('.', ',')}" for k in TAMANIOS) + " |",
              "|---|---|" + "---|" * len(TAMANIOS)]
    for clave, (que, _) in COCIENTES.items():
        xs = r[clave]
        lineas.append(f"| {que} | {miles(len(xs))} | " +
                      " | ".join(pct(sum(k * x >= UMBRAL_DE[clave] for x in xs) / len(xs)) for k in TAMANIOS) + " |")
    lineas.append(f"| unidades de una fila (control: 50 veces la mediana de su producto) | {miles(len(u))} (muestra) | " +
                  " | ".join(pct(sum(k * x > 1 for x in u) / len(u)) for k in TAMANIOS) + " |")
    lineas += ["", "Con más tamaños para las unidades: " + " · ".join(
        f"×{k}: {pct(sum(k * x > 1 for x in u) / len(u))}" for k in (10, 25, 50, 100, 1000)), "",
        "## 2. Un día cargado a medias", "",
        "Si falta una parte de un día (por ejemplo, una categoría), las ventas del día bajan esa fracción. El control "
        "lo ve si el día queda por debajo de 1/3 de sus vecinos.", "",
        "| Falta | " + " | ".join(f"{f * 100:.0f} %" for f in FALTANTE) + " | 100 % |", "|---|" + "---|" * (len(FALTANTE) + 1),
        "| Detectado | " + " | ".join(pct(sum((1 - f) * x <= 1 / VECES_SOSPECHOSO for x in r["dia"]) / len(r["dia"])) for f in FALTANTE)
        + " | 100 % (días sin ventas) |",
        "", "## 3. ¿Por qué 3 y no otro umbral? Detección contra falsas alarmas", "",
        "Falsas alarmas: lugares de la base real, sin errores, que el control marcaría con ese umbral. Detección: de un "
        "error ×2.", "",
        "| Umbral | " + " | ".join(f"{que}: falsas alarmas · detecta ×2" for _, (que, _) in COCIENTES.items()) + " |",
        "|---|" + "---|" * len(COCIENTES)]
    for t in UMBRALES:
        celdas = []
        for clave in COCIENTES:
            xs = r[clave]
            todos = len(r[clave + "_todos"])
            fa = sum(x >= t or x <= 1 / t for x in r[clave + "_todos"])
            det = sum(2 * x >= t for x in xs) / len(xs)
            celdas.append(f"{fa:,} ({pct(fa / todos)}) · {pct(det)}".replace(",", "."))
        lineas.append(f"| {str(t).replace('.', ',')} | " + " | ".join(celdas) + " |")
    lineas += ["", "(Con el umbral actual, las falsas alarmas incluyen los lugares que la base ya marca: las 10 celdas del "
               "error de carga de enero de 2026 en el presupuesto, que no son falsas.)", "",
               "## 4. Confirmación con inyecciones reales", "",
               f"Presupuesto ×2 y ×3 en {len(casos)} celdas sorteadas de una copia, corriendo la función del control: "
               f"**{coinciden} de {len(casos)}** coinciden con la cuenta.", "",
               "| Error | Celda | r natural | Predicho | Marcado por el control |", "|---|---|---|---|---|"]
    lineas += [f"| ×{k} | {c} | {str(rr).replace('.', ',')} | {'sí' if p else 'no'} | {'sí' if m else 'no'} |" for k, c, rr, p, m in casos]
    texto = "\n".join(lineas) + "\n"
    (CARPETA / "resultado.md").write_text(texto)
    Path("trazas/sensibilidad.md").write_text(texto)
    print(texto)


if __name__ == "__main__":
    main()
