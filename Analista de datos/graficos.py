"""Gráficos de los informes: los arma el código a partir del resultado de calcular(), nunca el modelo (semana 2).
Cada gráfico devuelve también los números que dibujó, para que se puedan rastrear hasta su consulta."""
import os

import duckdb
import matplotlib

matplotlib.use("Agg")  # sin ventana: solo archivos
import matplotlib.pyplot as plt

from procesador_capa_semantica import BASE

# Colores de la paleta de referencia (skill dataviz): una serie en azul; arriba/abajo de cero, azul y rojo
AZUL, ROJO = "#2a78d6", "#e34948"
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
    return {**proveedores, **{k: v[len(prefijo):] for k, v in sucursales.items()}}


NOMBRES = _nombres()


NOMBRE_DE = {"proveedor": "nombre_proveedor", "sucursal": "nombre_sucursal"}


def etiqueta(fila, dimensiones):
    """Nombre del grupo: los valores de sus dimensiones. Si vino el nombre del proveedor o de la sucursal, va solo el
    nombre: el código es ruido para la gerencia (decisión 68). Los productos sí llevan su sku: hay nombres repetidos."""
    partes = []
    for d in dimensiones:
        if NOMBRE_DE.get(d) in dimensiones:
            continue
        valor = fila[d]
        if d in NOMBRE_DE and NOMBRE_DE[d] not in dimensiones:  # vino el código solo: su nombre
            valor = NOMBRES.get(valor, valor)
        elif d == "nombre_sucursal":
            valor = NOMBRES.get(fila.get("sucursal"), valor)
        if d == "mes":
            valor = MESES[valor - 1]
        elif d == "mes_fiscal":
            valor = MESES_FISCALES[valor - 1]
        elif d == "trimestre_fiscal":
            valor = f"T{valor}"
        partes.append(str(valor))
    return " · ".join(partes)


def que_dibujar(resultado):
    """Elige el gráfico según la forma del resultado: (tipo, campo del valor, unidad del valor)."""
    filas = resultado["filas"]
    unidad = resultado["unidad"]
    if resultado["medida"] == "desvio_presupuesto_pct":
        return "divergente", "valor", "%"
    if resultado["medida"] == "efectos_margen":  # la variación del margen de cada grupo; los efectos van en el texto
        return "divergente", "variacion_pp", "pp"
    if "diferencia" in filas[0]:  # comparación de una medida aditiva: lo que subió o bajó cada grupo
        return "divergente", "diferencia", unidad
    if "variacion" in filas[0]:  # comparación de un % o un promedio: la variación (pp si es un %)
        return "divergente", "variacion", resultado.get("unidad_variacion", "%")
    return "barras", "valor", unidad


MAXIMO_GRUPOS = 6  # el informe es de una página: dos gráficos chicos (decisión 54)


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


def graficar(resultado, ruta, titulo, maximo=MAXIMO_GRUPOS, destacar=()):
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
    # Por tiempo, todos los períodos en orden y en el eje horizontal (IBCS, decisión 71): una línea si es un valor,
    # columnas si es un cambio (un desvío, una variación por mes). Antes, el cambio iba en barras horizontales
    # ordenadas por valor y con 6 de 12 meses: no se veía si el desvío era sostenido o puntual
    por_tiempo = len(dimensiones) == 1 and dimensiones[0] in TEMPORALES
    temporal = por_tiempo and tipo == "barras"
    omitidos = 0
    if not por_tiempo and len(filas) > maximo:
        omitidos = len(filas) - maximo
        # los resaltados entran siempre; el resto del lugar, para los que más se movieron
        filas = sorted(filas, key=lambda f: (not es_destacado(f, dimensiones, destacar), -abs(f[campo])))[:maximo]

    if por_tiempo:
        tipo = "linea" if temporal else "columnas"
        orden_temporal = lambda f: f[dimensiones[0]]
        desde = (resultado.get("periodo") or {}).get("desde")
        if dimensiones[0] == "mes" and desde:  # de nov-2025 a mar-2026: dic va antes que ene (empieza en el mes de desde)
            primero = int(desde[5:7])
            orden_temporal = lambda f: (f["mes"] - primero) % 12
        filas = sorted(filas, key=orden_temporal)
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
            # La variación sola no dice si es grave: con el nivel al lado, «1,4 % (+0,5 pp)» (decisión 68)
            textos = [f"{formato(f['actual'], '%')} ({t})" for f, t in zip(filas, textos)]
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
