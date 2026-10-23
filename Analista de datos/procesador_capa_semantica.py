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


def calcular(medida, filtros=None):
    """Calcula una medida con filtros simples (columna = valor). Devuelve valor, SQL y parámetros."""
    filtros = filtros or {}
    if medida not in MEDIDAS:
        raise ValueError(f"Medida desconocida: {medida}")
    m = MEDIDAS[medida]
    if "tabla" not in m:
        raise ValueError(f"{medida} es una medida derivada: todavía no se calcula")

    # Paso 2: el join completo de la tabla (decisión 9)
    join = ESQUEMA["tablas"][m["tabla"]]["join"]

    # Paso 3: cada filtro va a su columna; el valor, como parámetro
    condiciones, parametros = [], []
    for dimension, valor in filtros.items():
        if dimension not in ESQUEMA["dimensiones"]:
            raise ValueError(f"Dimensión desconocida: {dimension}")
        condiciones.append(f"{ESQUEMA['dimensiones'][dimension]} = ?")
        parametros.append(valor)

    sql = f"SELECT {m['formula']}\nFROM {join}"
    if condiciones:
        sql += "\nWHERE " + " AND ".join(condiciones)

    # Paso 4: ejecutar en solo lectura
    with duckdb.connect(BASE, read_only=True) as con:
        valor = con.execute(sql, parametros).fetchone()[0]
    return {"medida": medida, "valor": valor, "unidad": m["unidad"], "sql": sql, "parametros": parametros}
