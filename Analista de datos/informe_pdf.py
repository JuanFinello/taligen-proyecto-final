"""El PDF de un informe: solo maqueta lo que recibe, no consulta ni decide nada (decisión 41).
Cada indicador y cada gráfico lleva el número de su consulta ([C1], [C2]…), que está con su SQL en el anexo."""
import json
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
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer,
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
    "identificacion": ParagraphStyle("identificacion", fontName="Texto-Negrita", fontSize=8.5, leading=11,
                                     textColor=TINTA_SUAVE),
    "subtitulo": ParagraphStyle("subtitulo", fontName="Texto", fontSize=10, leading=14, textColor=TINTA_SUAVE),
    "seccion": ParagraphStyle("seccion", fontName="Texto-Negrita", fontSize=13, leading=16, textColor=TINTA,
                              spaceBefore=14, spaceAfter=6),
    "texto": ParagraphStyle("texto", fontName="Texto", fontSize=10, leading=14, textColor=TINTA, spaceAfter=4),
    "nota": ParagraphStyle("nota", fontName="Texto", fontSize=8, leading=10, textColor=TINTA_SUAVE),
    "kpi_valor": ParagraphStyle("kpi_valor", fontName="Texto-Negrita", fontSize=14, leading=17, textColor=TINTA),
    "kpi_nombre": ParagraphStyle("kpi_nombre", fontName="Texto", fontSize=8, leading=10, textColor=TINTA_SUAVE),
    "sql": ParagraphStyle("sql", fontName="Mono", fontSize=7, leading=9, textColor=TINTA),
    "mensaje": ParagraphStyle("mensaje", fontName="Texto-Negrita", fontSize=17, leading=21, textColor=TINTA),
    "bajada": ParagraphStyle("bajada", fontName="Texto", fontSize=10.5, leading=14.5, textColor=TINTA, spaceAfter=3,
                             leftIndent=11, firstLineIndent=-11),
    "prueba": ParagraphStyle("prueba", fontName="Texto-Negrita", fontSize=11.5, leading=14, textColor=TINTA,
                             spaceBefore=10, spaceAfter=2),
    "kpi_var": ParagraphStyle("kpi_var", fontName="Texto-Negrita", fontSize=9, leading=11, textColor=TINTA),
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
    if estilo == "mensaje":  # el título no lleva referencias: sus cifras ya van citadas en los puntos
        texto = re.sub(r"\s?\[C\d+\]", "", texto)
    if estilo in ("texto", "bajada"):
        texto = re.sub(r"\s?\[(C\d+)\]", rf'<font size="6.5" color="{TINTA_SUAVE}"><super>\1</super></font>', texto)
    return Paragraph(texto, ESTILOS[estilo])


def fecha(iso):
    """2025-08-01 → 01-08-2025: el formato de los pedidos, el esquema y los textos de Haiku (decisión 67)"""
    anio, mes, dia = iso.split("-")
    return f"{dia}-{mes}-{anio}"


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
    """Una página que se lee de arriba abajo (decisión 54): el mensaje como título, el porqué, qué hacer, tres
    indicadores con su comparación y una o dos pruebas (gráfico con el grupo clave resaltado y una oración).
    Después, el anexo con las consultas. informe: titulo, identificacion, pedido, puntos [str], acciones [str], indicadores [{nombre,
    valor, unidad, variacion, unidad_variacion, color, contra, consulta}], pruebas [{titulo, grafico, texto,
    consulta, nota}], supuestos [str], consultas [{id, descripcion, resultado}]."""
    ids = {c["id"] for c in informe["consultas"]}
    citadas = [i["consulta"] for i in informe["indicadores"]] + [s["consulta"] for s in informe["pruebas"]]
    sueltas = [c for c in citadas if c not in ids]
    if sueltas:  # una cifra sin su consulta en el anexo rompe la regla central
        raise ValueError(f"Citan consultas que no están en el anexo: {', '.join(sueltas)}")

    historia = [p(informe["identificacion"].upper(), "identificacion"), Spacer(1, 2), p(informe["titulo"], "mensaje"),
                Spacer(1, 6), *[p("•  " + punto, "bajada") for punto in informe["puntos"]]]
    acciones = [Paragraph('<font name="Texto-Negrita">Qué hacer</font>', ESTILOS["texto"]),
                *[p("▸ " + a) for a in informe["acciones"]]]
    caja = Table([[acciones]], colWidths=[17 * cm])
    caja.setStyle(TableStyle([("LINEBEFORE", (0, 0), (0, 0), 2.5, colors.HexColor(TINTA)),
                              ("LEFTPADDING", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 2),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    historia += [Spacer(1, 4), caja, Spacer(1, 10), *indicadores(informe["indicadores"])]
    for prueba in informe["pruebas"]:
        imagen = Image(prueba["grafico"])
        escala = 15 * cm / imagen.drawWidth  # dos gráficos y el resto del informe entran en una página
        imagen.drawWidth, imagen.drawHeight = imagen.drawWidth * escala, imagen.drawHeight * escala
        fuente = f"Fuente: consulta [{prueba['consulta']}]" + (f" · {prueba['nota']}" if prueba.get("nota") else "")
        historia.append(KeepTogether([p(prueba["titulo"], "prueba"), imagen, p(fuente, "nota"), Spacer(1, 2),
                                      p(prueba["texto"])]))
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
