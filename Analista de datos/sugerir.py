"""La pregunta siguiente (decisión 86, «lo que sube la vara»): después de cada respuesta, 2 o 3 preguntas para seguir.
Como Tableau Pulse, salen del resultado y no de un modelo: el código mira la última consulta y propone los pasos
típicos de un analista (los operadores de la literatura de OLAP): comparar con el período anterior, pasar a
comparables, bajar un nivel (región → sucursal, categoría → subcategoría) y buscar la causa del grupo que más cayó.
Solo combina medidas y dimensiones de la capa, así que toda sugerencia se puede responder; no cuesta nada."""
from datetime import date

import duckdb

from explicar import MESES
from graficos import NOMBRES
from procesador_capa_semantica import BASE, COBERTURA, dimensiones_validas

MAXIMO = 3
# Bajar un nivel: el que sigue a lo que ya se filtró; si no se filtró nada, el primero que la medida admita
SIGUIENTE = {"region": "sucursal", "categoria": "subcategoria", "subcategoria": "producto", "producto": "region",
             "sucursal": "categoria", "proveedor": "categoria"}
# Mirar al primero de un ranking por otra dimensión: dónde se vende un producto, qué vende una sucursal
DEL_PRIMERO = {"producto": "region", "sucursal": "categoria", "region": "sucursal", "categoria": "subcategoria",
               "subcategoria": "producto", "proveedor": "categoria", "marca": "region", "formato": "region"}
DE_ENTRADA = ["categoria", "region"]
NOMBRE = {"region": "región", "sucursal": "sucursal", "categoria": "categoría", "subcategoria": "subcategoría",
          "producto": "producto", "proveedor": "proveedor", "marca": "marca", "formato": "formato"}
DESDE = date.fromisoformat(COBERTURA["ventas_desde"])
with duckdb.connect(BASE, read_only=True) as _con:
    PRODUCTOS = dict(_con.execute("SELECT sku, descripcion FROM productos").fetchall())


def con_nombre(codigo):
    """«S02 (Los Ceibos)», «P0185 (Jabón en polvo Espuma Clara 800 g)»: el código solo no se entiende."""
    nombre = NOMBRES.get(str(codigo)) or PRODUCTOS.get(str(codigo))
    return f"{codigo} ({nombre[:45]})" if nombre else str(codigo)


def corto(filtros):
    """El período de los filtros, en corto: «el AF2026», «el T2 del AF2026», «marzo de 2026», «2025»."""
    af, anio, mes = filtros.get("anio_fiscal"), filtros.get("anio"), filtros.get("mes")
    if isinstance(af, int):
        if isinstance(filtros.get("trimestre_fiscal"), int):
            return f"el T{filtros['trimestre_fiscal']} del AF{af}"
        return f"el AF{af}"
    if isinstance(anio, int) and isinstance(mes, int):
        return f"{MESES[mes - 1]} de {anio}"
    if isinstance(anio, int) and "mes" not in filtros:
        return str(anio)
    return None


def anterior(filtros):
    """Los filtros que cambian para el mismo período un año antes, si ese período está en la base."""
    af, anio, mes = filtros.get("anio_fiscal"), filtros.get("anio"), filtros.get("mes")
    if isinstance(af, int):
        return {"anio_fiscal": af - 1} if date(af - 2, 5, 1) >= DESDE else None
    if isinstance(anio, int) and isinstance(mes, int):
        return {"anio": anio - 1} if date(anio - 1, mes, 1) >= DESDE else None
    if isinstance(anio, int) and "mes" not in filtros:
        return {"anio": anio - 1} if date(anio - 1, 1, 1) >= DESDE else None
    return None


def de(filtros):
    """« de Perfumería en el Sur»: los filtros que no son de período, para el texto."""
    partes = [con_nombre(filtros[d]) for d in ("producto", "categoria", "subcategoria", "region", "sucursal", "proveedor")
              if isinstance(filtros.get(d), (str, int))]
    return f" de {' en '.join(partes)}" if partes else ""


def grupo_que_mas_cayo(resultado, dimension):
    """El grupo con la peor variación, si cayó y le fue peor que al total."""
    filas = [f for f in resultado.get("filas", []) if isinstance(f.get("variacion"), (int, float))]
    if not filas:
        return None
    peor = min(filas, key=lambda f: f["variacion"])
    total = resultado.get("variacion")
    if peor["variacion"] < 0 and (not isinstance(total, (int, float)) or peor["variacion"] < total):
        return peor.get(dimension)
    return None


def sugerencias(respuesta):
    """Hasta MAXIMO preguntas para seguir. Mira la última consulta de calcular y, para no sugerir lo que ya se hizo,
    todas las de la respuesta (el agente suele hacer la total y la comparable)."""
    if respuesta.get("ruta") != "agente" or respuesta.get("tipo") == "sin_dato":
        return []  # sin dato: sugerir otra medida sería responder con otra cosa. Una ambigua sí: el agente ya eligió
                   # una lectura y respondió con ella (y si no consultó nada, abajo no hay de dónde sugerir)
    consultas = [c for c in respuesta.get("consultas", []) if c["tool"] == "calcular"]
    if not consultas:
        return []
    a, r = consultas[-1]["argumentos"], consultas[-1]["resultado"]
    medida, filtros = a.get("medida"), a.get("filtros") or {}
    # Abrir por una dimensión que ya está filtrada en un valor da un solo grupo: no cuenta como abierto
    agrupar = [d for d in a.get("agrupar_por") or [] if not d.startswith("nombre_") and not isinstance(filtros.get(d), (str, int))]
    if len(r.get("filas") or []) < 2:  # un solo grupo (el proveedor de un producto) no es un corte
        agrupar = []
    comparo = any(c["argumentos"].get("comparar_con") for c in consultas)
    comparables = any(c["argumentos"].get("comparables") for c in consultas)
    # Una caída sin abrir (la comparable, si la hay: es la que dice si las mismas sucursales vienen peor)
    cayo = next((c for c in reversed(consultas) if c["argumentos"].get("comparar_con")
                 and not c["argumentos"].get("agrupar_por") and isinstance(c["resultado"].get("variacion"), (int, float))
                 and c["resultado"]["variacion"] < 0), None)
    periodo, validas = corto(filtros), dimensiones_validas(medida)
    nombre = {"ventas_netas": "las ventas", "unidades": "las unidades", "margen_bruto": "el margen bruto",
              "margen_pct": "el margen", "desvio_presupuesto_pct": "el desvío contra presupuesto"}.get(medida)
    if not periodo or not nombre:
        return []
    plural = nombre.startswith("las")
    abre, vino = ("se abren", "vinieron") if plural else ("se abre", "vino")
    salida = []

    # 1. La causa: un grupo que cae más que el total (eso es un diagnóstico: la puerta lo manda al coordinador)
    if agrupar and a.get("comparar_con") and (grupo := grupo_que_mas_cayo(r, agrupar[0])):
        salida.append(f"¿Qué explica la caída de {con_nombre(grupo)} en {nombre.split(' ', 1)[1]} en {periodo}?")
        hijo = SIGUIENTE.get(agrupar[0])
        if hijo in validas:
            salida.append(f"¿Cómo {abre} {nombre} de {con_nombre(grupo)} por {NOMBRE[hijo]} en {periodo}?")
    elif cayo:
        en_comparables = " en sucursales comparables" if cayo["argumentos"].get("comparables") else ""
        salida.append(f"¿Qué explica la caída de {nombre}{de(filtros)}{en_comparables} en {periodo}?")
    # 1b. Un ranking (abierto y sin comparar): mirar al primero por otra dimensión
    if agrupar and not a.get("comparar_con") and r.get("filas"):
        primero, otra = r["filas"][0].get(agrupar[0]), DEL_PRIMERO.get(agrupar[0])
        if primero is not None and otra in validas and otra not in filtros:
            salida.append(f"¿Cómo {abre} {nombre} de {con_nombre(primero)} por {NOMBRE[otra]} en {periodo}?")
    # 2. El desvío con presupuesto sospechoso (decisión 84): mirar los meses vecinos
    if medida == "desvio_presupuesto_pct" and r.get("aviso") and isinstance(filtros.get("mes"), int):
        mes, anio = filtros["mes"], filtros.get("anio")
        antes = (MESES[(mes - 2) % 12], anio - 1 if mes == 1 else anio)
        despues = (MESES[mes % 12], anio + 1 if mes == 12 else anio)
        salida.append(f"¿Cuál fue {nombre}{de(filtros)} en {antes[0]} de {antes[1]} y en {despues[0]} de {despues[1]}?")
    # 3. Comparar con el año anterior
    if not comparo and medida != "desvio_presupuesto_pct" and (previo := anterior(filtros)):
        salida.append(f"¿Cómo {vino} {nombre}{de(filtros)} en {periodo} "
                      f"contra {corto({**filtros, **previo})}?")
    # 4. Comparables: las ventas de dos períodos con todas las sucursales (S39 y S40 abrieron en el medio)
    if comparo and not comparables and medida in ("ventas_netas", "unidades"):
        salida.append("¿Y en sucursales comparables, las que estaban abiertas en los dos períodos?")
    # 5. El margen: ¿precio o costo?
    if medida == "margen_pct" and a.get("comparar_con"):
        salida.append(f"¿El cambio del margen{de(filtros)} en {periodo} fue por precio o por costo?")
    # 6. Bajar un nivel
    if not agrupar:
        ya = [SIGUIENTE[d] for d in SIGUIENTE if d in filtros and isinstance(filtros[d], str)]
        hijo = next((d for d in ya + DE_ENTRADA if d in validas and d not in filtros), None)
        if hijo:
            salida.append(f"¿Cómo {abre} {nombre}{de(filtros)} por {NOMBRE[hijo]} en {periodo}?")
    return list(dict.fromkeys(salida))[:MAXIMO]
