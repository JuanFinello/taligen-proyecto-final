"""Interfaz mínima (decisión 101): la misma puerta que el chat de la terminal, con el comprobante de cada número al lado.
El chat a la izquierda; a la derecha, «De dónde sale» la última respuesta: cada consulta en castellano
(qué se midió, de qué, cuándo), su SQL y su resultado, y los controles en código que pasó.
El diseño sigue la bibliografía revisada (README, decisión 101) y el boceto que eligió el usuario: lo mínimo, con los
comprobantes a la vista.

Uso: .venv/bin/streamlit run analista/interfaz.py      (cada pregunta gasta lo mismo que en el chat de la terminal)"""
import asyncio
import base64
import contextlib
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
from sugerir import Memoria, sugerencias

st.set_page_config(page_title="Analista de datos · Almacenes del Sur", page_icon="📊", layout="wide")
st.markdown("""<style>
#MainMenu, footer, header [data-testid="stToolbar"] {visibility: hidden;}
.block-container {padding-top: 1.5rem;}
div[data-testid="stCaptionContainer"] p {margin-bottom: 0;}
.stButton button {font-size: 0.85rem; padding: 0.15rem 0.6rem;}
/* Los dos recuadros: superficies grises sobre el fondo, como la elevación del tema oscuro de Material Design */
.st-key-caja_chat, .st-key-caja_evidencia {background: #1E1E1E; border-radius: 10px;}
/* Quién habla, en dos grises: la pregunta, más clara (más arriba en la elevación); la respuesta, más oscura */
.st-key-caja_chat [data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) {background: #3A3A3A;}
.st-key-caja_chat [data-testid="stChatMessage"]:has([aria-label="Chat message from assistant"]) {background: #262626;}
/* El avatar del agente es el personaje completo en blanco, en el mismo cuadro que el ícono de persona */
[data-testid="stChatMessageAvatarImage"] {box-sizing: border-box; padding: 3px; object-fit: contain;
  background: #0E1117; border: 1px solid #31333F;}
[data-testid="stCaptionContainer"] p {color: #A8A8A8;}
.st-key-caja_chat button, .st-key-caja_evidencia button {background: #2C2C2C; border: 1px solid #4A4A4A;}
.st-key-caja_chat button:hover, .st-key-caja_evidencia button:hover {border-color: #81C995;}
/* El verde desaturado lleva texto oscuro: con texto blanco, el verde anterior daba 3,4:1 y no pasaba WCAG */
button[kind="primary"], button[kind="primary"] * {color: #0B1F13 !important;}
</style>""", unsafe_allow_html=True)
LOG = Path(f"salidas/interfaz-{registro.CORRIDA}.log")
AVATAR_AGENTE = str(Path(__file__).with_name("imagenes") / "agente.png")  # el personaje de la presentación, en blanco


# ---------- La conversación ----------
def estado():
    s = st.session_state
    if "conversacion" not in s:
        nueva_conversacion(s)
    return s


def nueva_conversacion(s):
    s.conversacion, s.turnos, s.pendiente, s.descargar = Conversacion(varios_turnos=True), [], None, None
    s.memoria = Memoria()  # lo ya sugerido y preguntado, para no repetir (decisión 121)


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
                     "sugerencias": sugerencias(respuesta, s.memoria, texto)})


# ---------- Lo que se muestra de cada respuesta ----------
def sin_rutas(texto):
    """Sin la línea de la ruta del archivo («PDF: salidas/2026…»): sus dígitos parecerían números sin respaldo."""
    return "\n".join(l for l in texto.splitlines() if not l.startswith(("Diagnóstico: ", "PDF: "))).strip()


def pie(turno):
    r = turno["respuesta"]
    return (f"{r.get('tipo')} → {r.get('ruta')} · {len(r['consultas'])} {'consulta' if len(r['consultas']) == 1 else 'consultas'} · "
            + f"US$ {turno['costo']:.4f}".replace(".", ",") + f" · {turno['segundos']:.0f} s")


def supuestos(r):
    datos = r.get("registro")
    return list(datos.supuestos) if datos else []


def avisos(r):
    """Los avisos de las consultas, cada uno una sola vez: en un informe, varias consultas pueden traer el mismo (el
    presupuesto sospechoso de un mes aparece en cada consulta que lo suma) y antes se mostraba repetido."""
    return list(dict.fromkeys(c["resultado"]["aviso"] for c in r["consultas"]
                              if isinstance(c.get("resultado"), dict) and c["resultado"].get("aviso")))


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


# ---------- La pantalla ----------
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


CONVERSACION = "Sobre esta conversación"


SEMANAL, MENSUAL = "Semanal: qué requiere atención", "Mensual: cumplimiento del presupuesto"


def cobertura():
    """Primer y último día con ventas en la base."""
    c = ver_modelo()["cobertura"]
    return date.fromisoformat(c["ventas_desde"]), date.fromisoformat(c["ventas_hasta"])


def semanas_posibles():
    """(primer lunes, último lunes) de las semanas completas que tienen la misma semana del año anterior en la base
    (el semanal compara contra 52 semanas antes, informe_programado.informes_del)."""
    desde, hasta = cobertura()
    primero = desde + timedelta(days=364)
    primero += timedelta(days=(7 - primero.weekday()) % 7)
    ultimo = hasta - timedelta(days=(hasta.weekday() + 1) % 7) - timedelta(days=6)
    return primero, ultimo


def meses_posibles():
    """Los meses completos que tienen el mismo mes del año anterior en la base (el mensual lo usa de contexto), del
    más reciente al más viejo."""
    desde, hasta = cobertura()
    meses, mes = [], date(hasta.year, hasta.month, 1)
    while date(mes.year - 1, mes.month, 1) >= desde:
        fin = (mes.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        if fin <= hasta:
            meses.append(mes)
        mes = (mes - timedelta(days=1)).replace(day=1)
    return meses


def pedido_semanal(dia):
    """El pedido del informe semanal de la semana (lunes a domingo) que contiene ese día."""
    lunes = dia - timedelta(days=dia.weekday())
    return informes_del(lunes + timedelta(days=7))[0][3]


def pedido_mensual(mes):
    """El pedido del informe mensual de ese mes (el mismo texto que el informe programado)."""
    siguiente = (mes.replace(day=28) + timedelta(days=4)).replace(day=1)
    primer_lunes = siguiente + timedelta(days=(7 - siguiente.weekday()) % 7)
    return next(p for clave, _, _, p in informes_del(primer_lunes) if clave == f"mes-{mes:%Y-%m}")


def informes_listos(s):
    """Los informes para elegir: uno sobre la conversación del chat, el semanal y el mensual de los informes
    programados (decisión 66, cada uno responde otra pregunta), con el período que elija el usuario, y uno escrito
    por el usuario."""
    preguntas = [t["pregunta"] for t in s.turnos]
    return {CONVERSACION: ("Informe ejecutivo con lo que vimos en esta conversación: " + "; ".join(preguntas))
            if preguntas else "", SEMANAL: "", MENSUAL: "", OTRO: ""}


def pestania_preguntar():
    s = estado()
    # Los botones van en su propia fila, arriba de los dos recuadros: así los recuadros empiezan a la misma altura
    borrar, informe, _ = st.columns([1, 1, 3])
    if borrar.button("Nueva conversación", width="stretch"):
        nueva_conversacion(s)
        st.rerun()
    with informe.popover("Generar informe", width="stretch"):
        opciones = informes_listos(s)
        elegido = st.radio("Qué informe querés", list(opciones), index=0 if s.turnos else 1)
        if elegido == SEMANAL:
            primero, ultimo = semanas_posibles()
            dia = st.date_input("Un día de la semana", value=ultimo, min_value=primero, max_value=ultimo + timedelta(days=6),
                                format="DD/MM/YYYY")
            lunes = dia - timedelta(days=dia.weekday())
            st.caption(f"Semana del lunes {lunes:%d-%m-%Y} al domingo {lunes + timedelta(days=6):%d-%m-%Y}, contra la misma semana del año anterior")
            pedido = pedido_semanal(dia)
        elif elegido == MENSUAL:
            meses = meses_posibles()
            mes = st.selectbox("Mes", meses, format_func=lambda m: f"{MESES[m.month - 1]} de {m.year}")
            st.caption("Con el acumulado del año fiscal y el mismo mes del año anterior como contexto")
            pedido = pedido_mensual(mes)
        else:
            pedido = st.text_area("Contame qué informe necesitás", height=90) if elegido == OTRO else opciones[elegido]
        if elegido == CONVERSACION and not pedido:
            st.caption("Primero hacé alguna pregunta en el chat.")
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
                with st.chat_message("assistant", avatar=AVATAR_AGENTE):
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


st.markdown("### Almacenes del Sur · Analista de datos")
pestania_preguntar()
