"""Gráficos de los informes: los arma el código a partir del resultado de calcular(), nunca el modelo (semana 2).
Cada gráfico devuelve también los números que dibujó, para que se puedan rastrear hasta su consulta."""
import matplotlib

matplotlib.use("Agg")  # sin ventana: solo archivos
import matplotlib.pyplot as plt

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
              "costo_unitario_actual", "variacion_precio_pct", "variacion_costo_unitario_pct"}  # lo que calcular() agrega a cada fila; el resto son dimensiones
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


def etiqueta(fila, dimensiones):
    """Nombre del grupo: los valores de sus dimensiones (el nombre del proveedor, si vino, va con su código)."""
    partes = []
    for d in dimensiones:
        valor = fila[d]
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
    textos = [str(fila[d]).lower() for d in dimensiones] + [etiqueta(fila, dimensiones).lower()]
    return any(d.lower() in t for d in destacar for t in textos)


def graficar(resultado, ruta, titulo, maximo=MAXIMO_GRUPOS, destacar=()):
    """Un PNG a partir de un resultado agrupado de calcular(). Devuelve qué dibujó, con sus números.
    Fuera de las líneas de tiempo, muestra como máximo `maximo` grupos: los resaltados y los que más se movieron.
    Con `destacar`, solo esos grupos van en color y el resto en gris (Storytelling with Data)."""
    if not resultado.get("filas"):
        raise ValueError("Solo se grafica un resultado agrupado (con agrupar_por)")
    filas = resultado["filas"]
    # Las dimensiones son las columnas que no son números calculados (nombre_proveedor queda dentro de la etiqueta)
    dimensiones = [d for d in filas[0] if d not in CALCULADOS]
    tipo, campo, unidad = que_dibujar(resultado)
    filas = [f for f in filas if f[campo] is not None]
    temporal = len(dimensiones) == 1 and dimensiones[0] in TEMPORALES and tipo == "barras"
    omitidos = 0
    if not temporal and len(filas) > maximo:
        omitidos = len(filas) - maximo
        # los resaltados entran siempre; el resto del lugar, para los que más se movieron
        filas = sorted(filas, key=lambda f: (not es_destacado(f, dimensiones, destacar), -abs(f[campo])))[:maximo]

    if temporal:
        tipo = "linea"
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

    alto = 2.2 if tipo == "linea" else max(1.5, 0.24 * len(filas) + 0.55)
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
        colores = [(color_de(medida, v) if tipo == "divergente" else AZUL) if r else GRIS
                   for v, r in zip(valores, resaltados)]
        barras = ax.barh(nombres, valores, color=colores, height=0.6)
        etiquetas = ax.bar_label(barras, labels=[formato(v, unidad, tipo == "divergente", millones) for v in valores],
                                 padding=3, fontsize=8)
        for texto, r in zip(etiquetas, resaltados):
            texto.set_color(TINTA if r else TINTA_SUAVE)
        ax.xaxis.set_visible(False)
        if tipo == "divergente":
            ax.axvline(0, color=TINTA_SUAVE, linewidth=0.8)
        ax.margins(x=0.25)  # lugar para las etiquetas de los dos lados

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
