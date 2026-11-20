"""El PDF de un informe: solo maqueta lo que recibe, no consulta ni decide nada (decisión 41).
Cada indicador y cada gráfico lleva el número de su consulta ([C1], [C2]…), que está con su SQL en el anexo."""
import re
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
import os
from xml.sax.saxutils import escape

import matplotlib
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

from graficos import NOMBRES, TINTA, TINTA_SUAVE, formato
from procesador_capa_semantica import sqls

# DejaVu (viene con matplotlib): la fuente estándar del PDF no tiene el «−» de los números
_FUENTES = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
for nombre, archivo in [("Texto", "DejaVuSans.ttf"), ("Texto-Negrita", "DejaVuSans-Bold.ttf"), ("Mono", "DejaVuSansMono.ttf")]:
    pdfmetrics.registerFont(TTFont(nombre, os.path.join(_FUENTES, archivo)))

FONDO_SUAVE = colors.HexColor("#f0efec")
ESTILOS = {
    "titulo": ParagraphStyle("titulo", fontName="Texto-Negrita", fontSize=18, leading=22, textColor=TINTA),
    "identificacion": ParagraphStyle("identificacion", fontName="Texto-Negrita", fontSize=7.5, leading=10,
                                     textColor=TINTA_SUAVE),
    "subtitulo": ParagraphStyle("subtitulo", fontName="Texto", fontSize=10, leading=14, textColor=TINTA_SUAVE),
    "seccion": ParagraphStyle("seccion", fontName="Texto-Negrita", fontSize=13, leading=16, textColor=TINTA,
                              spaceBefore=14, spaceAfter=6),
    "texto": ParagraphStyle("texto", fontName="Texto", fontSize=9.5, leading=13.5, textColor=TINTA, spaceAfter=4),
    "nota": ParagraphStyle("nota", fontName="Texto", fontSize=7, leading=9, textColor=TINTA_SUAVE),
    "kpi_valor": ParagraphStyle("kpi_valor", fontName="Texto-Negrita", fontSize=14, leading=17, textColor=TINTA),
    "kpi_nombre": ParagraphStyle("kpi_nombre", fontName="Texto", fontSize=8, leading=10, textColor=TINTA_SUAVE),
    "sql": ParagraphStyle("sql", fontName="Mono", fontSize=7, leading=9, textColor=TINTA),
    "mensaje": ParagraphStyle("mensaje", fontName="Texto-Negrita", fontSize=15, leading=19, textColor=TINTA),
    "bajada": ParagraphStyle("bajada", fontName="Texto", fontSize=10.5, leading=14.5, textColor=TINTA, spaceAfter=3,
                             leftIndent=11, firstLineIndent=-11),
    "prueba": ParagraphStyle("prueba", fontName="Texto-Negrita", fontSize=11.5, leading=14, textColor=TINTA,
                             spaceBefore=10, spaceAfter=2),
    "kpi_var": ParagraphStyle("kpi_var", fontName="Texto-Negrita", fontSize=9, leading=11, textColor=TINTA),
    # La jerarquía de la página (decisión 104): el mensaje, un número, rótulos chicos y el texto en peso normal
    # Aire entre secciones mayor que dentro de una sección: es lo que agrupa a la vista (proximidad, Gestalt)
    "rotulo": ParagraphStyle("rotulo", fontName="Texto-Negrita", fontSize=7.5, leading=10, textColor=TINTA,
                             spaceBefore=30, spaceAfter=8),
    "razon": ParagraphStyle("razon", fontName="Texto", fontSize=9.5, leading=13.5, textColor=TINTA, spaceAfter=6,
                            leftIndent=16, firstLineIndent=-16),
}




def p(texto, estilo="texto"):
    """Un párrafo. En el texto de Haiku, el guion delante de un número pasa a signo menos (como en las tarjetas y los
    gráficos) y las referencias [Cn] van chicas y en gris: siguen ahí, pero no cortan la lectura (decisión 68)."""
    # Los códigos de proveedor y sucursal («Molinos del Plata (PR01)», «PR05 sube») son ruido para la gerencia: va
    # el nombre, de la base. Los sku de producto quedan (hay nombres repetidos)
    texto = re.sub(r"\s?\((?:PR|S)\d+\)|\b(?:PR|S)\d+\s+(?=[A-ZÁÉÍÓÚÑ])", "", texto)
    texto = re.sub(r"\b(?:PR|S)\d+\b", lambda m: NOMBRES.get(m.group(), m.group()), texto)
    # Los % y los pp, con un decimal, como en las tarjetas y los gráficos: Haiku copia «−7,35 %» del resultado y la
    # tarjeta dice «−7,4 %» (IBCS: el mismo formato en toda la página). Redondeo comercial, como el formato de las tarjetas
    texto = re.sub(r"(\d+),(\d{2,})(?=\s?(?:%|pp))", lambda m: f"{Decimal(m[1] + '.' + m[2]).quantize(Decimal('0.1'), ROUND_HALF_UP)}".replace(".", ","), texto)
    texto = escape(re.sub(r"(?<![\w\-])-(?=\$?\s?\d)", "−", texto))
    # Un número no se separa de su unidad al cortar la línea («1,0» al final y «%» en la siguiente)
    texto = re.sub(r"(?<=\d) (?=(?:%|pp|M)\b|%)", "\u00a0", texto)
    texto = texto.replace("$ ", "$\u00a0")
    if estilo == "mensaje":  # el título no lleva referencias: sus cifras ya van citadas en los puntos
        texto = re.sub(r"\s?\[C\d+\]", "", texto)
    if estilo in ("texto", "bajada", "razon"):
        texto = re.sub(r"\s?\[(C\d+)\]", r'&#8202;<font size="5.5" color="#A0A4A8"><super>\1</super></font>', texto)
    return Paragraph(texto, ESTILOS[estilo])


def fecha(iso):
    """2025-08-01 → 01-08-2025: el formato de los pedidos, el esquema y los textos de Haiku (decisión 67)"""
    anio, mes, dia = iso.split("-")
    return f"{dia}-{mes}-{anio}"


def cifra(ind, campo="valor", unidad="unidad", con_signo=None):
    en_millones = ind[unidad] == "ARS" and abs(ind[campo]) >= 1e6  # $ 663,1 M; un costo por unidad, en pesos
    return formato(ind[campo], ind[unidad], ind.get("con_signo", False) if con_signo is None else con_signo, en_millones)


def contra_en_palabras(contra, nombre=""):
    """«vs T2 AF2025» → «que en el T2 AF2025»; «vs presupuesto» → «que el presupuesto». Sin lo que ya dice el nombre
    («Ventas, mismas sucursales» con «vs AF2025, mismas sucursales»)."""
    resto = re.sub(r"^(vs\.?|contra)\s+", "", (contra or "").strip())
    resto = ", ".join(parte for parte in resto.split(", ") if parte.lower() not in nombre.lower())
    if not resto:
        return ""
    if "presupuesto" in resto.lower():
        return "que el presupuesto"
    return f"que en {resto}" if resto.lower().startswith(("el ", "la ", "los ", "las ")) else f"que en el {resto}"


def cambio_en_palabras(ind):
    """«0,2 pp menos», «3,9 % más»: sin el signo suelto, que no dice contra qué (decisión 104)."""
    variacion = cifra(ind, "variacion", "unidad_variacion", False).lstrip("+−-")
    return f"{variacion} {'menos' if ind['variacion'] < 0 else 'más'}"


def numero_principal(principal, complemento=None):
    """El número del mensaje, en palabras, debajo del título, con el tamaño y el color del texto (decisión 104). El
    margen % se dice como lo entiende cualquiera: «de cada $ 100 vendidos quedaron $ 26,8, contra $ 27,0». Con su
    complemento, el mismo dato en la otra escala: el glosario pide el margen % junto a los pesos, y «bajó el %» sin
    «subió en pesos» se lee como una pérdida que no es."""
    sup = lambda c: f'<font size="5.5" color="{TINTA_SUAVE}"><super>{c}</super></font>'
    negrita = lambda x: f'<font name="Texto-Negrita">{escape(x)}</font>'
    contra = contra_en_palabras(principal.get("contra"), principal["nombre"])
    if principal["unidad"] == "%" and "margen" in principal["nombre"].lower():
        texto = f"De cada $ 100 vendidos quedaron {negrita('$ ' + cifra(principal).replace(' %', ''))} de margen{sup(principal['consulta'])}"
        if principal.get("anterior") is not None:
            texto += f", contra $ {formato(principal['anterior'], '%').replace(' %', '')} {contra.removeprefix('que ')}"
    else:
        nombre = re.sub(r"\s*%$", "", principal["nombre"])
        texto = f"{escape(nombre)}: {negrita(cifra(principal))}{sup(principal['consulta'])}"
        if principal.get("variacion") is not None:
            texto += f", {escape(cambio_en_palabras(principal))} {escape(contra)}".rstrip()
    texto += "."
    if complemento:
        if complemento.get("variacion") is not None:
            sube = complemento["variacion"] >= 0
            texto += (f" En pesos, el margen {'creció' if sube else 'bajó'} "
                      f"{escape(cifra(complemento, 'variacion', 'unidad_variacion', False).lstrip('+−-'))}: "
                      f"{escape(cifra(complemento))}{sup(complemento['consulta'])}.")
        else:
            texto += f" En pesos, {escape(cifra(complemento))}{sup(complemento['consulta'])}."
    return [Paragraph(texto, ESTILOS["texto"])]


def indicadores(lista):
    """Una fila de tarjetas: nombre, valor y, debajo, la variación contra qué (en color si es buena o mala, IBCS)."""
    celdas = []
    for ind in lista:
        en_millones = lambda v, u: u == "ARS" and abs(v) >= 1e6  # $ 663,1 M; un costo por unidad, en pesos
        valor = formato(ind["valor"], ind["unidad"], ind.get("con_signo", False), en_millones(ind["valor"], ind["unidad"]))
        celda = [p(ind["nombre"], "kpi_nombre"), p(valor, "kpi_valor")]
        if ind.get("variacion") is not None:
            variacion = formato(ind["variacion"], ind["unidad_variacion"], True,
                                en_millones(ind["variacion"], ind["unidad_variacion"]))
            estilo = ParagraphStyle("var", parent=ESTILOS["kpi_var"], textColor=colors.HexColor(ind["color"]))
            celda.append(Paragraph(escape(f"{variacion} ") + f'<font name="Texto" color="{TINTA_SUAVE}">'
                                   + escape(ind.get("contra") or "") + "</font>", estilo))
        celda.append(p(f"[{ind['consulta']}]", "nota"))
        celdas.append(celda)
    tabla = Table([celdas], colWidths=[17 * cm / len(celdas)] * len(celdas))
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), FONDO_SUAVE),
        ("LINEAFTER", (0, 0), (-2, -1), 3, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return [tabla]


def anexo(consultas, archivo_sql):
    """Una línea por consulta citada: número y qué calcula. El SQL completo va en un archivo al lado del PDF."""
    return [KeepTogether([p("Anexo: consultas usadas", "seccion"),  # el título no queda solo al pie de una página
            p(f"Cada cifra del informe sale de una de estas consultas. Su SQL, con los parámetros para volver a "
              f"correrla, está en {archivo_sql}.", "nota"), Spacer(1, 4),
            *[p(f"[{c['id']}] {c['descripcion']}", "nota") for c in consultas]])]


def escribir_sql(consultas, ruta):
    """El SQL de cada consulta del anexo, con sus parámetros, listo para volver a correr."""
    lineas = []
    for c in consultas:
        lineas += [f"-- [{c['id']}] {c['descripcion']}"]
        for parte, sql, parametros in sqls(c["resultado"]):  # en una comparación, uno por período
            lineas += [f"-- {parte.rstrip(': ')}" if parte else "", f"-- parámetros: {parametros}", sql.rstrip(";") + ";", ""]
    Path(ruta).write_text("\n".join(l for l in lineas if l is not None) + "\n")


def armar_pdf(informe, ruta):
    """Una página que se lee de arriba abajo (decisiones 54 y 104): el mensaje como título, qué hacer, tres
    indicadores con su comparación y 2 o 3 puntos, cada uno con su prueba al lado (el punto es el titular de su
    gráfico). Después, el anexo con las consultas. informe: titulo, identificacion, pedido, bajada,
    indicadores [{nombre, valor, unidad, variacion, unidad_variacion, color, contra, consulta}],
    puntos [{texto, grafico: {ruta, consulta, nota} o nada}], supuestos [str], consultas [{id, descripcion, resultado}]."""
    ids = {c["id"] for c in informe["consultas"]}
    citadas = ([informe["principal"]["consulta"]] + ([informe["complemento"]["consulta"]] if informe.get("complemento") else [])
               + [x["grafico"]["consulta"] for x in informe["puntos"] if x.get("grafico")])
    sueltas = [c for c in citadas if c not in ids]
    if sueltas:  # una cifra sin su consulta en el anexo rompe la regla central
        raise ValueError(f"Citan consultas que no están en el anexo: {', '.join(sueltas)}")

    # De arriba abajo, cada cosa en su nivel (decisión 104): el mensaje; el número del mensaje y su contexto; por qué,
    # numerado (cada razón una vez); qué hacer, como consecuencia; y las pruebas, con un rótulo que dice qué muestran
    historia = [p(informe["identificacion"].upper(), "identificacion"), Spacer(1, 4), p(informe["titulo"], "mensaje"),
                Spacer(1, 5), *([p(informe["bajada"])] if informe.get("bajada") else numero_principal(informe["principal"], informe.get("complemento"))),
                p("POR QUÉ", "rotulo")]
    graficos, numero = [], 0
    for i, punto in enumerate(informe["puntos"], 1):
        referencia = ""
        if punto.get("mismo_grafico"):
            referencia = f'  <font color="{TINTA_SUAVE}">→&nbsp;gráfico&nbsp;{punto["mismo_grafico"]}</font>'
        if punto.get("grafico"):
            numero += 1
            graficos.append((numero, punto["grafico"]))
            referencia = f'  <font color="{TINTA_SUAVE}">→&nbsp;gráfico&nbsp;{numero}</font>'
        parrafo = p(f"{i}.  {punto['texto']}", "razon")  # p() escapa el texto; la referencia se agrega como marcado
        historia.append(Paragraph(parrafo.text + referencia, ESTILOS["razon"]))
    for numero, grafico in graficos:
        imagen = Image(grafico["ruta"])
        escala = 16 * cm / imagen.drawWidth  # casi de ancho completo: el gráfico es la prueba
        imagen.drawWidth, imagen.drawHeight = imagen.drawWidth * escala, imagen.drawHeight * escala
        fuente = f"Fuente: consulta [{grafico['consulta']}]" + (f" · {grafico['nota']}" if grafico.get("nota") else "")
        historia.append(KeepTogether([p(f"GRÁFICO {numero} · {grafico['rotulo']}", "rotulo"), imagen, Spacer(1, 3),
                                      p(fuente, "nota")]))
    # Los supuestos son de método, como las consultas: van con el anexo, no en la página del mensaje
    archivo_sql = Path(ruta).with_name("consultas.sql")
    escribir_sql(informe["consultas"], archivo_sql)
    historia += [PageBreak()]
    if informe.get("pedido"):
        historia += [p("Pedido", "seccion"), p(f"«{informe['pedido']}»", "nota"), Spacer(1, 6)]
    if informe.get("supuestos"):
        historia += [p("Supuestos", "seccion"), *[p("• " + s, "nota") for s in informe["supuestos"]], Spacer(1, 6)]
    historia += anexo(informe["consultas"], archivo_sql.name)

    def pie(canvas, doc):
        canvas.setFont("Texto", 7)
        canvas.setFillColor(TINTA_SUAVE)
        canvas.drawString(2 * cm, 1.2 * cm, "Almacenes del Sur · Analista de datos")
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")

    doc = SimpleDocTemplate(str(ruta), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm,
                            bottomMargin=2 * cm, title=informe["titulo"])
    doc.build(historia, onFirstPage=pie, onLaterPages=pie)
    return str(ruta)
