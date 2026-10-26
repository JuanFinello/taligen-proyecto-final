"""Procesador de la capa semántica: arma el SQL desde medidas.yaml y esquema.yaml, lo corre y devuelve número + SQL."""
import duckdb
import yaml

BASE = "Data/base/almacenes_del_sur.duckdb"
CAPA = "Data/capa_semantica"

with open(f"{CAPA}/medidas.yaml") as f:
    MEDIDAS_YAML = yaml.safe_load(f)
MEDIDAS = {m["id"]: m for m in MEDIDAS_YAML["medidas"]}
with open(f"{CAPA}/esquema.yaml") as f:
    ESQUEMA = yaml.safe_load(f)


def ver_modelo():
    """Versión compacta para Haiku: lo que necesita para elegir medida y filtros. Sin fórmulas ni joins (decisión 3)."""
    # Las derivadas (variaciones, desvío) se suman cuando calcular() las sepa hacer (pieza 2)
    medidas = [
        {"id": m["id"], "nombre": m["nombre"], "sinonimos": m["sinonimos"], "unidad": m["unidad"]}
        for m in MEDIDAS_YAML["medidas"]
    ]

    # Para cada dimensión, busca su columna en el esquema y copia los valores válidos (o el rango)
    tabla_de_alias = {datos["alias"]: tabla for tabla, datos in ESQUEMA["tablas"].items()}
    dimensiones = {}
    for dimension, columna in ESQUEMA["dimensiones"].items():
        alias, nombre_columna = columna.split(".")
        info = ESQUEMA["tablas"][tabla_de_alias[alias]]["columnas"][nombre_columna]
        dimensiones[dimension] = {k: info[k] for k in ("valores", "rango") if k in info}

    return {
        "medidas": medidas,
        "dimensiones": dimensiones,
        "nota_dimensiones": ESQUEMA["nota_dimensiones"],
        "reglas": MEDIDAS_YAML["reglas"],
    }


def inicio_del_periodo(filtros):
    """Primer día del período que marcan los filtros de fecha (los que van a la tabla fechas, alias f)."""
    condiciones, parametros = [], []
    for dimension, valor in filtros.items():
        columna = ESQUEMA["dimensiones"].get(dimension, "")
        if columna.startswith("f."):
            condiciones.append(f"{columna} = ?")
            parametros.append(valor)
    sql = "SELECT MIN(f.fecha) FROM fechas f"
    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)
    with duckdb.connect(BASE, read_only=True) as con:
        return con.execute(sql, parametros).fetchone()[0]


def calcular(medida, filtros=None, agrupar_por=None, orden="desc", limite=None, comparar_con=None,
             comparables=False, abiertas_hasta=None):
    """Calcula una medida con filtros simples (columna = valor).
    Sin agrupar_por devuelve un valor; con agrupar_por (lista de dimensiones), una fila por grupo ordenada por el valor.
    Con comparar_con (solo los filtros que cambian), calcula también el período anterior y la variación.
    Con comparables=True, los dos períodos usan solo las sucursales abiertas al inicio del anterior.
    abiertas_hasta no lo pasa el modelo: lo pone comparables."""
    filtros = filtros or {}
    agrupar_por = agrupar_por or []
    if medida not in MEDIDAS:
        raise ValueError(f"Medida desconocida: {medida}")
    m = MEDIDAS[medida]
    if "tabla" not in m:
        raise ValueError(f"{medida} es una medida derivada: todavía no se calcula")

    # Paso 1: comparar dos períodos (decisión 11). El anterior copia los filtros y cambia solo lo de comparar_con
    if comparables and not comparar_con:
        raise ValueError("comparables=True necesita comparar_con")
    if comparar_con:
        if agrupar_por:
            raise ValueError("Todavía no se puede comparar y agrupar a la vez")
        filtros_anterior = {**filtros, **comparar_con}
        # Comparables (decisión 12): sucursales con fecha_apertura <= primer día del período anterior
        hasta = inicio_del_periodo(filtros_anterior) if comparables else None
        actual = calcular(medida, filtros, abiertas_hasta=hasta)
        anterior = calcular(medida, filtros_anterior, abiertas_hasta=hasta)
        if m["unidad"] == "%":
            variacion, unidad_variacion = actual["valor"] - anterior["valor"], "pp"
        else:
            variacion, unidad_variacion = (actual["valor"] - anterior["valor"]) / anterior["valor"] * 100, "%"
        return {"medida": medida, "unidad": m["unidad"], "actual": actual, "anterior": anterior,
                "variacion": variacion, "unidad_variacion": unidad_variacion,
                "comparables": comparables, "abiertas_hasta": hasta}

    # Paso 2: el join completo de la tabla (decisión 9)
    # Una tabla de dimensión (por ejemplo, sucursales) no tiene join: va sola con su alias
    tabla = ESQUEMA["tablas"][m["tabla"]]
    join = tabla["join"] or f"{m['tabla']} {tabla['alias']}"

    # Paso 3: cada filtro va a su columna; el valor, como parámetro
    condiciones, parametros = [], []
    for dimension, valor in filtros.items():
        if dimension not in ESQUEMA["dimensiones"]:
            raise ValueError(f"Dimensión desconocida: {dimension}")
        condiciones.append(f"{ESQUEMA['dimensiones'][dimension]} = ?")
        parametros.append(valor)
    if abiertas_hasta:
        condiciones.append("s.fecha_apertura <= ?")
        parametros.append(abiertas_hasta)

    # Paso 4: cada dimensión de agrupar_por va a su columna (decisión 10)
    columnas = []
    for dimension in agrupar_por:
        if dimension not in ESQUEMA["dimensiones"]:
            raise ValueError(f"Dimensión desconocida: {dimension}")
        columnas.append(ESQUEMA["dimensiones"][dimension])
    if orden not in ("desc", "asc"):
        raise ValueError(f"Orden inválido: {orden}")

    seleccion = [f"{c} AS {d}" for c, d in zip(columnas, agrupar_por)] + [f"{m['formula']} AS valor"]
    sql = f"SELECT {', '.join(seleccion)}\nFROM {join}"
    if condiciones:
        sql += "\nWHERE " + " AND ".join(condiciones)
    if columnas:
        sql += f"\nGROUP BY {', '.join(columnas)}\nORDER BY valor {orden.upper()}"
        if limite:
            sql += f"\nLIMIT {int(limite)}"

    # Paso 5: ejecutar en solo lectura
    with duckdb.connect(BASE, read_only=True) as con:
        resultado = con.execute(sql, parametros)
        if not columnas:
            valor = resultado.fetchone()[0]
            return {"medida": medida, "filtros": filtros, "valor": valor, "unidad": m["unidad"], "sql": sql, "parametros": parametros}
        filas = [dict(zip(agrupar_por + ["valor"], fila)) for fila in resultado.fetchall()]
    return {"medida": medida, "filtros": filtros, "filas": filas, "unidad": m["unidad"], "sql": sql, "parametros": parametros}
