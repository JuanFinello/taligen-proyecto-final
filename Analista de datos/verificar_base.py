"""Verifica la base después de una ingesta de datos nuevos (decisión 63; guía: Data/base/INGESTA.md).
La base no declara claves foráneas: si una fila no calza en un join, el número sale mal sin ningún error. Este
script lo controla antes de que el agente o el informe programado usen la base.
Uso: .venv/bin/python verificar_base.py [ruta.duckdb]      (sale con código 1 si hay algún error)"""
import re
import sys

import duckdb
import yaml

from procesador_capa_semantica import BASE


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
]


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
        return resultados, avisos(con)


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else BASE
    resultados, notas = verificar(ruta)
    for nombre, malas in resultados:
        print(f"{'✓' if malas == 0 else '✗'} {nombre}" + (f": {malas} filas con problema" if malas else ""))
    for nota in notas:
        print(f"· {nota}")
    errores = sum(1 for _, malas in resultados if malas)
    print(f"\n{len(resultados) - errores} de {len(resultados)} controles bien")
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
