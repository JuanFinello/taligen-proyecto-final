"""Gráficos de los informes: los arma el código a partir del resultado de calcular(), nunca el modelo (semana 2).
Cada gráfico devuelve también los números que dibujó, para que se puedan rastrear hasta su consulta."""
import os
import statistics
from datetime import date

import duckdb
import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")  # sin ventana: solo archivos
import matplotlib.pyplot as plt

from procesador_capa_semantica import BASE

# Colores de la paleta de referencia (skill dataviz): una serie en azul; arriba/abajo de cero, azul y rojo
AZUL, ROJO = "#2a78d6", "#e34948"
SERIES = [AZUL, "#d9822b", "#7b5cc4", "#2a9d8f"]  # una línea por grupo (decisión 106): como mucho 4, cada una con su color
TINTA, TINTA_SUAVE, GRILLA = "#0b0b0b", "#52514e", "#e4e3df"
GRIS = "#cfcdc8"  # lo que no se resalta (decisión 54)

# El color dice si el cambio es bueno o malo, no su signo (IBCS): una suba de costo es mala aunque sea positiva.
# En las neutras no hay bueno ni malo (más descuento o más stock no es mejor ni peor en sí): siempre azul
MENOS_ES_MEJOR = {"costo", "costo_unitario", "devoluciones", "tasa_quiebre_pct"}
NEUTRAS = {"descuentos", "presupuesto", "stock_promedio", "cantidad_sucursales", "sucursales_abiertas"}

CALCULADOS = {"valor", "participacion_pct", "actual", "anterior", "variacion", "diferencia", "aporte_pct",
              "ventas_netas", "presupuesto", "margen_pct_anterior", "margen_pct_actual", "variacion_pp",
              "efecto_precio_pp", "efecto_costo_pp", "precio_anterior", "precio_actual", "costo_unitario_anterior",
              "costo_unitario_actual", "variacion_precio_pct", "variacion_costo_unitario_pct",
              "presupuesto_sospechoso"}  # lo que calcular() agrega a cada fila; el resto son dimensiones
TEMPORALES = ["fecha", "semana", "mes", "mes_fiscal", "trimestre_fiscal", "anio", "anio_fiscal"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MESES_FISCALES = MESES[4:] + MESES[:4]  # el año fiscal empieza en mayo


def formato(valor, unidad, con_signo=False, millones=False):
    """Número en castellano: coma decimal, punto de miles; en millones si lo pide el gráfico (todos iguales)."""
    signo = "−" if valor < 0 else "+" if con_signo and valor > 0 else ""
    valor = abs(valor)
    if unidad.startswith("ARS"):  # «ARS» y «ARS por unidad»
        texto = "$ " + (f"{valor / 1e6:,.1f} M" if millones else f"{valor:,.0f}")
    elif unidad in ("%", "pp"):
        texto = f"{valor:,.1f} {unidad}"
    else:
        texto = f"{valor:,.0f}"
    if not any(c in "123456789" for c in texto):  # redondeado da cero: sin signo («0,0 pp», no «−0,0 pp»)
        signo = ""
    return signo + texto.replace(",", "_").replace(".", ",").replace("_", ".")


def _nombres():
    """Código → nombre corto de proveedores y sucursales. A las sucursales se les saca el prefijo que comparten todas
    («Almacenes del Sur »): en la página alcanza con «Sierra Chica»."""
    with duckdb.connect(BASE, read_only=True) as con:
        proveedores = dict(con.execute("SELECT proveedor_id, nombre FROM proveedores").fetchall())
        sucursales = dict(con.execute("SELECT sucursal_id, nombre FROM sucursales").fetchall())
    prefijo = os.path.commonprefix(list(sucursales.values()))
    prefijo = prefijo[:prefijo.rfind(" ") + 1]  # hasta una palabra entera
    return {**proveedores, **{k: v[len(prefijo):] for k, v in sucursales.items()}}, prefijo


NOMBRES, PREFIJO_SUCURSALES = _nombres()


NOMBRE_DE = {"proveedor": "nombre_proveedor", "sucursal": "nombre_sucursal"}


def etiqueta(fila, dimensiones):
    """Nombre del grupo: los valores de sus dimensiones. Si vino el nombre del proveedor o de la sucursal, va solo el
    nombre: el código es ruido para la gerencia (decisión 68). Los productos sí llevan su sku: hay nombres repetidos."""
    partes = []
    for d in dimensiones:
        if NOMBRE_DE.get(d) in dimensiones:
            continue
        valor = fila[d]
        if d in ("semana", "fecha") and isinstance(valor, str):  # del informe.json vuelve como texto
            valor = date.fromisoformat(valor[:10])
        if d in NOMBRE_DE and NOMBRE_DE[d] not in dimensiones:  # vino el código solo: su nombre
            valor = NOMBRES.get(valor, valor)
        elif d == "nombre_sucursal":
            valor = NOMBRES.get(fila.get("sucursal"), valor.removeprefix(PREFIJO_SUCURSALES))
        if d == "mes":
            valor = MESES[valor - 1]
        elif d == "mes_fiscal":
            valor = MESES_FISCALES[valor - 1]
        elif d == "trimestre_fiscal":
            valor = f"T{valor}"
        elif d in ("semana", "fecha") and hasattr(valor, "month"):  # «8 sep»: el año lo dice el rótulo
            valor = f"{valor.day} {MESES[valor.month - 1]}"
        elif isinstance(valor, bool) and d in SI_NO:
            valor = SI_NO[d][0 if valor else 1]
        partes.append(str(valor))
    return " · ".join(partes)


SI_NO = {"es_marca_propia": ("Marca propia", "Otras marcas")}  # cómo se nombra cada lado de una dimensión sí/no


def dimensiones_de(filas):
    """Las dimensiones de las filas: las columnas que no son números calculados; un nombre cuenta como su código
    (nombre_sucursal es la dimensión sucursal)."""
    dimensiones = [d.removeprefix("nombre_") for d in filas[0] if d not in CALCULADOS] if filas else []
    return list(dict.fromkeys(dimensiones))


# Con más grupos de los que entran en barras, la pregunta es si el cambio es de todos o de unos pocos: va la
# distribución entera, un punto por grupo, y no los 6 que más se movieron (decisión 106). Solo sucursales y
# productos: con proveedores o marcas importa el nombre de cada uno, y ahí siguen las barras
DISTRIBUCION = {"sucursal", "producto"}
MAXIMO_GRUPOS = 6  # el informe es de una página: dos gráficos chicos (decisión 54)
# Las sucursales de una región (10 como mucho) entran en barras, que se leen mejor que los puntos: con su nombre y su
# largo. La distribución queda para más (las 40 de la cadena, los productos)
MAXIMO_SUCURSALES = 12


def que_dibujar(resultado):
    """Elige el gráfico según la forma del resultado: (tipo, campo del valor, unidad del valor)."""
    filas = resultado["filas"]
    unidad = resultado["unidad"]
    dimensiones = dimensiones_de(filas)
    por_tiempo = len(dimensiones) == 1 and dimensiones[0] in TEMPORALES
    muchos = len(dimensiones) == 1 and dimensiones[0] in DISTRIBUCION and len(filas) > MAXIMO_SUCURSALES
    forma = "distribucion" if muchos else "divergente"
    temporales = [d for d in dimensiones if d in TEMPORALES]
    if len(dimensiones) == 2 and "valor" in filas[0] and "variacion" not in filas[0]:
        # dos cortes sin comparación (decisión 106): tiempo × grupo, un mapa de calor (dónde y cuándo a la vez);
        # grupo × un sí/no, pesas (la distancia entre los dos lados, en cada grupo)
        if len(temporales) == 1:  # una medida que se suma (pesos, unidades), apilada: se ve cada parte y el total;
            return ("calor" if unidad in ("%", "pp") else "apiladas"), "valor", unidad  # un %, en mapa de calor
        if any(len({f[d] for f in filas}) == 2 for d in dimensiones):
            return "pesas", "valor", unidad
    if len(dimensiones) == 2 and len(temporales) == 1 and len({f[next(d for d in dimensiones if d not in TEMPORALES)]
                                                                for f in filas}) <= len(SERIES):
        # por mes y por pocos grupos: una línea por grupo con su cambio (decisión 106)
        if resultado["medida"] == "efectos_margen":
            return "lineas_por_grupo", "variacion_pp", "pp"
        if "variacion" in filas[0]:
            return "lineas_por_grupo", "variacion", resultado.get("unidad_variacion", "%")
    if resultado["medida"] == "desvio_presupuesto_pct":
        return forma, "valor", "%"
    if resultado["medida"] == "efectos_margen":  # la variación del margen de cada grupo; los efectos van en el texto
        # por mes, el margen % de los dos períodos en dos líneas, como cualquier comparación por mes (decisión 106)
        return ("lineas", "margen_pct_actual", "%") if por_tiempo else (forma, "variacion_pp", "pp")
    if por_tiempo and "actual" in filas[0] and "anterior" in filas[0]:
        # Dos períodos mes a mes: dos líneas, para ver si el cambio es sostenido o de un mes (decisión 106)
        return "lineas", "actual", unidad
    if muchos and "variacion" in filas[0]:  # sucursales de tamaños distintos: se comparan en %, no en pesos
        return forma, "variacion", resultado.get("unidad_variacion", "%")
    if "diferencia" in filas[0]:  # comparación de una medida aditiva: lo que subió o bajó cada grupo
        return "divergente", "diferencia", unidad
    if "variacion" in filas[0]:  # comparación de un % o un promedio: la variación (pp si es un %)
        return "divergente", "variacion", resultado.get("unidad_variacion", "%")
    return "barras", "valor", unidad



def color_de(medida, valor):
    """Azul si el valor es bueno, rojo si es malo, según la medida (en las neutras, azul)."""
    if medida in NEUTRAS:
        return AZUL
    bueno = valor <= 0 if medida in MENOS_ES_MEJOR else valor >= 0
    return AZUL if bueno else ROJO


def es_destacado(fila, dimensiones, destacar):
    """¿La fila es uno de los grupos a resaltar? Vale el código o el nombre («PR01» o «Molinos del Plata»)."""
    valores = [str(fila[d]).lower() for d in dimensiones]
    nombre = etiqueta(fila, dimensiones).lower()
    # Un código o un número tiene que ser exacto: «1» (enero) no puede resaltar «12» (diciembre). Un nombre puede ir
    # en parte: «Molinos del Plata» resalta «Molinos del Plata S.A.» (decisión 71)
    return any(d.lower() in valores or d.lower() == nombre or (len(d) >= 4 and not d.isdigit() and d.lower() in nombre)
               for d in map(str, destacar))


def orden_temporal(resultado, dimension, filtros=None):
    """Para ordenar los períodos: de nov-2025 a mar-2026, dic va antes que ene (empieza en el mes de desde); en un año
    fiscal, de mayo a abril."""
    desde = (resultado.get("periodo") or {}).get("desde")
    primero = int(desde[5:7]) if desde else 5 if {"anio_fiscal", "trimestre_fiscal"} & set(filtros or {}) else None
    if dimension == "mes" and primero:
        return lambda f: (f["mes"] - primero) % 12
    return lambda f: f[dimension]


def _terminar(fig, ax, ruta, titulo, letra_x=8):
    """Lo común a todos los gráficos: título opcional, sin bordes, guardar."""
    if titulo:  # en el informe de una página el título va en el texto, como conclusión (decisión 54)
        fig.suptitle(titulo, x=0.02, ha="left", fontsize=11, color=TINTA)  # desde el borde: no lo corta una etiqueta
    ax.tick_params(colors=TINTA_SUAVE, labelsize=8, length=0)
    ax.tick_params(axis="x", labelsize=letra_x)
    for lado in ax.spines.values():
        lado.set_visible(False)
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def separar(posiciones, ax, proporcion=0.09):
    """Las alturas de los rótulos al final de las líneas, corridas lo justo para que no se pisen (en el orden dado)."""
    bajo, alto = ax.get_ylim()
    minimo = (alto - bajo) * proporcion
    orden = sorted(range(len(posiciones)), key=lambda i: posiciones[i])
    corridas = list(posiciones)
    for antes, i in zip(orden, orden[1:]):
        corridas[i] = max(corridas[i], corridas[antes] + minimo)
    exceso = (max(corridas) - max(posiciones)) / 2  # repartir el corrimiento para arriba y para abajo
    return [y - exceso for y in corridas]


def _lineas_por_grupo(resultado, filas, temporal, grupo, campo, unidad, ruta, titulo, destacar, filtros):
    """Por mes y por un grupo (2 a 4 categorías o regiones): una línea por grupo, con el cambio contra el período
    anterior y el cero marcado; así se ve cuándo se movió cada uno y si uno compensó al otro (decisión 106)."""
    filas = sorted(filas, key=orden_temporal(resultado, temporal, filtros))
    meses = list(dict.fromkeys(etiqueta(f, [temporal]) for f in filas))
    grupos = list(dict.fromkeys(f[grupo] for f in filas))
    fig, ax = plt.subplots(figsize=(7, 2.4), dpi=200)
    finales, datos, numero = [], [], 0
    for g in grupos:
        serie = [f for f in filas if f[grupo] == g]
        valores = [f[campo] for f in serie]
        resaltado = not destacar or es_destacado(serie[0], [grupo], destacar)
        color = SERIES[numero % len(SERIES)] if resaltado else GRIS  # el primero resaltado, azul
        numero += resaltado
        g = etiqueta(serie[0], [grupo])  # «Marca propia», no «True»
        ax.plot([etiqueta(f, [temporal]) for f in serie], valores, color=color, linewidth=2)
        ax.plot(len(meses) - 1, valores[-1], "o", color=color, markersize=4)
        finales.append((g, valores[-1], color))
        datos += [(f"{g} · {etiqueta(f, [temporal])}", f[campo]) for f in serie]
    ax.axhline(0, color=TINTA_SUAVE, linewidth=0.8)
    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(4))
    ax.yaxis.set_major_formatter(lambda v, _: formato(v, unidad, True))
    for (g, valor, color), y in zip(finales, separar([v for _, v, _ in finales], ax)):
        ax.annotate(f"{g} {formato(valor, unidad, True)}", (len(meses) - 1, y), xytext=(8, 0),
                    textcoords="offset points", va="center", fontsize=8, color=color)
    ax.grid(axis="y", color=GRILLA, linewidth=0.6)
    ax.margins(x=0.04)
    _terminar(fig, ax, ruta, titulo)
    return {"ruta": str(ruta), "titulo": titulo, "tipo": "lineas_por_grupo", "campo": campo, "unidad": unidad,
            "datos": datos, "mostrados": len(grupos), "omitidos": 0,
            "resaltados": [g for g in grupos if destacar and es_destacado({grupo: g}, [grupo], destacar)], "nota": ""}


def _calor(resultado, filas, dimensiones, unidad, ruta, titulo):
    """Tiempo × grupo: una celda por (período, grupo) con su valor, más oscura cuanto más alto. Un incidente se ve
    como un bloque: en qué grupo y en qué períodos. Una sola tinta (rojo si más es peor, azul si no)."""
    from matplotlib.colors import LinearSegmentedColormap
    temporal = next(d for d in dimensiones if d in TEMPORALES)
    grupo = next(d for d in dimensiones if d not in TEMPORALES)
    periodos = sorted({f[temporal] for f in filas})
    grupos = sorted({f[grupo] for f in filas}, key=str)
    valor = {(f[grupo], f[temporal]): f["valor"] for f in filas}
    matriz = [[valor.get((g, p)) for p in periodos] for g in grupos]
    tinta = ROJO if resultado["medida"] in MENOS_ES_MEJOR else AZUL
    mapa = LinearSegmentedColormap.from_list("una_tinta", ["#f4f3f0", tinta])
    fig, ax = plt.subplots(figsize=(7, 0.35 * len(grupos) + 0.8), dpi=200)
    ax.imshow([[v if v is not None else 0 for v in fila] for fila in matriz], cmap=mapa, aspect="auto", vmin=0)
    maximo = max(v for fila in matriz for v in fila if v is not None) or 1
    for i, fila in enumerate(matriz):
        for j, v in enumerate(fila):
            if v is not None:  # el número en la celda: blanco sobre lo oscuro
                ax.text(j, i, f"{v:,.0f}".replace(",", "."), ha="center", va="center", fontsize=6.5,
                        color="white" if v > maximo * 0.55 else TINTA_SUAVE)
    ax.set_yticks(range(len(grupos)), [etiqueta({grupo: g}, [grupo]) for g in grupos])
    ax.set_xticks(range(len(periodos)), [etiqueta({temporal: p}, [temporal]) for p in periodos], rotation=0)
    _terminar(fig, ax, ruta, titulo)
    return {"ruta": str(ruta), "titulo": titulo, "tipo": "calor", "campo": "valor", "unidad": unidad,
            "datos": [(f"{etiqueta({grupo: g}, [grupo])} · {etiqueta({temporal: p}, [temporal])}", valor.get((g, p)))
                      for g in grupos for p in periodos], "mostrados": len(grupos), "omitidos": 0, "resaltados": [],
            "nota": f"cada celda, en {unidad}"}


def _apiladas(resultado, filas, dimensiones, unidad, ruta, titulo, destacar):
    """Tiempo × grupo de una medida que se suma: columnas apiladas, una por período. Abajo, sobre la base común, los
    grupos que no se resaltan (en grises): así se lee si compensaron; arriba, en color, el que nombra la razón. El
    alto de la columna es el total. Cada parte se nombra al final, sin leyenda (decisión 106)."""
    temporal = next(d for d in dimensiones_de(filas) if d in TEMPORALES)
    grupo = next(d for d in dimensiones if d not in TEMPORALES and d != temporal)
    periodos = sorted({f[temporal] for f in filas})
    grupos = sorted({f[grupo] for f in filas}, key=lambda g: (es_destacado({grupo: g}, [grupo], destacar), str(g)))
    valor = {(f[grupo], f[temporal]): f["valor"] or 0 for f in filas}
    millones = max(sum(valor.get((g, p), 0) for g in grupos) for p in periodos) >= 1e6
    grises = ["#b9b7b1", "#d6d4ce", "#e8e6e1"]
    fig, ax = plt.subplots(figsize=(7, 2.6), dpi=200)
    base = [0] * len(periodos)
    nombres = [etiqueta({temporal: p}, [temporal]) for p in periodos]
    finales, numero_gris = [], 0
    for g in grupos:
        alturas = [valor.get((g, p), 0) for p in periodos]
        if es_destacado({grupo: g}, [grupo], destacar):
            color = AZUL
        else:
            color, numero_gris = grises[numero_gris % len(grises)], numero_gris + 1
        ax.bar(nombres, alturas, bottom=base, color=color, width=0.7, edgecolor="white", linewidth=0.5)
        finales.append((etiqueta({grupo: g}, [grupo]), base[-1] + alturas[-1] / 2, color))
        base = [b + a for b, a in zip(base, alturas)]
    for nombre, y, color in finales:  # el nombre de cada parte, a la derecha de la última columna
        ax.annotate(nombre.removesuffix(" S.A.").replace(" S.A. (marca propia)", " (marca propia)"),
                    (len(periodos) - 1, y), xytext=(22, 0), textcoords="offset points", va="center", fontsize=7.5,
                    color=TINTA if color == AZUL else TINTA_SUAVE)
    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(4))
    ax.yaxis.set_major_formatter(lambda v, _: formato(v, unidad, millones=millones))
    ax.grid(axis="y", color=GRILLA, linewidth=0.6)
    ax.set_axisbelow(True)
    _terminar(fig, ax, ruta, titulo, letra_x=6.5 if len(periodos) > 8 else 8)  # muchas fechas: más chicas
    return {"ruta": str(ruta), "titulo": titulo, "tipo": "apiladas", "campo": "valor", "unidad": unidad,
            "datos": [(f"{etiqueta({grupo: g}, [grupo])} · {etiqueta({temporal: p}, [temporal])}", valor.get((g, p)))
                      for g in grupos for p in periodos], "mostrados": len(grupos), "omitidos": 0,
            "resaltados": [g for g in grupos if es_destacado({grupo: g}, [grupo], destacar)], "nota": ""}


def _pesas(resultado, filas, dimensiones, unidad, ruta, titulo):
    """Grupo × un sí/no: una fila por grupo con los dos valores unidos por una línea. Se ve si la distancia entre
    los dos lados se repite en todos los grupos. Los dos lados se nombran sobre la primera fila, sin leyenda."""
    lado = next(d for d in dimensiones if len({f[d] for f in filas}) == 2)
    grupo = next(d for d in dimensiones if d != lado)
    valores = {}
    for f in filas:
        valores.setdefault(f[grupo], {})[f[lado]] = f["valor"]
    si, no = (True, False) if lado in SI_NO else sorted({f[lado] for f in filas}, key=str)
    grupos = sorted((g for g in valores if si in valores[g] and no in valores[g]), key=lambda g: valores[g][no])
    alto_fila = 0.26 if len(grupos) <= 8 else 0.165  # muchos grupos: filas más juntas, para que entre en la página
    fig, ax = plt.subplots(figsize=(7, alto_fila * len(grupos) + 0.7), dpi=200)
    for i, g in enumerate(grupos):
        a, b = valores[g][no], valores[g][si]
        ax.plot([a, b], [i, i], color=GRILLA, linewidth=3, zorder=1)
        ax.scatter([a], [i], color=GRIS, s=40, zorder=2)
        ax.scatter([b], [i], color=AZUL, s=40, zorder=2)
        for x, color, a_la_izquierda in ((a, TINTA_SUAVE, a <= b), (b, TINTA, b < a)):  # el número, del lado de afuera
            ax.annotate(formato(x, unidad), (x, i), xytext=(-7 if a_la_izquierda else 7, 0), textcoords="offset points",
                        ha="right" if a_la_izquierda else "left", va="center", fontsize=7.5, color=color)
    arriba = len(grupos) - 1
    for x, nombre, color in ((valores[grupos[-1]][no], etiqueta({lado: no}, [lado]), TINTA_SUAVE),
                             (valores[grupos[-1]][si], etiqueta({lado: si}, [lado]), AZUL)):
        ax.annotate(nombre, (x, arriba), xytext=(0, 10), textcoords="offset points", ha="center", fontsize=7.5,
                    color=color)
    ax.set_yticks(range(len(grupos)), [etiqueta({grupo: g}, [grupo]) for g in grupos])
    ax.xaxis.set_visible(False)
    ax.margins(x=0.12, y=0.25 if len(grupos) <= 8 else 0.08)
    _terminar(fig, ax, ruta, titulo)
    return {"ruta": str(ruta), "titulo": titulo, "tipo": "pesas", "campo": "valor", "unidad": unidad,
            "datos": [(f"{etiqueta({grupo: g}, [grupo])} · {etiqueta({lado: l}, [lado])}", valores[g][l])
                      for g in grupos for l in (no, si)], "mostrados": len(grupos), "omitidos": 0, "resaltados": [],
            "nota": ""}


def _lineas(resultado, filas, dimensiones, campo, unidad, ruta, titulo, series, filtros):
    """Dos períodos mes a mes: el actual en azul y el anterior en gris, con su nombre al final de cada línea
    (sin leyenda aparte: el rótulo junto a la línea se lee sin ir y volver)."""
    filas = sorted(filas, key=orden_temporal(resultado, dimensiones[0], filtros))
    campo_anterior = campo.replace("actual", "anterior")  # actual → anterior; margen_pct_actual → margen_pct_anterior
    filas = [f for f in filas if f.get(campo_anterior) is not None]
    nombres = [etiqueta(f, dimensiones) for f in filas]
    actual, anterior = [f[campo] for f in filas], [f[campo_anterior] for f in filas]
    millones = max(abs(v) for v in actual + anterior) >= 1e6
    fig, ax = plt.subplots(figsize=(7, 2.4), dpi=200)
    # Tinta (decisión 106): fuera lo redundante (un marcador en cada mes repite lo que ya dice la línea; queda solo
    # el último, donde está el nombre), y la tinta de referencia mínima pero no nula: pocas líneas de grilla, muy
    # claras, para leer el nivel (Gillan y Richman 1994: la tinta de más empeora; quitar los ejes, también)
    for valores, color in ((anterior, GRIS), (actual, AZUL)):
        ax.plot(nombres, valores, color=color, linewidth=2)
        ax.plot(nombres[-1], valores[-1], color=color, marker="o", markersize=4)
    # Sin forzar el cero: lo que se compara es la distancia entre las dos líneas, y desde cero no se ve; el nivel lo
    # dice el rótulo de cada una (las barras sí arrancan en cero: ahí el largo es el valor)
    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(4))
    ax.yaxis.set_major_formatter(lambda v, _: formato(v, unidad, millones=millones))
    posiciones = separar([anterior[-1], actual[-1]], ax)
    for valores, y, color, nombre in ((anterior, posiciones[0], TINTA_SUAVE, series[1]),
                                      (actual, posiciones[1], TINTA, series[0])):
        ax.annotate(f"{nombre} {formato(valores[-1], unidad, millones=millones)}", (len(nombres) - 1, y),
                    xytext=(8, 0), textcoords="offset points", va="center", fontsize=8, color=color)
    ax.grid(axis="y", color=GRILLA, linewidth=0.6)
    ax.margins(x=0.04)
    _terminar(fig, ax, ruta, titulo)
    return {"ruta": str(ruta), "titulo": titulo, "tipo": "lineas", "campo": campo, "unidad": unidad,
            "datos": list(zip(nombres, actual)), "anteriores": list(zip(nombres, anterior)), "mostrados": len(filas),
            "omitidos": 0, "resaltados": [], "nota": ""}


def _distribucion(resultado, filas, dimensiones, campo, unidad, ruta, titulo, destacar):
    """Muchos grupos (sucursales, productos): una columna por grupo, ordenadas de la que más bajó a la que más subió.
    Se lee como una escalera: si el cambio es de todos, es pareja; un grupo con un problema se ve como un escalón
    brusco en una punta. Llevan nombre las dos puntas y los grupos que nombra la razón (en azul; el resto, en gris).
    Sin destacar, cada columna en color según si su cambio es bueno o malo. (Antes era un punto por grupo: la altura
    de cada punto no significaba nada y costaba leerlo.)"""
    filas = sorted(filas, key=lambda f: f[campo])
    valores = [f[campo] for f in filas]
    nombres = [etiqueta(f, dimensiones) for f in filas]
    resaltados = [bool(destacar) and es_destacado(f, dimensiones, destacar) for f in filas]
    medida = resultado["medida"]
    fig, ax = plt.subplots(figsize=(7, 2.4), dpi=200)
    colores = [(AZUL if r else GRIS) if destacar else color_de(medida, v) for r, v in zip(resaltados, valores)]
    ax.bar(range(len(valores)), valores, color=colores, width=0.75)
    ax.axhline(0, color=TINTA_SUAVE, linewidth=0.8)
    for i in {0, len(valores) - 1}:  # las dos puntas, en la punta de su columna
        if not resaltados[i]:
            ax.annotate(f"{nombres[i]} {formato(valores[i], unidad, True)}", (i, valores[i]),
                        xytext=(0, -9 if valores[i] < 0 else 4), textcoords="offset points",
                        ha="left" if i == 0 else "right", fontsize=7, color=TINTA_SUAVE)
    for i, resaltado in enumerate(resaltados):  # los que nombra la razón, del otro lado del cero: ahí no hay columnas
        if resaltado:
            ax.annotate(f"{nombres[i]} {formato(valores[i], unidad, True)}", (i, 0),
                        xytext=(0, 4 if valores[i] < 0 else -9), textcoords="offset points",
                        ha="left" if i < len(valores) / 2 else "right", fontsize=7, color=AZUL)
    ax.set_xticks([])
    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(5))
    ax.yaxis.set_major_formatter(lambda v, _: formato(v, unidad, True))
    ax.grid(axis="y", color=GRILLA, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.margins(y=0.18)
    _terminar(fig, ax, ruta, titulo)
    grupo = dimensiones_de(filas)[0]
    una = "una" if grupo == "sucursal" else "un"
    return {"ruta": str(ruta), "titulo": titulo, "tipo": "distribucion", "campo": campo, "unidad": unidad,
            "datos": list(zip(nombres, valores)), "mostrados": len(filas), "omitidos": 0,
            "resaltados": [n for n, r in zip(nombres, resaltados) if r],
            "nota": f"cada columna es {una} {grupo}, de l{'a' if grupo == 'sucursal' else 'o'} que más bajó a "
                    f"l{'a' if grupo == 'sucursal' else 'o'} que más subió",
            "mediana": statistics.median(valores)}


def graficar(resultado, ruta, titulo, maximo=MAXIMO_GRUPOS, destacar=(), series=("actual", "anterior"),
             filtros=None):
    """Un PNG a partir de un resultado agrupado de calcular(). Devuelve qué dibujó, con sus números.
    Fuera de los gráficos por tiempo, muestra como máximo `maximo` grupos: los resaltados y los que más se movieron.
    Con `destacar`, solo esos grupos van en color y el resto en gris (Storytelling with Data)."""
    if not resultado.get("filas"):
        raise ValueError("Solo se grafica un resultado agrupado (con agrupar_por)")
    filas = resultado["filas"]
    # Las dimensiones son las columnas que no son números calculados (nombre_proveedor queda dentro de la etiqueta)
    dimensiones = [d for d in filas[0] if d not in CALCULADOS]
    tipo, campo, unidad = que_dibujar(resultado)
    filas = [f for f in filas if f[campo] is not None]
    if tipo == "distribucion":
        return _distribucion(resultado, filas, dimensiones, campo, unidad, ruta, titulo, destacar)
    if tipo == "apiladas":
        return _apiladas(resultado, filas, dimensiones, unidad, ruta, titulo, destacar)
    if tipo == "calor":
        return _calor(resultado, filas, dimensiones_de(filas), unidad, ruta, titulo)
    if tipo == "pesas":
        return _pesas(resultado, filas, dimensiones_de(filas), unidad, ruta, titulo)
    if tipo == "lineas_por_grupo":
        temporal = next(d for d in dimensiones_de(filas) if d in TEMPORALES)
        grupo = next(d for d in dimensiones if d not in TEMPORALES and not d.startswith("nombre_"))
        return _lineas_por_grupo(resultado, filas, temporal, grupo, campo, unidad, ruta, titulo, destacar, filtros)
    if tipo == "lineas":
        return _lineas(resultado, filas, dimensiones, campo, unidad, ruta, titulo, series, filtros)
    # Por tiempo, todos los períodos en orden y en el eje horizontal (IBCS, decisión 71): una línea si es un valor,
    # columnas si es un cambio (un desvío, una variación por mes). Antes, el cambio iba en barras horizontales
    # ordenadas por valor y con 6 de 12 meses: no se veía si el desvío era sostenido o puntual
    por_tiempo = len(dimensiones) == 1 and dimensiones[0] in TEMPORALES
    temporal = por_tiempo and tipo == "barras"
    omitidos = 0
    if dimensiones_de(filas) == ["sucursal"]:
        maximo = max(maximo, MAXIMO_SUCURSALES)
    if not por_tiempo and len(filas) > maximo:
        omitidos = len(filas) - maximo
        # los resaltados entran siempre; el resto del lugar, para los que más se movieron
        filas = sorted(filas, key=lambda f: (not es_destacado(f, dimensiones, destacar), -abs(f[campo])))[:maximo]

    if por_tiempo:
        tipo = "linea" if temporal else "columnas"
        filas = sorted(filas, key=orden_temporal(resultado, dimensiones[0], filtros))
    else:
        filas = sorted(filas, key=lambda f: f[campo])  # barras horizontales: la mayor arriba

    nombres = [etiqueta(f, dimensiones) for f in filas]
    valores = [f[campo] for f in filas]
    millones = max(abs(v) for v in valores) >= 1e6  # una sola escala por gráfico

    alto = 2.2 if tipo in ("linea", "columnas") else max(1.5, 0.24 * len(filas) + 0.55)
    fig, ax = plt.subplots(figsize=(7, alto), dpi=200)
    if tipo == "linea":
        ax.plot(nombres, valores, color=AZUL, linewidth=2, marker="o", markersize=4)
        ax.yaxis.set_major_formatter(lambda v, _: formato(v, unidad, millones=millones))
        if unidad not in ("%", "pp") and min(valores) > 0:  # un monto desde cero: si no, un cambio chico parece un salto
            ax.set_ylim(0, max(valores) * 1.15)
        ax.grid(axis="y", color=GRILLA, linewidth=0.8)
    else:
        medida = resultado["medida"]
        resaltados = [es_destacado(f, dimensiones, destacar) if destacar else True for f in filas]
        # Un criterio visible: también va en color todo grupo que se movió al menos tanto como el resaltado más chico
        # del mismo lado. Si no, dos barras iguales salen una en rojo y otra en gris (decisión 68)
        for lado in (1, -1):
            # sobre lo que se lee en la etiqueta (redondeado), no sobre el valor exacto
            visto = [round(lado * v, 1) for v in valores]
            umbral = [x for x, r in zip(visto, resaltados) if r and x > 0]
            if destacar and umbral:
                resaltados = [r or x >= min(umbral) for x, r in zip(visto, resaltados)]
        cambio = tipo in ("divergente", "columnas")
        colores = [(color_de(medida, v) if cambio else AZUL) if r else GRIS for v, r in zip(valores, resaltados)]
        if tipo == "columnas":
            barras = ax.bar(nombres, valores, color=colores, width=0.6)
        else:
            barras = ax.barh(nombres, valores, color=colores, height=0.6)
        textos = [formato(v, unidad, cambio, millones) for v in valores]
        if campo == "variacion" and unidad == "pp" and all("actual" in f for f in filas):
            # La variación sola no dice si es grave: con el nivel al lado (decisión 68). Primero lo que mide la barra,
            # el cambio, y después el nivel: «+0,5 pp (1,4 %)» (decisión 104)
            textos = [f"{t} ({formato(f['actual'], '%')})" for f, t in zip(filas, textos)]
        etiquetas = ax.bar_label(barras, labels=textos, padding=3, fontsize=8)
        for texto, r in zip(etiquetas, resaltados):
            texto.set_color(TINTA if r else TINTA_SUAVE)
        if tipo == "columnas":
            ax.yaxis.set_visible(False)
            ax.axhline(0, color=TINTA_SUAVE, linewidth=0.8)
            if max(valores) <= 0:  # todo para abajo: los nombres arriba, junto al cero, y no lejos al pie
                ax.xaxis.tick_top()
            ax.margins(y=0.3)  # lugar para las etiquetas arriba y abajo
        else:
            ax.xaxis.set_visible(False)
            if tipo == "divergente":
                ax.axvline(0, color=TINTA_SUAVE, linewidth=0.8)
            ax.margins(x=0.45 if " (" in textos[0] else 0.25)  # lugar para las etiquetas de los dos lados

    if titulo:  # en el informe de una página el título va en el texto, como conclusión (decisión 54)
        fig.suptitle(titulo, x=0.02, ha="left", fontsize=11, color=TINTA)  # desde el borde: no lo corta una etiqueta
    ax.tick_params(colors=TINTA_SUAVE, labelsize=8, length=0)
    for lado in ax.spines.values():
        lado.set_visible(False)
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)
    return {"ruta": str(ruta), "titulo": titulo, "tipo": tipo, "campo": campo, "unidad": unidad,
            "datos": list(zip(nombres, valores)), "mostrados": len(filas), "omitidos": omitidos,
            "resaltados": [n for n, f in zip(nombres, filas) if destacar and es_destacado(f, dimensiones, destacar)]}
