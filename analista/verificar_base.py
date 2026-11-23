"""Verifica la base después de una ingesta de datos nuevos (decisión 63; guía: Data/base/INGESTA.md).
La base no declara claves foráneas: si una fila no calza en un join, el número sale mal sin ningún error. Este
script lo controla antes de que el agente o el informe programado usen la base.
Dos niveles (decisión 85): los errores (estructura, valores imposibles, importes que no cierran) bloquean, porque con
ellos un número sale mal; los avisos (algo raro que puede ser real o un error de carga) se informan y no bloquean,
porque un salto en las ventas puede ser justo lo que hay que encontrar (el quiebre de P14).
Uso: .venv/bin/python analista/verificar_base.py [ruta.duckdb]      (sale con código 1 si hay algún error)"""
import re
import sys

import duckdb
import yaml

from procesador_capa_semantica import BASE, VECES_SOSPECHOSO, celdas_de_presupuesto_sospechosas


def joins_del_esquema():
    """[(tabla, prefijo del join hasta el paso anterior, tabla unida, alias, condición)] de cada join de esquema.yaml,
    más las relaciones une_con: se controlan las mismas que usa el procesador."""
    with open("Data/capa_semantica/esquema.yaml") as f:
        esquema = yaml.safe_load(f)
    pasos = []
    for tabla, datos in esquema["tablas"].items():
        if datos["join"]:
            partes = re.split(r" JOIN ", datos["join"])
            for i, parte in enumerate(partes[1:], 1):
                unida, alias, condicion = re.match(r"(\w+) (\w+) ON (.+)", parte).groups()
                pasos.append((tabla, " JOIN ".join(partes[:i]), unida, alias, condicion))
        for columna, info in datos["columnas"].items():
            if info.get("une_con"):
                otra_tabla, otra_columna = info["une_con"].split(".")
                a = datos["alias"]
                pasos.append((tabla, f"{tabla} {a}", otra_tabla, "u",
                              f"{a}.{columna} = u.{otra_columna} OR {a}.{columna} IS NULL"))
    return pasos


# (nombre, SQL que cuenta las filas con problema). Todo lo que dé más de 0 es un error
CONTROLES = [
    # Claves únicas: si una se repite, los joins duplican filas y los totales se inflan
    ("fechas: una fila por día", "SELECT COUNT(*) - COUNT(DISTINCT fecha) FROM fechas"),
    ("productos: sku único", "SELECT COUNT(*) - COUNT(DISTINCT sku) FROM productos"),
    ("sucursales: sucursal_id único", "SELECT COUNT(*) - COUNT(DISTINCT sucursal_id) FROM sucursales"),
    ("proveedores: proveedor_id único", "SELECT COUNT(*) - COUNT(DISTINCT proveedor_id) FROM proveedores"),
    ("promociones: promocion_id único", "SELECT COUNT(*) - COUNT(DISTINCT promocion_id) FROM promociones"),
    ("ventas: una fila por fecha, sucursal, producto y tipo",
     "SELECT COUNT(*) FROM (SELECT 1 FROM ventas GROUP BY fecha, sucursal_id, sku, tipo_movimiento HAVING COUNT(*) > 1)"),
    ("stock: una fila por semana, sucursal y producto",
     "SELECT COUNT(*) FROM (SELECT 1 FROM stock_semanal GROUP BY semana, sucursal_id, sku HAVING COUNT(*) > 1)"),
    ("presupuesto: una fila por mes, sucursal y categoría",
     "SELECT COUNT(*) FROM (SELECT 1 FROM presupuesto GROUP BY mes, sucursal_id, categoria HAVING COUNT(*) > 1)"),

    # Calendario: sin huecos, y las columnas fiscales según la regla del glosario (el AF empieza el 1 de mayo)
    ("fechas: sin días faltantes", "SELECT DATEDIFF('day', MIN(fecha), MAX(fecha)) + 1 - COUNT(*) FROM fechas"),
    ("fechas: año, mes y día calendario", "SELECT COUNT(*) FROM fechas WHERE anio != YEAR(fecha) OR mes != MONTH(fecha) OR dia != DAY(fecha)"),
    ("fechas: año, mes y trimestre fiscal",
     "SELECT COUNT(*) FROM fechas WHERE anio_fiscal != YEAR(fecha) + (MONTH(fecha) >= 5)::INT"
     " OR mes_fiscal != (MONTH(fecha) + 7) % 12 + 1 OR trimestre_fiscal != ((MONTH(fecha) + 7) % 12) // 3 + 1"),
    ("fechas: semana_inicio es el lunes", "SELECT COUNT(*) FROM fechas WHERE semana_inicio != DATE_TRUNC('week', fecha)"),
    ("fechas: cubre todas las ventas", "SELECT COUNT(*) FROM ventas WHERE fecha > (SELECT MAX(fecha) FROM fechas) OR fecha < (SELECT MIN(fecha) FROM fechas)"),

    # Reglas del negocio que los cálculos dan por ciertas
    ("ventas: tipo de movimiento conocido", "SELECT COUNT(*) FROM ventas WHERE tipo_movimiento NOT IN ('venta', 'devolucion')"),
    ("ventas: devoluciones con unidades negativas y ventas con positivas",
     "SELECT COUNT(*) FROM ventas WHERE (tipo_movimiento = 'devolucion') != (unidades < 0)"),
    ("ventas: sin vacíos en las claves",
     "SELECT COUNT(*) FROM ventas WHERE fecha IS NULL OR sucursal_id IS NULL OR sku IS NULL OR importe_neto IS NULL OR costo IS NULL"),
    ("ventas: ninguna antes de la apertura de su sucursal",
     "SELECT COUNT(*) FROM ventas v JOIN sucursales s USING (sucursal_id) WHERE v.fecha < s.fecha_apertura"),
    ("ventas: la promoción es de ese producto y estaba vigente",
     "SELECT COUNT(*) FROM ventas v JOIN promociones pm USING (promocion_id)"
     " WHERE v.sku != pm.sku OR v.fecha NOT BETWEEN pm.fecha_desde AND pm.fecha_hasta"),
    ("sucursales: todas con fecha de apertura (la usan las comparables)", "SELECT COUNT(*) FROM sucursales WHERE fecha_apertura IS NULL"),
    ("presupuesto: el mes es el día 1", "SELECT COUNT(*) FROM presupuesto WHERE DAY(mes) != 1"),
    ("presupuesto: categorías que existen en productos",
     "SELECT COUNT(*) FROM presupuesto WHERE categoria NOT IN (SELECT DISTINCT categoria FROM productos)"),
    ("stock: la semana es un lunes", "SELECT COUNT(*) FROM stock_semanal WHERE semana != DATE_TRUNC('week', semana)"),
    # Valores imposibles e importes que no cierran (decisión 85): con ellos, una suma sale mal sin ningún error
    ("ventas: neto = bruto − descuento", "SELECT COUNT(*) FROM ventas WHERE ABS(importe_neto - (importe_bruto - descuento)) > 0.01"),
    ("ventas: en una venta, descuento entre 0 y el bruto",
     "SELECT COUNT(*) FROM ventas WHERE tipo_movimiento = 'venta' AND (descuento < 0 OR descuento > importe_bruto)"),
    ("ventas: en una venta, unidades y costo positivos",
     "SELECT COUNT(*) FROM ventas WHERE tipo_movimiento = 'venta' AND (unidades <= 0 OR costo <= 0)"),
    ("stock: sin unidades negativas", "SELECT COUNT(*) FROM stock_semanal WHERE stock_unidades < 0"),
    ("presupuesto: importes positivos", "SELECT COUNT(*) FROM presupuesto WHERE importe_presupuesto <= 0"),
    ("productos: precio de lista positivo", "SELECT COUNT(*) FROM productos WHERE precio_lista <= 0"),
    ("promociones: termina después de empezar y descuento entre 0 y 100",
     "SELECT COUNT(*) FROM promociones WHERE fecha_hasta < fecha_desde OR descuento_pct <= 0 OR descuento_pct >= 100"),
]

# Lo raro que puede ser real o un error de carga: se avisa con ejemplos y no bloquea (decisión 85). Cada consulta
# devuelve filas de ejemplo. El umbral de cada salto depende del ruido de su serie (decisión 92, medido en
# evaluacion/pruebas/sensibilidad.py): el presupuesto y el costo unitario son muy estables, y con 1,5 veces sus vecinos ven un
# error del doble sin falsas alarmas (en dos años, solo 2 avisos más, los dos hechos reales: una apertura y un quiebre);
# las ventas de un día son ruidosas (con 1,5 serían 450 alarmas) y siguen con 3, el umbral del agente (decisión 84).
V = VECES_SOSPECHOSO
ESTABLE = 1.5
UMBRALES = {"presupuesto": ESTABLE, "costo": ESTABLE, "dia": V}
SOSPECHAS = [
    ("ventas: el costo por unidad de un producto salta contra sus meses vecinos", f"""
        WITH m AS (SELECT sku, DATE_TRUNC('month', fecha) AS mes, SUM(costo) / SUM(unidades) AS cu
                   FROM ventas WHERE tipo_movimiento = 'venta' GROUP BY 1, 2)
        SELECT sku, mes, cu / vecinos FROM (
            SELECT a.*, (SELECT MEDIAN(b.cu) FROM m b WHERE b.sku = a.sku AND b.mes <> a.mes
                         AND b.mes BETWEEN a.mes - INTERVAL 2 MONTH AND a.mes + INTERVAL 2 MONTH) AS vecinos FROM m a)
        WHERE cu / vecinos >= {ESTABLE} OR cu / vecinos <= {1 / ESTABLE}"""),
    ("ventas: las ventas de un día de una sucursal saltan contra el mismo día de las semanas vecinas", f"""
        WITH d AS (SELECT sucursal_id, fecha, SUM(importe_neto) AS x FROM ventas GROUP BY 1, 2)
        SELECT sucursal_id, fecha, x / vecinos FROM (
            SELECT a.*, (SELECT MEDIAN(b.x) FROM d b WHERE b.sucursal_id = a.sucursal_id AND b.fecha <> a.fecha
                         AND DAYOFWEEK(b.fecha) = DAYOFWEEK(a.fecha) AND b.fecha BETWEEN a.fecha - 28 AND a.fecha + 28)
                   AS vecinos FROM d a)
        WHERE x / vecinos >= {V} OR x / vecinos <= {1 / V}"""),
    ("ventas: días sin ventas de una sucursal abierta (¿carga incompleta?)", """
        SELECT s.sucursal_id, f.fecha FROM sucursales s
        JOIN fechas f ON f.fecha >= s.fecha_apertura AND f.fecha <= (SELECT MAX(fecha) FROM ventas)
        LEFT JOIN (SELECT DISTINCT sucursal_id, fecha FROM ventas) v ON v.sucursal_id = s.sucursal_id AND v.fecha = f.fecha
        WHERE v.fecha IS NULL"""),
    ("ventas: una fila con más de 50 veces las unidades habituales de su producto", """
        SELECT v.sucursal_id, v.fecha, v.sku, v.unidades FROM ventas v
        JOIN (SELECT sku, MEDIAN(unidades) AS med FROM ventas WHERE tipo_movimiento = 'venta' GROUP BY 1) m USING (sku)
        WHERE v.tipo_movimiento = 'venta' AND v.unidades > 50 * m.med"""),
    ("ventas: el bruto no es unidades × precio de lista", """
        SELECT v.fecha, v.sucursal_id, v.sku FROM ventas v JOIN productos p USING (sku)
        WHERE ABS(v.importe_bruto - v.unidades * p.precio_lista) > 0.01"""),
    ("ventas: un descuento sin promoción, o que no es el % de su promoción", """
        SELECT v.fecha, v.sucursal_id, v.sku FROM ventas v LEFT JOIN promociones pr USING (promocion_id)
        WHERE (v.descuento <> 0 AND v.promocion_id IS NULL)
           OR ABS(v.descuento - v.importe_bruto * pr.descuento_pct / 100) > 1"""),
    ("stock: una semana con más de 10 veces el stock habitual de su sucursal y producto", """
        SELECT st.sucursal_id, st.sku, st.semana FROM stock_semanal st
        JOIN (SELECT sucursal_id, sku, MEDIAN(stock_unidades) AS med FROM stock_semanal GROUP BY 1, 2) m USING (sucursal_id, sku)
        WHERE m.med > 0 AND st.stock_unidades > 10 * m.med"""),
    # Una foto que repite la anterior en todos los productos no pasa con stock real (en la base real y en el año
    # simulado, ninguna): es la de la semana anterior cargada otra vez (decisión 92). Puede ser real si la sucursal
    # no se movió en toda la semana, por eso avisa y no bloquea
    ("stock: una foto de una sucursal idéntica a la de la semana anterior", """
        WITH f AS (SELECT sucursal_id, semana, sku, stock_unidades FROM stock_semanal)
        SELECT a.sucursal_id, a.semana FROM f a JOIN f b ON b.sucursal_id = a.sucursal_id AND b.sku = a.sku AND b.semana = a.semana - 7
        GROUP BY 1, 2 HAVING COUNT(*) >= 50 AND COUNT(*) FILTER (WHERE a.stock_unidades <> b.stock_unidades) = 0"""),
    ("stock: semanas sin foto de una sucursal abierta", """
        SELECT s.sucursal_id, w.semana FROM sucursales s
        JOIN (SELECT DISTINCT semana FROM stock_semanal) w ON w.semana >= s.fecha_apertura  -- desde su primera semana completa
        LEFT JOIN (SELECT DISTINCT sucursal_id, semana FROM stock_semanal) st ON st.sucursal_id = s.sucursal_id AND st.semana = w.semana
        WHERE st.semana IS NULL"""),
    ("productos: un texto escrito como una orden para el asistente (decisión 57)", """
        SELECT sku, descripcion FROM productos
        WHERE REGEXP_MATCHES(LOWER(descripcion || ' ' || marca || ' ' || subcategoria),
                             'asistente|instrucci|ignor[aá]|prompt|respond[eé] que|system')"""),
]


def dato(x):
    """Un valor de un ejemplo, legible: la fecha sin la hora, los cocientes como «11,5 veces», los textos cortados."""
    if hasattr(x, "date") and callable(x.date):
        return str(x.date())
    if isinstance(x, float):
        return f"({x:.1f} veces)".replace(".", ",")
    return str(x)[:60]


def sospechas(con):
    """[(sospecha, cuántas, ejemplos)] de las que aparecen."""
    salida = []
    # Los más lejos de sus vecinos primero: son los más probables errores de carga
    presupuesto = sorted(celdas_de_presupuesto_sospechosas(con, ESTABLE), key=lambda c: -max(c[6], 1 / c[6]))
    if presupuesto:
        salida.append(("presupuesto: presupuesto ÷ ventas salta contra sus meses vecinos (decisión 84)", len(presupuesto),
                       [f"{a}-{m:02d} {s} {c} ({v:.1f} veces)".replace(".", ",") for a, m, s, c, _, _, v in presupuesto[:3]]))
    for nombre, sql in SOSPECHAS:
        filas = con.execute(sql).fetchall()
        if filas:
            salida.append((nombre, len(filas), [" ".join(dato(x) for x in f) for f in filas[:3]]))
    return salida


def avisos(con):
    """Lo que no es un error pero conviene saber: cuál es el último dato y si su mes está completo."""
    hasta, = con.execute("SELECT MAX(fecha) FROM ventas").fetchone()
    salida = [f"ventas hasta el {hasta}"]
    if con.execute("SELECT MONTH(? + INTERVAL 1 DAY) = MONTH(?)", [hasta, hasta]).fetchone()[0]:
        salida.append(f"el mes de {hasta} no está completo: el informe mensual de ese mes avisará que faltan datos")
    for tabla, columna in (("stock_semanal", "semana"), ("presupuesto", "mes")):
        ultimo, = con.execute(f"SELECT MAX({columna}) FROM {tabla}").fetchone()
        salida.append(f"{tabla} hasta el {ultimo}")
    return salida


def verificar(ruta=BASE):
    """[(control, filas con problema)] de cada control; 0 es que está bien."""
    resultados = []
    with duckdb.connect(ruta, read_only=True) as con:
        for tabla, prefijo, unida, alias, condicion in joins_del_esquema():
            # Las filas de la tabla que se pierden en este paso del join (las que no encuentran su par)
            columna_unida = re.search(rf"\b{alias}\.(\w+)", condicion).group(1)
            sql = f"SELECT COUNT(*) FROM {prefijo} LEFT JOIN {unida} {alias} ON {condicion} WHERE {alias}.{columna_unida} IS NULL"
            if alias == "u":  # une_con: los vacíos están permitidos (una venta sin promoción)
                origen = condicion.split(" = ")[0]
                sql = (f"SELECT COUNT(*) FROM {prefijo} WHERE {origen} IS NOT NULL AND {origen} NOT IN "
                       f"(SELECT {columna_unida} FROM {unida})")
            resultados.append((f"{tabla}: cada fila encuentra su {unida}", con.execute(sql).fetchone()[0]))
        for nombre, sql in CONTROLES:
            resultados.append((nombre, con.execute(sql).fetchone()[0]))
        return resultados, avisos(con), sospechas(con)


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else BASE
    resultados, notas, raras = verificar(ruta)
    for nombre, malas in resultados:
        print(f"{'✓' if malas == 0 else '✗'} {nombre}" + (f": {malas} filas con problema" if malas else ""))
    for nota in notas:
        print(f"· {nota}")
    if raras:
        print(f"\nAvisos: {len(raras)} cosas raras (pueden ser reales o un error de carga; no bloquean)")
    for nombre, cuantas, ejemplos in raras:
        print(f"⚠ {nombre}: {cuantas}. Por ejemplo: {' · '.join(ejemplos)}")
    errores = sum(1 for _, malas in resultados if malas)
    print(f"\n{len(resultados) - errores} de {len(resultados)} controles bien" + (f" · {len(raras)} avisos" if raras else ""))
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
