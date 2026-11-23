"""Interfaz mínima (decisión 101): la misma puerta que el chat de la terminal, con el comprobante de cada número al lado.
- Preguntar: el chat a la izquierda; a la derecha, «De dónde sale» la última respuesta: cada consulta en castellano
  (qué se midió, de qué, cuándo), su SQL y su resultado, y los controles en código que pasó.
- Cómo sé que funciona: el resultado de cada test, leído de su traza.
El diseño sigue la bibliografía revisada (README, decisión 101) y el boceto que eligió el usuario: lo mínimo, con los
comprobantes a la vista.

Uso: .venv/bin/streamlit run analista/interfaz.py      (cada pregunta gasta lo mismo que en el chat de la terminal)"""
import asyncio
import base64
import contextlib
import re
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import informes
import registro
from agente import resumen
from controles import (FECHA_ESCRITA, MAX_SIN_CONTROL, grupos_sin_filtro, numeros_del_texto, periodo_fuera_de_la_base, valores_de,
                       valores_que_no_estan)
from datetime import date, timedelta

from explicar import MESES, explicar
from informe_programado import informes_del
from procesador_capa_semantica import sqls, ver_modelo
from puerta import Clasificacion, Conversacion, al_historial, contexto_para_coordinador
from sugerir import sugerencias

st.set_page_config(page_title="Analista de datos · Almacenes del Sur", page_icon="📊", layout="wide")
st.markdown("""<style>
#MainMenu, footer, header [data-testid="stToolbar"] {visibility: hidden;}
.block-container {padding-top: 1.5rem;}
div[data-testid="stCaptionContainer"] p {margin-bottom: 0;}
.stButton button {font-size: 0.85rem; padding: 0.15rem 0.6rem;}
/* Los dos recuadros: superficies grises sobre el fondo, como la elevación del tema oscuro de Material Design */
.st-key-caja_chat, .st-key-caja_evidencia {background: #1E1E1E; border-radius: 10px;}
.st-key-caja_chat [data-testid="stChatMessage"] {background: #2C2C2C;}
[data-testid="stCaptionContainer"] p {color: #A8A8A8;}
.st-key-caja_chat button, .st-key-caja_evidencia button {background: #2C2C2C; border: 1px solid #4A4A4A;}
.st-key-caja_chat button:hover, .st-key-caja_evidencia button:hover {border-color: #81C995;}
/* El verde desaturado lleva texto oscuro: con texto blanco, el verde anterior daba 3,4:1 y no pasaba WCAG */
button[kind="primary"], button[kind="primary"] * {color: #0B1F13 !important;}
</style>""", unsafe_allow_html=True)
LOG = Path(f"salidas/interfaz-{registro.CORRIDA}.log")


# ---------- La conversación ----------
def estado():
    s = st.session_state
    if "conversacion" not in s:
        nueva_conversacion(s)
    return s


def nueva_conversacion(s):
    s.conversacion, s.turnos, s.pendiente, s.descargar = Conversacion(varios_turnos=True), [], None, None


def generar_informe(s, pedido):
    """Un informe en PDF pedido con el botón: va directo al coordinador (decisiones 42 y 53), con la conversación como
    contexto, y queda en el chat como un turno más, con sus consultas a la derecha."""
    numero = len(s.turnos) + 1
    registro.CASO.set(f"interfaz-{numero}")
    inicio = time.monotonic()
    carpeta = f"salidas/interfaz-{registro.CORRIDA}-informe-{numero}"
    contexto = contexto_para_coordinador(Clasificacion(motivo="pedido con el botón de informe", tipo="informe"),
                                         s.conversacion.anteriores)
    with open(LOG, "a") as log, contextlib.redirect_stdout(log):
        try:
            resultado = asyncio.run(informes.atender(pedido, carpeta, "Informe", contexto, "informe"))
        except informes.NoSeEntrega as motivo:
            resultado = {"texto": f"No pude armar el informe: {motivo}.", "consultas": [], "salida": None}
    respuesta = {"pregunta": pedido, "ruta": "coordinador", "tipo": "informe", **resultado}
    s.conversacion.historial = [*s.conversacion.historial, *al_historial(pedido, respuesta)]
    s.conversacion.anteriores.append((pedido, respuesta["texto"]))
    costo = sum(l["costo_usd"] for l in registro.leer(registro.LLAMADAS)
                if l.get("corrida") == registro.CORRIDA and l.get("caso") == f"interfaz-{numero}")
    s.turnos.append({"pregunta": pedido, "respuesta": respuesta, "segundos": time.monotonic() - inicio, "costo": costo,
                     "sugerencias": []})
    s.descargar = ruta_pdf(respuesta)


def ruta_pdf(r):
    salida = Path(r["salida"]) if r.get("salida") else None
    pdf = (salida if salida.suffix == ".pdf" else salida.parent / "informe.pdf") if salida else None
    return pdf if pdf and pdf.exists() else None


def descarga_automatica(pdf):
    """Baja el PDF sin otro clic (un enlace que se toca solo). Si el navegador lo bloquea, queda el botón."""
    datos = base64.b64encode(pdf.read_bytes()).decode()
    components.html(f"""<script>
      const a = document.createElement('a');
      a.href = 'data:application/pdf;base64,{datos}'; a.download = 'informe_almacenes_del_sur.pdf';
      document.body.appendChild(a); a.click();
    </script>""", height=0)


def preguntar(s, texto):
    """Un turno por la puerta, como el chat de la terminal. Lo que imprime el agente va al .log, no a la pantalla."""
    numero = len(s.turnos) + 1
    registro.CASO.set(f"interfaz-{numero}")
    inicio = time.monotonic()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as log, contextlib.redirect_stdout(log):
        respuesta = asyncio.run(s.conversacion.turno(texto))
    costo = sum(l["costo_usd"] for l in registro.leer(registro.LLAMADAS)
                if l.get("corrida") == registro.CORRIDA and l.get("caso") == f"interfaz-{numero}")
    s.turnos.append({"pregunta": texto, "respuesta": respuesta, "segundos": time.monotonic() - inicio, "costo": costo,
                     "sugerencias": sugerencias(respuesta)})


# ---------- Lo que se muestra de cada respuesta ----------
def sin_rutas(texto):
    """Sin la línea de la ruta del archivo («PDF: salidas/2026…»): sus dígitos parecerían números sin respaldo."""
    return "\n".join(l for l in texto.splitlines() if not l.startswith(("Diagnóstico: ", "PDF: "))).strip()


def pie(turno):
    r = turno["respuesta"]
    return (f"{r.get('tipo')} → {r.get('ruta')} · {len(r['consultas'])} consulta(s) · "
            + f"US$ {turno['costo']:.4f}".replace(".", ",") + f" · {turno['segundos']:.0f} s")


def supuestos(r):
    datos = r.get("registro")
    return list(datos.supuestos) if datos else []


def avisos(r):
    return [c["resultado"]["aviso"] for c in r["consultas"] if isinstance(c.get("resultado"), dict) and c["resultado"].get("aviso")]


def sin_respaldo(r):
    """Los números del texto que no salen de ninguna consulta (el criterio del control de la decisión 49)."""
    valores = valores_de([c["resultado"] for c in r["consultas"]])
    sueltos = []
    for valor, tolerancia, escrito in numeros_del_texto(FECHA_ESCRITA.sub(" ", sin_rutas(r["texto"]))):
        if (valor.is_integer() and valor <= MAX_SIN_CONTROL and "," not in escrito) or 1900 <= valor <= 2100:
            continue
        if not any(abs(valor - abs(v)) <= tolerancia for v in valores):
            sueltos.append(escrito)
    return sueltos


def controles(turno):
    """Los controles en código que pasó la respuesta (decisiones 49, 95, 97 y 116), en una línea."""
    r = turno["respuesta"]
    numeros = not sin_respaldo(r)
    filtros = not grupos_sin_filtro(turno["pregunta"], r["consultas"], supuestos(r))
    afuera = periodo_fuera_de_la_base(turno["pregunta"])
    no_esta = valores_que_no_estan(turno["pregunta"])
    return " · ".join([f"{'✓' if numeros else '✗'} números con respaldo", f"{'✓' if filtros else '✗'} filtros usados",
                       "✓ período dentro de la base" if not afuera else "✓ período fuera de la base, sin números"]
                      + ["✓ lo pedido no está en la base, sin números"] * bool(no_esta))


def mostrar_pdf(r):
    pdf = ruta_pdf(r)
    if pdf:
        datos = pdf.read_bytes()
        st.markdown(f'<iframe src="data:application/pdf;base64,{base64.b64encode(datos).decode()}" width="100%" '
                    'height="520" style="border:1px solid #ddd;border-radius:6px"></iframe>', unsafe_allow_html=True)
        st.download_button("Descargar el PDF", datos, file_name="informe_almacenes_del_sur.pdf", mime="application/pdf",
                           key=f"bajar-{pdf}")


# ---------- Pestaña 1 ----------
def de_donde_sale(turno):
    st.markdown("##### De dónde sale")
    r = turno["respuesta"]
    if not r["consultas"]:
        st.caption("Esta respuesta no usó consultas.")
    for numero, consulta in enumerate(r["consultas"], 1):
        lineas = explicar(consulta).splitlines()
        lineas = lineas[:4] if consulta["tool"] == "calcular" else lineas[:1]
        st.markdown(f"**Consulta {consulta.get('id') or numero}**  \n" + "  \n".join(lineas))
        izquierda, derecha = st.columns(2)
        with izquierda.popover("SQL", width="stretch"):
            for _, sql, parametros in sqls(consulta["resultado"]):
                st.code(sql + (f"\n-- parámetros: {parametros}" if parametros else ""), language="sql")
        with derecha.popover("Resultado", width="stretch"):
            if consulta["tool"] == "calcular" and resumen(consulta["resultado"]):
                st.markdown(resumen(consulta["resultado"]))
            else:
                st.json(consulta["resultado"], expanded=False)
    st.caption(controles(turno))


ALTO = 560  # los dos recuadros, de la misma altura y con su propio scroll
OTRO = "Otro (lo escribo yo)"


def informes_listos(s):
    """Los informes para elegir con un toque: los mismos cuatro de los informes programados (decisión 66, cada uno
    responde otra pregunta), con los últimos períodos completos de la base; y, si hay conversación, uno sobre ella."""
    hasta = date.fromisoformat(ver_modelo()["cobertura"]["ventas_hasta"])
    ultimo_domingo = hasta - timedelta(days=(hasta.weekday() + 1) % 7)
    opciones = {}
    if s.turnos:
        opciones[f"Sobre lo que venimos hablando ({s.turnos[-1]['pregunta'][:50]})"] = \
            f"Informe ejecutivo sobre: {s.turnos[-1]['pregunta']}"
    semanal = informes_del(ultimo_domingo + timedelta(days=1))[0]
    opciones[f"Semana del {semanal[1]:%d-%m} al {semanal[2]:%d-%m-%Y}: qué requiere atención"] = semanal[3]
    lunes_de_cierre = hasta + timedelta(days=1 + (7 - (hasta + timedelta(days=1)).weekday()) % 7)
    for clave, desde, fin, pedido in informes_del(lunes_de_cierre)[1:]:
        if fin > hasta:
            continue
        if clave.startswith("mes-"):
            opciones[f"{MESES[desde.month - 1].capitalize()} de {desde.year}: cumplimiento del presupuesto"] = pedido
        elif clave.startswith("trimestre-"):
            af, t = clave.split("-")[1:]
            opciones[f"{t} del {af}: por qué se movió el margen"] = pedido
        else:
            opciones[f"{clave.split('-')[1]} completo: de dónde vino el crecimiento"] = pedido
    opciones[OTRO] = ""
    return opciones


def pestania_preguntar():
    s = estado()
    # Los botones van en su propia fila, arriba de los dos recuadros: así los recuadros empiezan a la misma altura
    borrar, informe, _ = st.columns([1, 1, 3])
    if borrar.button("Nueva conversación", width="stretch"):
        nueva_conversacion(s)
        st.rerun()
    with informe.popover("Generar informe", width="stretch"):
        opciones = informes_listos(s)
        elegido = st.radio("Qué informe querés", list(opciones), index=0)
        pedido = st.text_area("Contame qué informe necesitás", height=90) if elegido == OTRO else opciones[elegido]
        if st.button("Generar el PDF", type="primary", disabled=not pedido.strip()):
            with st.spinner("Armando el informe (alrededor de un minuto)…"):
                generar_informe(s, pedido)
            st.rerun()
    if s.descargar:
        descarga_automatica(s.descargar)
        s.descargar = None
    chat, evidencia = st.columns([3, 2], gap="medium")
    with chat:
        with st.container(border=True, height=ALTO, key="caja_chat"):
            if not s.turnos:
                cobertura = ver_modelo()["cobertura"]
                st.caption(f"Ventas, margen, presupuesto, stock y promociones, de {cobertura['ventas_desde']} a "
                           f"{cobertura['ventas_hasta']}. También diagnósticos («¿por qué…?») e informes en PDF. "
                           "No hay datos de clientes ni de tickets.")
            for turno in s.turnos:
                r = turno["respuesta"]
                with st.chat_message("user", avatar=":material/person:"):
                    st.markdown(turno["pregunta"])
                with st.chat_message("assistant", avatar=":material/query_stats:"):
                    st.markdown(sin_rutas(r["texto"]).replace("\n", "  \n"))
                    mostrar_pdf(r)
                    st.caption(pie(turno))
                    for aviso in avisos(r):
                        st.markdown(f"⚠ {aviso}")
                    for supuesto in supuestos(r):
                        st.caption(f"Supuso: {supuesto}")
            if s.turnos and s.turnos[-1]["sugerencias"]:
                for j, sugerencia in enumerate(s.turnos[-1]["sugerencias"]):
                    if st.button(sugerencia, key=f"sug-{len(s.turnos)}-{j}"):
                        s.pendiente = sugerencia
                        st.rerun()
        pregunta = st.chat_input("¿Qué querés saber?") or s.pendiente
        if pregunta:
            s.pendiente = None
            with st.spinner("Consultando la base…"):
                preguntar(s, pregunta)
            st.rerun()
    with evidencia:
        with st.container(border=True, height=ALTO, key="caja_evidencia"):
            if s.turnos:
                de_donde_sale(s.turnos[-1])
            else:
                st.markdown("##### De dónde sale")
                st.caption("Acá aparece, para cada respuesta, la consulta de la que sale cada número: qué se midió, "
                           "de qué y cuándo, con su SQL y su resultado, y los controles que pasó.")


# ---------- Pestaña 2 ----------
TESTS = [  # (test, qué prueba, traza, patrón del resultado)
    ("Corrida completa", "las 20 preguntas, 5 conversaciones y 3 informes del curso", "corrida_completa.md", r"\*\*28 casos[^*]+\*\*"),
    ("Datos nuevos", "el agente sobre un año simulado con cosas que nunca pasaron", "agente_anio.md", r"\*\*\d+ de \d+\*\* pasan"),
    ("Errores de carga", "errores plantados al azar en 30 bases", "deteccion.md", r"\*\*Total:[^*]+\*\*"),
    ("Lenguaje", "la misma pregunta dicha de 4 maneras", "lenguaje.md", r"\*\*Variantes[^*]+\*\*"),
    ("Fechas", "año fiscal, «el mes pasado», ambiguas, fuera de la base", "fechas.md", r"\*\*\d+ de \d+\*\* pasan"),
    ("No inventar", "preguntas que la base no puede responder", "no_inventar.md", r"\*\*\d+ de \d+\*\* pasan"),
    ("Ataques", "inyección, borrar datos, leer archivos", "ataques.md", r"\*\*Capas de código[^*]+\*\*"),
    ("Consistencia", "cada caso 10 veces: ¿acierta siempre o solo a veces? (pass^k)", "consistencia.md",
     r"\*\*(?:De trabajo|Reserva)[^*]+\*\*"),
    ("Conversación", "qué arrastra de un turno al otro y qué suelta", "conversacion.md", r"\*\*Turnos correctos[^*]+\*\*"),
    ("La puerta", "quién responde cada pregunta", "matriz_puerta.md", r"\*\*Camino correcto[^*]+\*\*"),
    ("Costo", "por pregunta, de los registros", "costos.md", r"mediana US\$ [^)]+"),
]


def pestania_calidad():
    st.caption("Cada resultado sale de un test que se vuelve a correr con un comando (`evaluacion/robustez/`), calificado por código "
               "contra valores calculados con SQL antes de correr el agente.")
    filas = []
    for test, que, archivo, patron in TESTS:
        ruta = Path("trazas") / archivo
        hallados = re.findall(patron, ruta.read_text()) if ruta.exists() else []  # consistencia: trabajo y reserva
        filas.append({"Test": test, "Qué prueba": que,
                      "Resultado": " · ".join(h.replace("**", "").strip() for h in hallados) or "—"})
    st.dataframe(filas, hide_index=True, width="stretch")


st.markdown("### Almacenes del Sur · Analista de datos")
preguntar_tab, calidad_tab = st.tabs(["Preguntar", "Cómo sé que funciona"])
with preguntar_tab:
    pestania_preguntar()
with calidad_tab:
    pestania_calidad()
