"""La pregunta siguiente (decisión 86, «lo que sube la vara»): después de cada respuesta, 2 o 3 preguntas para seguir.
Como Tableau Pulse, salen del resultado y no de un modelo: el código mira la última consulta y propone los pasos
típicos de un analista (los operadores de la literatura de OLAP): comparar con el período anterior, pasar a
comparables, bajar un nivel (región → sucursal, categoría → subcategoría) y buscar la causa del grupo que más cayó.
Solo combina medidas y dimensiones de la capa, así que toda sugerencia se puede responder; no cuesta nada.
Con memoria de la conversación (decisión 121): no repite una sugerencia ya mostrada ni una pregunta ya hecha, y pone
primero los pasos que menos se propusieron."""
from datetime import date

import duckdb

from explicar import MESES
from graficos import NOMBRES
from controles import sin_tildes
from procesador_capa_semantica import BASE, COBERTURA, dimensiones_validas, ver_modelo

MAXIMO = 3
# Bajar un nivel: el que sigue a lo que ya se filtró; si no se filtró nada, el primero que la medida admita
SIGUIENTE = {"region": "sucursal", "categoria": "subcategoria", "subcategoria": "producto", "producto": "region",
             "sucursal": "categoria", "proveedor": "categoria"}
# Mirar al primero de un ranking por otra dimensión: dónde se vende un producto, qué vende una sucursal. En orden: si la
# primera ya está filtrada (el producto que más vende en el Sur), la siguiente (por sucursal del Sur)
DEL_PRIMERO = {"producto": ["region", "sucursal"], "sucursal": ["categoria", "subcategoria"],
               "region": ["sucursal", "categoria"], "categoria": ["subcategoria", "region"],
               "subcategoria": ["producto", "region"], "proveedor": ["categoria", "region"], "marca": ["region", "sucursal"],
               "formato": ["region", "sucursal"]}
# Cruzar con otra medida, el paso que sigue a «cuánto vendió»: con qué margen (y al revés)
CRUCE = {"ventas_netas": "margen_pct", "unidades": "ventas_netas", "margen_pct": "ventas_netas",
         "margen_bruto": "ventas_netas", "tasa_quiebre_pct": "ventas_netas", "stock_promedio": "ventas_netas",
         "descuentos": "ventas_netas", "precio_promedio": "unidades", "presupuesto": "ventas_netas"}
# El nombre de cada medida en una frase (con su artículo). Una medida que no está acá no recibe sugerencias
NOMBRE_MEDIDA = {"ventas_netas": "las ventas", "ventas_brutas": "las ventas brutas", "descuentos": "los descuentos",
                 "devoluciones": "las devoluciones", "unidades": "las unidades", "costo": "el costo",
                 "margen_bruto": "el margen bruto", "margen_pct": "el margen", "precio_promedio": "el precio promedio",
                 "costo_unitario": "el costo por unidad", "presupuesto": "el presupuesto",
                 "stock_promedio": "el stock promedio", "tasa_quiebre_pct": "la tasa de quiebre",
                 "desvio_presupuesto_pct": "el desvío contra presupuesto", "dias_con_ventas": "los días con ventas"}
PERIODO = ("anio", "mes", "anio_fiscal", "trimestre_fiscal", "mes_fiscal", "fecha", "semana")
DE_ENTRADA = ["categoria", "region"]
NOMBRE = {"region": "región", "sucursal": "sucursal", "categoria": "categoría", "subcategoria": "subcategoría",
          "producto": "producto", "proveedor": "proveedor", "marca": "marca", "formato": "formato"}
DESDE = date.fromisoformat(COBERTURA["ventas_desde"])
HASTA = date.fromisoformat(COBERTURA["ventas_hasta"])
TODA_LA_BASE = f"entre {MESES[DESDE.month - 1]} de {DESDE.year} y {MESES[HASTA.month - 1]} de {HASTA.year}"
# Los hermanos de un filtro, para «¿Y en el Centro?»: los valores válidos de la dimensión, leídos de la base
VALORES = {d: info.get("valores", []) for d, info in ver_modelo()["dimensiones"].items()}
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
        if isinstance(mes, list) and len(mes) > 1:  # unos meses del año fiscal: «de diciembre a abril del AF2026»
            return f"de {MESES[mes[0] - 1]} a {MESES[mes[-1] - 1]} del AF{af}"
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


def anio_parejo(filtros):
    """Para un año calendario que la base no tiene entero (2026: enero a abril; 2024: mayo a diciembre), los mismos
    meses de los dos años, si el anterior los tiene: («enero a abril de 2026», «enero a abril de 2025»). Comparar un
    año incompleto contra uno entero daría una caída falsa."""
    anio = filtros.get("anio")
    if not isinstance(anio, int) or "mes" in filtros:
        return None
    desde, hasta = max(date(anio, 1, 1), DESDE), min(date(anio, 12, 31), HASTA)
    if (desde, hasta) == (date(anio, 1, 1), date(anio, 12, 31)):
        return None  # el año está entero: la comparación de siempre
    if date(anio - 1, desde.month, 1) < DESDE or desde > hasta:
        return None
    meses = f"{MESES[desde.month - 1]} a {MESES[hasta.month - 1]}"
    return f"{meses} de {anio}", f"{meses} de {anio - 1}"


def de(filtros):
    """« de Perfumería en el Sur»: los filtros que no son de período, para el texto."""
    partes = [("el " if d == "region" else "") + con_nombre(filtros[d])
              for d in ("producto", "categoria", "subcategoria", "region", "sucursal", "proveedor")
              if isinstance(filtros.get(d), (str, int))]
    return f" de {' en '.join(partes)}".replace(" de el ", " del ") if partes else ""


def en(filtros):
    """« en el Sur», « en S02 (Los Ceibos)»: dónde, si se filtró, para nombrar al primero de un ranking."""
    if isinstance(filtros.get("sucursal"), str):
        return f" en {con_nombre(filtros['sucursal'])}"
    if isinstance(filtros.get("region"), str):
        return f" en el {filtros['region']}"
    return ""


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


class Memoria:
    """Lo que ya se vio en una conversación: las sugerencias mostradas, las preguntas hechas y cuántas veces se propuso
    cada paso (operador). Una por conversación; sin ella, las sugerencias salen sin memoria."""
    def __init__(self):
        self.vistas, self.usos = set(), {}


def _normal(texto):
    return " ".join(sin_tildes(texto).lower().strip(" ¿?").split())


def candidatas(respuesta, ya_dicho=""):
    """Todas las preguntas para seguir, en orden de prioridad, cada una con su paso (operador). Mira la consulta
    principal de calcular (la primera: la que responde lo pedido; las siguientes suelen ser la comparable o una medida
    de apoyo) y, para no sugerir lo que ya se hizo, todas las de la respuesta. ya_dicho: lo ya preguntado o sugerido
    en la conversación, sin tildes, para no proponer un hermano que ya se vio."""
    if respuesta.get("ruta") != "agente" or respuesta.get("tipo") == "sin_dato":
        return []  # sin dato: sugerir otra medida sería responder con otra cosa. Una ambigua sí: el agente ya eligió
                   # una lectura y respondió con ella (y si no consultó nada, abajo no hay de dónde sugerir)
    consultas = [c for c in respuesta.get("consultas", []) if c["tool"] == "calcular"]
    if not consultas:
        return []
    a, r = consultas[0]["argumentos"], consultas[0]["resultado"]
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
    validas = dimensiones_validas(medida)
    sin_periodo = not any(k in filtros for k in PERIODO)
    periodo = corto(filtros) or (TODA_LA_BASE if sin_periodo else None)
    nombre = NOMBRE_MEDIDA.get(medida)
    if not periodo or not nombre:
        return []
    en_periodo = f" {periodo}" if periodo == TODA_LA_BASE else f" en {periodo}"
    plural = nombre.startswith(("las", "los"))
    abre, vino = ("se abren", "vinieron") if plural else ("se abre", "vino")
    salida = []

    # 1. La causa: un grupo que cae más que el total (eso es un diagnóstico: la puerta lo manda al coordinador)
    if agrupar and a.get("comparar_con") and (grupo := grupo_que_mas_cayo(r, agrupar[0])):
        salida.append(("causa", f"¿Qué explica la caída de {con_nombre(grupo)} en {nombre.split(' ', 1)[1]}{en_periodo}?"))
        hijo = SIGUIENTE.get(agrupar[0])
        if hijo in validas:
            salida.append(("bajar", f"¿Cómo {abre} {nombre} de {con_nombre(grupo)} por {NOMBRE[hijo]}{en_periodo}?"))
    elif cayo:
        en_comparables = " en sucursales comparables" if cayo["argumentos"].get("comparables") else ""
        salida.append(("causa", f"¿Qué explica la caída de {nombre}{de(filtros)}{en_comparables}{en_periodo}?".replace(" de el ", " del ")))
    # 1b. Un ranking (abierto y sin comparar): mirar al primero por otra dimensión
    primero = r["filas"][0].get(agrupar[0]) if agrupar and r.get("filas") else None
    if agrupar and not a.get("comparar_con") and primero is not None:
        otra = next((d for d in DEL_PRIMERO.get(agrupar[0], []) if d in validas and not isinstance(filtros.get(d), (str, int))), None)
        if otra:
            salida.append(("primero_por_otra", f"¿Cómo {abre} {nombre} de {con_nombre(primero)}{en(filtros)} por {NOMBRE[otra]}{en_periodo}?"))
        # 1c. El primero contra el año anterior: si el período tiene uno en la base, o el último AF si no hay período
        sujeto = ("el " if agrupar[0] == "region" else "") + con_nombre(primero)
        if sin_periodo and date(HASTA.year - 2, 5, 1) >= DESDE:
            af = HASTA.year if (HASTA.month, HASTA.day) == (4, 30) else HASTA.year - (HASTA.month < 5)
            salida.append(("primero_anio", f"¿Cómo {vino} {nombre} de {sujeto}{en(filtros)} en el AF{af} contra el AF{af - 1}?"))
        elif not sin_periodo and (previo := anterior(filtros)):
            salida.append(("primero_anio", f"¿Cómo {vino} {nombre} de {sujeto}{en(filtros)}{en_periodo} contra {corto({**filtros, **previo})}?"))
    # 2. El desvío con presupuesto sospechoso (decisión 84): mirar los meses vecinos
    if medida == "desvio_presupuesto_pct" and r.get("aviso") and isinstance(filtros.get("mes"), int):
        mes, anio = filtros["mes"], filtros.get("anio")
        antes = (MESES[(mes - 2) % 12], anio - 1 if mes == 1 else anio)
        despues = (MESES[mes % 12], anio + 1 if mes == 12 else anio)
        salida.append(("meses_vecinos", f"¿Cuál fue {nombre}{de(filtros)} en {antes[0]} de {antes[1]} y en {despues[0]} de {despues[1]}?"))
    # 3. Comparar con el año anterior
    parejo = anio_parejo(filtros)
    if not comparo and medida != "desvio_presupuesto_pct" and parejo:
        salida.append(("anio_anterior", f"¿Cómo {vino} {nombre}{de(filtros)} de {parejo[0]} contra {parejo[1]}?"))
    elif not comparo and medida != "desvio_presupuesto_pct" and (previo := anterior(filtros)):
        salida.append(("anio_anterior", f"¿Cómo {vino} {nombre}{de(filtros)}{en_periodo} contra {corto({**filtros, **previo})}?"))
    # 4. Comparables: las ventas de dos períodos con todas las sucursales (S39 y S40 abrieron en el medio)
    if comparo and not comparables and medida in ("ventas_netas", "unidades"):
        salida.append(("comparables", "¿Y en sucursales comparables, las que estaban abiertas en los dos períodos?"))
    # 5. El margen: ¿precio o costo? Salvo que la respuesta ya lo haya separado (efectos_margen)
    separado = any(c["argumentos"].get("medida") == "efectos_margen" for c in consultas)
    if medida == "margen_pct" and a.get("comparar_con") and not separado:
        salida.append(("precio_costo", f"¿El cambio del margen{de(filtros)}{en_periodo} fue por precio o por costo?"))
    # 6. Bajar un nivel
    if not agrupar:
        ya = [SIGUIENTE[d] for d in SIGUIENTE if d in filtros and isinstance(filtros[d], str)]
        hijos = list(dict.fromkeys(d for d in ya + DE_ENTRADA if d in validas and d not in filtros))
        for hijo in hijos[:2]:
            salida.append(("bajar", f"¿Cómo {abre} {nombre}{de(filtros)} por {NOMBRE[hijo]}{en_periodo}?"))
    # 7. Cruzar con otra medida: del primero de un ranking, o de lo que se filtró
    otra_medida = CRUCE.get(medida)
    if otra_medida and not any(c["argumentos"].get("medida") == otra_medida for c in consultas):
        nombrado = ("el " if agrupar and agrupar[0] == "region" else "") + con_nombre(primero) if primero is not None else ""
        sujeto = (nombrado + en(filtros)) if primero is not None else \
            (de(filtros).removeprefix(" del ").removeprefix(" de ") if de(filtros) else "la cadena")
        if primero is None and de(filtros).startswith(" del "):
            sujeto = "el " + sujeto
        if otra_medida == "margen_pct":
            salida.append(("cruce", f"¿Qué margen tuvo {sujeto}{en_periodo}?"))
        elif otra_medida == "unidades":
            salida.append(("cruce", f"¿Cuántas unidades vendió {sujeto}{en_periodo}?"))
        else:
            salida.append(("cruce", f"¿Cuánto vendió {sujeto}{en_periodo}?"))
    # 8. El hermano: lo mismo en otra región o categoría que todavía no se preguntó («¿Y en el Centro?»)
    for d in ("region", "categoria"):
        actual = filtros.get(d)
        if isinstance(actual, str):
            otro = next((v for v in VALORES.get(d, []) if v != actual and sin_tildes(str(v)).lower() not in ya_dicho), None)
            if otro:
                salida.append(("hermano", f"¿Y en {'el ' if d == 'region' else ''}{otro}?"))
    # 9. Sin período (toda la base): lo mismo en el último año fiscal completo, que es lo que suele importar
    if sin_periodo:
        ultimo_af = HASTA.year if HASTA.month == 4 and HASTA.day == 30 else HASTA.year - (HASTA.month < 5)
        salida.append(("af", f"¿Y en el AF{ultimo_af}?"))
    return list(dict.fromkeys(salida))


def sugerencias(respuesta, memoria=None, pregunta=None):
    """Hasta MAXIMO preguntas para seguir. Con memoria (una por conversación), no repite lo ya mostrado ni lo ya
    preguntado, y pone primero los pasos que menos se propusieron (decisión 121)."""
    if memoria is None:
        return [texto for _, texto in candidatas(respuesta)][:MAXIMO]
    if pregunta:
        memoria.vistas.add(_normal(pregunta))
    nuevas = [(op, texto) for op, texto in candidatas(respuesta, " ".join(memoria.vistas))
              if _normal(texto) not in memoria.vistas]
    # Primero los pasos menos propuestos en la conversación; a igualdad, el orden de prioridad (el sort es estable)
    nuevas.sort(key=lambda par: memoria.usos.get(par[0], 0))
    elegidas = nuevas[:MAXIMO]
    memoria.vistas |= {_normal(texto) for _, texto in elegidas}
    for op, _ in elegidas:
        memoria.usos[op] = memoria.usos.get(op, 0) + 1
    return [texto for _, texto in elegidas]
