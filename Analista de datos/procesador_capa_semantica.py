"""Procesador de la capa semántica: arma el SQL desde medidas.yaml y esquema.yaml, lo corre y devuelve número + SQL."""
import re

import duckdb
import yaml

BASE = "Data/base/almacenes_del_sur.duckdb"
CAPA = "Data/capa_semantica"

with open(f"{CAPA}/medidas.yaml") as f:
    MEDIDAS_YAML = yaml.safe_load(f)
MEDIDAS = {m["id"]: m for m in MEDIDAS_YAML["medidas"]}
DERIVADAS = {m["id"]: m for m in MEDIDAS_YAML["medidas_derivadas"]}
with open(f"{CAPA}/esquema.yaml") as f:
    ESQUEMA = yaml.safe_load(f)


def ver_modelo():
    """Versión compacta para Haiku: lo que necesita para elegir medida y filtros. Sin fórmulas ni joins (decisión 3)."""
    # Variación y participación no son medidas: salen de comparar_con y agrupar_por (decisiones 11 y 29)
    medidas = [
        {"id": m["id"], "nombre": m["nombre"], "descripcion": m["descripcion"], "sinonimos": m["sinonimos"], "unidad": m["unidad"]}
        for m in [*MEDIDAS_YAML["medidas"], *(DERIVADAS[d] for d in CALCULADAS)]  # derivadas: solo las que se piden por id
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
        # Para consultar_sql (decisión 34): solo nombres de tablas y columnas, sin descripciones
        "tablas_para_sql": {tabla: list(datos["columnas"]) for tabla, datos in ESQUEMA["tablas"].items()},
    }


def condicion(columna, valor):
    """Un filtro en SQL: «columna = ?» para un valor, «columna IN (?, ?, …)» para una lista (decisión 23)."""
    if isinstance(valor, list):
        if not valor:
            raise ValueError(f"Lista de valores vacía para {columna}")
        return f"{columna} IN ({', '.join('?' * len(valor))})", valor
    return f"{columna} = ?", [valor]


def validar_valores(dimension, columna, valor):
    """Si algún valor del filtro no existe en la base, error con los válidos, para que Haiku corrija (decisión 25)."""
    alias, nombre_columna = columna.split(".")
    tabla = next(t for t, datos in ESQUEMA["tablas"].items() if datos["alias"] == alias)
    info = ESQUEMA["tablas"][tabla]["columnas"][nombre_columna]
    valores = valor if isinstance(valor, list) else [valor]

    if "valores" in info:  # pocos valores, listados en el esquema
        malos = [v for v in valores if v not in info["valores"]]
        validos = f"válidos: {', '.join(map(str, info['valores']))}"
    elif "rango" in info:  # números o fechas: tiene que caer dentro del rango
        desde, hasta = info["rango"]
        malos = [v for v in valores if not (str(desde) <= str(v) <= str(hasta) if isinstance(desde, str)
                                            else isinstance(v, (int, float)) and desde <= v <= hasta)]
        validos = f"rango válido: {desde} a {hasta}"
    else:  # muchos valores (códigos, nombres): se buscan en la base
        sql = f"SELECT DISTINCT {columna} FROM {tabla} {alias} WHERE {columna} IN ({', '.join('?' * len(valores))})"
        with duckdb.connect(BASE, read_only=True) as con:
            existentes = {fila[0] for fila in con.execute(sql, valores).fetchall()}
        malos = [v for v in valores if v not in existentes]
        validos = info["descripcion"]
        if malos and info.get("distintos", 0) <= 50:  # si son pocos, se listan todos
            with duckdb.connect(BASE, read_only=True) as con:
                todos = [fila[0] for fila in con.execute(f"SELECT DISTINCT {columna} FROM {tabla} {alias} ORDER BY 1").fetchall()]
            validos = f"válidos: {', '.join(map(str, todos))}"
    if malos:
        raise ValueError(f"Valor no válido para {dimension}: {', '.join(map(str, malos))}. {validos}")


def buscar_producto(texto, limite=20):
    """De un nombre a sus códigos (decisión 33): productos cuyo nombre o marca contienen todas las palabras del texto,
    sin importar mayúsculas ni tildes. Devuelve también el SQL, como calcular()."""
    palabras = [p for p in texto.lower().replace(",", " ").split() if p]
    if not palabras:
        raise ValueError("Texto de búsqueda vacío")
    condicion = " AND ".join("strip_accents(lower(p.descripcion || ' ' || p.marca)) LIKE '%' || strip_accents(?) || '%'"
                             for _ in palabras)
    sql = (f"SELECT p.sku, p.descripcion, p.marca, p.categoria, p.subcategoria, p.precio_lista\nFROM productos p\n"
           f"WHERE {condicion}\nORDER BY p.sku\nLIMIT {int(limite)}")
    with duckdb.connect(BASE, read_only=True) as con:
        columnas = ["sku", "descripcion", "marca", "categoria", "subcategoria", "precio_lista"]
        filas = [dict(zip(columnas, fila)) for fila in con.execute(sql, palabras).fetchall()]
    return {"texto": texto, "productos": filas, "sql": sql, "parametros": palabras}


MAX_FILAS_SQL = 100


def consultar_sql(sql):
    """SQL de solo lectura para lo que la capa no cubre (decisión 34): la base se abre en read_only, así que no se
    puede modificar. Devuelve hasta MAX_FILAS_SQL filas y avisa si hay más."""
    # read_only no alcanza: COPY ... TO igual escribe archivos y read_text lee los del disco. Sin acceso externo, no.
    with duckdb.connect(BASE, read_only=True, config={"enable_external_access": False}) as con:
        resultado = con.execute(sql)
        columnas = [c[0] for c in resultado.description] if resultado.description else []
        filas = resultado.fetchmany(MAX_FILAS_SQL + 1)
    filas = [dict(zip(columnas, (v if isinstance(v, (int, float, str, bool, type(None))) else str(v) for v in fila)))
             for fila in filas]
    return {"sql": sql, "columnas": columnas, "filas": filas[:MAX_FILAS_SQL], "truncado": len(filas) > MAX_FILAS_SQL}


def periodo(filtros):
    """Primer y último día que marcan los filtros de fecha (los que van a la tabla fechas, alias f), para que el
    modelo copie las fechas en vez de deducirlas (decisión 39). Sin filtros de fecha, None; si los días no son
    seguidos (por ejemplo, agosto de los dos años), no hay un rango que informar y "desde" va igual para comparables."""
    condiciones, parametros = [], []
    for dimension, valor in filtros.items():
        columna = ESQUEMA["dimensiones"].get(dimension, "")
        if columna.startswith("f."):
            sql, valores = condicion(columna, valor)
            condiciones.append(sql)
            parametros += valores
    sql = "SELECT MIN(f.fecha), MAX(f.fecha), COUNT(*) FROM fechas f"
    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)
    with duckdb.connect(BASE, read_only=True) as con:
        desde, hasta, dias = con.execute(sql, parametros).fetchone()
    seguido = desde is not None and (hasta - desde).days + 1 == dias
    return {"desde": desde, "hasta": hasta if seguido else None, "hay_filtro": bool(condiciones)}


def rango_de_fechas(filtros):
    """El período para la respuesta: solo si hay filtros de fecha y los días son seguidos."""
    p = periodo(filtros)
    if p["hay_filtro"] and p["hasta"]:
        return {"periodo": {"desde": str(p["desde"]), "hasta": str(p["hasta"])}}
    return {}


def variacion(m, actual, anterior):
    """Variación entre dos valores: en pp si la medida es un %, si no en % (None si falta un valor o el anterior es 0)."""
    if actual is None or anterior is None:
        return None
    if m["unidad"] == "%":
        return actual - anterior
    return (actual - anterior) / anterior * 100 if anterior else None


def comparar_por_grupo(m, medida, filtros, filtros_anterior, agrupar_por, orden, limite, hasta, total_actual, total_anterior):
    """Comparar y agrupar a la vez (decisión 28): por grupo, los dos valores, la variación y, si la medida es
    aditiva, la diferencia y su aporte a la diferencia total (qué parte de la suba o la caída explica)."""
    actual = calcular(medida, filtros, agrupar_por, abiertas_hasta=hasta)
    anterior = calcular(medida, filtros_anterior, agrupar_por, abiertas_hasta=hasta)
    clave = lambda fila: tuple(fila[d] for d in agrupar_por)
    actuales = {clave(f): f["valor"] for f in actual["filas"]}
    anteriores = {clave(f): f["valor"] for f in anterior["filas"]}
    diferencia_total = (total_actual or 0) - (total_anterior or 0)

    filas = []
    for grupo in [*actuales, *(g for g in anteriores if g not in actuales)]:  # también los que solo están en un período
        a, b = actuales.get(grupo), anteriores.get(grupo)
        fila = {**dict(zip(agrupar_por, grupo)), "actual": a, "anterior": b, "variacion": variacion(m, a, b)}
        if m.get("aditiva"):  # un grupo que no estaba en un período cuenta como 0 en ese período
            fila["diferencia"] = (a or 0) - (b or 0)
            fila["aporte_pct"] = fila["diferencia"] / diferencia_total * 100 if diferencia_total else None
        filas.append(fila)

    # Si subas y caídas se compensan, el total casi no se mueve y el aporte se dispara (decisión 38):
    # con la diferencia neta por debajo del 10 % de lo que se movieron los grupos, el aporte no se informa
    aviso = None
    movimiento = sum(abs(f["diferencia"]) for f in filas) if m.get("aditiva") else 0
    if movimiento and abs(diferencia_total) < 0.1 * movimiento:
        for fila in filas:
            fila["aporte_pct"] = None
        aviso = ("Subas y caídas de los grupos se compensan y el total casi no cambia: el aporte no tiene sentido. "
                 "Explicá con la diferencia de cada grupo (quién subió y quién cayó).")

    # Se ordena por diferencia si la medida es aditiva (lo que más explica), si no por variación; los vacíos, al final
    criterio = "diferencia" if m.get("aditiva") else "variacion"
    filas.sort(key=lambda f: (f[criterio] is None, -(f[criterio] or 0) if orden == "desc" else (f[criterio] or 0)))
    if limite:
        filas = filas[:int(limite)]
    return {"filas": filas, "ordenado_por": criterio, **({"aviso": aviso} if aviso else {}),
            "sql": {"actual": actual["sql"], "anterior": anterior["sql"]},
            "parametros": {"actual": actual["parametros"], "anterior": anterior["parametros"]}}


def desvio_presupuesto(filtros, agrupar_por, orden, limite, comparar_con=None, comparables=False):
    """Desvío contra presupuesto (decisión 30): ventas_netas y presupuesto con los mismos filtros, y el % lo hace el código."""
    if comparar_con or comparables:
        raise ValueError("desvio_presupuesto_pct todavía no se puede comparar entre períodos")
    for dimension in [*filtros, *agrupar_por]:
        if dimension in ("fecha", "semana"):
            raise ValueError("El presupuesto es mensual: el desvío se pide por mes o por períodos más largos, no por fecha ni semana")
    presupuesto = calcular("presupuesto", filtros, agrupar_por)  # primero: rechaza lo que el presupuesto no tiene (producto…)
    ventas = calcular("ventas_netas", filtros, agrupar_por)
    desvio = lambda v, p: (v - p) / p * 100 if v is not None and p else None
    base = {"medida": "desvio_presupuesto_pct", "filtros": filtros, **rango_de_fechas(filtros), "unidad": "%",
            "sql": {"ventas_netas": ventas["sql"], "presupuesto": presupuesto["sql"]},
            "parametros": {"ventas_netas": ventas["parametros"], "presupuesto": presupuesto["parametros"]}}
    if not agrupar_por:
        v, p = ventas["valor"], presupuesto["valor"]
        return {**base, "valor": desvio(v, p), "ventas_netas": v, "presupuesto": p, "diferencia": None if v is None or p is None else v - p}

    clave = lambda fila: tuple(fila[d] for d in agrupar_por)
    vendido = {clave(f): f["valor"] for f in ventas["filas"]}
    filas = []
    for fila in presupuesto["filas"]:
        v, p = vendido.get(clave(fila)), fila["valor"]
        filas.append({**{d: fila[d] for d in agrupar_por}, "valor": desvio(v, p), "ventas_netas": v, "presupuesto": p,
                      "diferencia": None if v is None else v - p})
    filas.sort(key=lambda f: (f["valor"] is None, -(f["valor"] or 0) if orden == "desc" else (f["valor"] or 0)))
    total = {"valor": desvio(ventas["total"], presupuesto["total"]), "ventas_netas": ventas["total"], "presupuesto": presupuesto["total"]}
    return {**base, "filas": filas[:int(limite)] if limite else filas, "total": total}


def efectos(p0, c0, p1, c1):
    """Margen % = 1 - c/p (c = costo por unidad, p = precio promedio). La variación se separa en dos pasos que
    suman exacto: primero cambia el precio con el costo de antes, después cambia el costo con el precio nuevo."""
    if None in (p0, c0, p1, c1) or not p0 or not p1:
        return {"margen_pct_anterior": None, "margen_pct_actual": None, "variacion_pp": None,
                "efecto_precio_pp": None, "efecto_costo_pp": None}
    anterior, actual = (1 - c0 / p0) * 100, (1 - c1 / p1) * 100
    return {"margen_pct_anterior": anterior, "margen_pct_actual": actual, "variacion_pp": actual - anterior,
            "efecto_precio_pp": (c0 / p0 - c0 / p1) * 100, "efecto_costo_pp": (c0 - c1) / p1 * 100,
            "precio_anterior": p0, "precio_actual": p1, "costo_unitario_anterior": c0, "costo_unitario_actual": c1,
            # Cuánto subió cada uno en %: si no viene, Haiku lo calcula (decisión 50)
            "variacion_precio_pct": (p1 / p0 - 1) * 100, "variacion_costo_unitario_pct": (c1 / c0 - 1) * 100 if c0 else None}


def efectos_margen(filtros, agrupar_por, orden, limite, comparar_con=None, comparables=False):
    """Efecto precio y efecto costo de la variación del margen % (decisión 43): compara precio_promedio y
    costo_unitario entre los dos períodos con las mismas reglas que cualquier comparación, y la cuenta la hace el código."""
    if not comparar_con:
        raise ValueError("efectos_margen compara dos períodos: necesita comparar_con (por ejemplo {\"anio_fiscal\": 2025})")
    precio = calcular("precio_promedio", filtros, agrupar_por, comparar_con=comparar_con, comparables=comparables)
    costo = calcular("costo_unitario", filtros, agrupar_por, comparar_con=comparar_con, comparables=comparables)
    # Un SQL por medida y período, con la misma forma que el resto (lo usan las trazas y el anexo)
    sql, parametros = {}, {}
    for nombre, r in (("precio_promedio", precio), ("costo_unitario", costo)):
        for parte, texto, params in sqls(r):
            sql[f"{nombre} {parte.rstrip(': ')}"] = texto
            parametros[f"{nombre} {parte.rstrip(': ')}"] = params
    base = {"medida": "efectos_margen", "unidad": "pp", "filtros": filtros, "comparar_con": comparar_con,
            "comparables": comparables, "abiertas_hasta": precio["abiertas_hasta"],
            "periodo": precio["actual"].get("periodo"), "periodo_anterior": precio["anterior"].get("periodo"),
            "nota": "Los dos efectos suman la variación. Usan promedios: un cambio de mix (qué se vende) queda dentro de ellos.",
            "sql": sql, "parametros": parametros}
    total = efectos(precio["anterior"]["valor"], costo["anterior"]["valor"], precio["actual"]["valor"], costo["actual"]["valor"])
    if not agrupar_por:
        return {**base, **total}

    clave = lambda fila: tuple(fila[d] for d in agrupar_por)
    costos = {clave(f): f for f in costo["filas"]}
    filas = []
    for fila in precio["filas"]:
        c = costos.get(clave(fila), {})
        filas.append({**{d: fila[d] for d in agrupar_por},
                      **efectos(fila["anterior"], c.get("anterior"), fila["actual"], c.get("actual"))})
    filas.sort(key=lambda f: (f["variacion_pp"] is None,
                              -(f["variacion_pp"] or 0) if orden == "desc" else (f["variacion_pp"] or 0)))
    return {**base, "filas": filas[:int(limite)] if limite else filas, "total": total}


# Medidas derivadas que se piden por id; cada una la calcula su función (las demás salen de parámetros de calcular)
CALCULADAS = {"desvio_presupuesto_pct": desvio_presupuesto, "efectos_margen": efectos_margen}


def sqls(resultado):
    """Los SQL de un resultado con sus parámetros: uno, o uno por parte (actual/anterior, ventas/presupuesto).
    La usan las trazas del agente y el anexo de los informes."""
    sql, parametros = resultado.get("sql"), resultado.get("parametros")
    if sql is None and isinstance(resultado.get("actual"), dict):  # comparación sin agrupar: un SQL por período
        return [(f"{parte}: ", resultado[parte]["sql"], resultado[parte]["parametros"]) for parte in ("actual", "anterior")]
    if isinstance(sql, dict):
        return [(f"{parte}: ", texto, (parametros or {}).get(parte)) for parte, texto in sql.items()]
    return [("", sql, parametros)] if sql else []


def calcular(medida, filtros=None, agrupar_por=None, orden="desc", limite=None, comparar_con=None,
             comparables=False, abiertas_hasta=None):
    """Calcula una medida con filtros: un valor (columna = valor) o una lista (columna IN lista).
    Sin agrupar_por devuelve un valor; con agrupar_por (lista de dimensiones), una fila por grupo ordenada por el valor.
    Con comparar_con (solo los filtros que cambian), calcula también el período anterior y la variación.
    Con comparables=True, los dos períodos usan solo las sucursales abiertas al inicio del anterior.
    abiertas_hasta no lo pasa el modelo: lo pone comparables."""
    filtros = filtros or {}
    agrupar_por = agrupar_por or []
    if medida in CALCULADAS:
        if orden not in ("desc", "asc"):
            raise ValueError(f"Orden inválido: {orden}")
        return CALCULADAS[medida](filtros, agrupar_por, orden, limite, comparar_con, comparables)
    if medida not in MEDIDAS:
        raise ValueError(f"Medida desconocida: {medida}")
    m = MEDIDAS[medida]
    if "tabla" not in m:
        raise ValueError(f"{medida} es una medida derivada: todavía no se calcula")
    if orden not in ("desc", "asc"):
        raise ValueError(f"Orden inválido: {orden}")

    # Paso 1: comparar dos períodos (decisión 11). El anterior copia los filtros y cambia solo lo de comparar_con
    if comparables and not comparar_con:
        raise ValueError("comparables=True necesita comparar_con")
    if comparar_con:
        filtros_anterior = {**filtros, **comparar_con}
        # Comparables (decisión 12): sucursales con fecha_apertura <= primer día del período anterior
        hasta = periodo(filtros_anterior)["desde"] if comparables else None
        actual = calcular(medida, filtros, abiertas_hasta=hasta)
        anterior = calcular(medida, filtros_anterior, abiertas_hasta=hasta)
        resultado = {"medida": medida, "unidad": m["unidad"], "actual": actual, "anterior": anterior,
                     "variacion": variacion(m, actual["valor"], anterior["valor"]),
                     "unidad_variacion": "pp" if m["unidad"] == "%" else "%",
                     "comparables": comparables, "abiertas_hasta": hasta}
        if m.get("aditiva") and None not in (actual["valor"], anterior["valor"]):
            # La diferencia en la unidad de la medida (pesos, unidades): si no viene, Haiku la resta (decisión 50)
            resultado["diferencia"] = actual["valor"] - anterior["valor"]
        if agrupar_por:
            resultado.update(comparar_por_grupo(m, medida, filtros, filtros_anterior, agrupar_por, orden, limite, hasta,
                                                actual["valor"], anterior["valor"]))
        return resultado

    # Paso 2: el join completo de la tabla (decisión 9)
    # Una tabla de dimensión (por ejemplo, sucursales) no tiene join: va sola con su alias
    tabla = ESQUEMA["tablas"][m["tabla"]]
    join = tabla["join"] or f"{m['tabla']} {tabla['alias']}"

    # Columna de cada dimensión: la propia de la tabla si la declara (decisión 22), si no la del mapa general
    columna_de = {**ESQUEMA["dimensiones"], **tabla.get("dimensiones_propias", {})}

    # Solo sirven las dimensiones cuya tabla está en el join (alias = la palabra después de cada nombre de tabla)
    alias_del_join = set(re.findall(r"(?:^|JOIN )\w+ (\w+)", join))
    validas = [d for d, c in columna_de.items() if c.split(".")[0] in alias_del_join]
    for dimension in [*filtros, *agrupar_por]:
        if dimension in columna_de and dimension not in validas:
            raise ValueError(f"La dimensión {dimension} no se puede usar con {medida}. "
                             f"Dimensiones válidas para {medida}: {', '.join(validas)}")

    # Paso 3: cada filtro va a su columna; el valor, como parámetro
    condiciones, parametros = [], []
    for dimension, valor in filtros.items():
        if dimension not in columna_de:
            raise ValueError(f"Dimensión desconocida: {dimension}")
        validar_valores(dimension, columna_de[dimension], valor)
        sql, valores = condicion(columna_de[dimension], valor)
        condiciones.append(sql)
        parametros += valores
    if abiertas_hasta:
        condiciones.append("s.fecha_apertura <= ?")
        parametros.append(abiertas_hasta)

    # Paso 4: cada dimensión de agrupar_por va a su columna (decisión 10)
    columnas = []
    for dimension in agrupar_por:
        if dimension not in columna_de:
            raise ValueError(f"Dimensión desconocida: {dimension}")
        columnas.append(columna_de[dimension])

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
            return {"medida": medida, "filtros": filtros, **rango_de_fechas(filtros), "valor": valor, "unidad": m["unidad"],
                    "sql": sql, "parametros": parametros}
        filas = [dict(zip(agrupar_por + ["valor"], fila)) for fila in resultado.fetchall()]
    respuesta = {"medida": medida, "filtros": filtros, **rango_de_fechas(filtros), "filas": filas, "unidad": m["unidad"],
                 "sql": sql, "parametros": parametros}

    # Participación (decisión 29): solo en medidas aditivas, sobre el total real (con los mismos filtros, sin limite)
    if m.get("aditiva"):
        total = calcular(medida, filtros, abiertas_hasta=abiertas_hasta)
        for fila in filas:
            fila["participacion_pct"] = fila["valor"] / total["valor"] * 100 if total["valor"] and fila["valor"] is not None else None
        respuesta.update({"total": total["valor"], "sql_total": total["sql"]})
    return respuesta
