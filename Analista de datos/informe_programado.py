"""Informes que corren solos (semana 4), por calendario real (decisión 65). Cada lunes:
    semanal:    la semana que acaba de cerrar: qué requiere atención (quiebres, sucursales y productos que cayeron)
    mensual:    el primer lunes del mes, el mes anterior: cumplimiento del presupuesto y dónde no se cumplió
    trimestral: el primer lunes de agosto, noviembre, febrero y mayo, el trimestre fiscal: por qué se movió el margen
    anual:      el primer lunes de mayo, el año fiscal: de dónde vino el crecimiento
Si la base no cubre el período, no arma un informe viejo: avisa que faltan datos.
Lo lanza un temporizador de systemd los lunes a las 8 (programado/). A mano, o para simular otra fecha:
    .venv/bin/python informe_programado.py [--hoy 2026-05-04]
Cada informe va a salidas/programado/<período>/ (con ejecucion.log); cada corrida suma líneas a
salidas/programado/historial.txt y avisa con una notificación."""
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import duckdb

from procesador_capa_semantica import BASE
from verificar_base import verificar

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]
INTENTOS = 2  # Haiku varía entre corridas y la API puede fallar: un segundo intento antes de darlo por perdido
LIMITE_SEGUNDOS = 15 * 60  # medido: un informe tarda alrededor de 1,5 minutos; si pasa de 15, algo se trabó
CARPETA = Path("salidas/programado")
NOMBRES = {"semana": "Informe semanal", "mes": "Informe mensual", "trimestre": "Informe trimestral",
           "anio": "Informe anual"}  # el encabezado del PDF: qué informe es (decisión 70)
CIERRE_DE_TRIMESTRE = {8: 1, 11: 2, 2: 3, 5: 4}  # mes en que se informa → trimestre fiscal que cerró (glosario)


def af(dia):
    """Año fiscal de un día: empieza el 1 de mayo y se nombra por el año en que termina (glosario)."""
    return dia.year + (dia.month >= 5)


def fecha(dia):
    return dia.strftime("%d-%m-%Y")


def informes_del(lunes):
    """[(clave, desde, hasta, pedido)] de los informes que tocan ese lunes. La clave nombra la carpeta."""
    informes = []
    desde, hasta = lunes - timedelta(days=7), lunes - timedelta(days=1)
    antes = desde - timedelta(days=364)  # 52 semanas: lunes contra lunes, no fecha contra fecha
    # Cada informe responde otra pregunta (decisión 66), para la gerencia (68): el semanal, qué requiere atención;
    # el mensual, si se cumplió el presupuesto; el trimestral, por qué se movió el margen; el anual, de dónde vino el
    # crecimiento
    informes.append((f"semana-{desde}", desde, hasta,
                     f"Preparame un informe ejecutivo de la semana del lunes {fecha(desde)} al domingo {fecha(hasta)}, "
                     f"sobre qué requiere la atención de la gerencia esta semana: la tasa de quiebre de stock de la semana, por región y por "
                     f"proveedor; las sucursales con mayor caída de ventas netas; y los productos con caída fuerte. Todo "
                     f"contra la misma semana del año anterior (del lunes {fecha(antes)} al domingo "
                     f"{fecha(antes + timedelta(days=6))}). Las ventas netas y el margen del total, solo como contexto."))
    if lunes.day <= 7:  # primer lunes del mes: el mes anterior
        hasta = lunes.replace(day=1) - timedelta(days=1)
        desde = hasta.replace(day=1)
        mes = f"{MESES[desde.month - 1]} de {desde.year}"
        informes.append((f"mes-{desde:%Y-%m}", desde, hasta,
                         f"Preparame un informe de cumplimiento del presupuesto de {mes}: el desvío de las ventas netas "
                         f"contra el presupuesto, por categoría y por región, y dónde se concentra; el acumulado del "
                         f"AF{af(desde)} hasta {mes} contra su presupuesto; y si algún desvío parece un error de carga, "
                         f"marcarlo. Las ventas netas y el margen contra {MESES[desde.month - 1]} de {desde.year - 1}, "
                         f"solo como contexto."))
        if lunes.month in CIERRE_DE_TRIMESTRE:
            trimestre, anio_fiscal = CIERRE_DE_TRIMESTRE[lunes.month], af(hasta)
            meses = desde.year * 12 + desde.month - 1 - 2  # dos meses antes del último mes del trimestre
            inicio = date(meses // 12, meses % 12 + 1, 1)
            informes.append((f"trimestre-AF{anio_fiscal}-T{trimestre}", inicio, hasta,
                             f"Preparame un informe del T{trimestre} del AF{anio_fiscal} sobre por qué se movió el "
                             f"margen: la variación del margen bruto % contra el T{trimestre} del AF{anio_fiscal - 1}, "
                             f"separada en efecto precio y efecto costo, por categoría y por proveedor; la marca propia "
                             f"contra las marcas de proveedores; y si el cambio de mix entre categorías explica parte "
                             f"de la variación. Las ventas netas, solo como contexto."))
        if lunes.month == 5:
            anio_fiscal = af(hasta)
            informes.append((f"anio-AF{anio_fiscal}", date(anio_fiscal - 1, 5, 1), hasta,
                             f"Preparame un informe del AF{anio_fiscal} completo sobre de dónde vino el crecimiento: "
                             f"las ventas netas contra el AF{anio_fiscal - 1}, separando las sucursales comparables "
                             f"de las aperturas; qué regiones y sucursales crecieron más y menos; qué categorías "
                             f"ganaron o perdieron participación; y las ventas del año contra el presupuesto. El margen, "
                             f"solo como contexto."))
    return informes


def avisar(titulo, texto):
    """Notificación de escritorio; si no hay sesión gráfica, alcanza con el historial."""
    try:
        subprocess.run(["notify-send", titulo, texto], timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        pass


def anotar(linea):
    CARPETA.mkdir(parents=True, exist_ok=True)
    with open(CARPETA / "historial.txt", "a") as historial:
        historial.write(f"{datetime.now():%Y-%m-%d %H:%M} · {linea}\n")


def correr(clave, pedido):
    """Corre informes.py con reintento y límite de tiempo. Devuelve 'bien' o el motivo de la falla."""
    carpeta = CARPETA / clave
    carpeta.mkdir(parents=True, exist_ok=True)
    with open(carpeta / "ejecucion.log", "a") as log:
        for intento in range(1, INTENTOS + 1):
            log.write(f"\n===== {datetime.now():%Y-%m-%d %H:%M:%S} · intento {intento} · {pedido}\n")
            log.flush()
            try:
                nombre = NOMBRES[clave.split("-")[0]]
                codigo = subprocess.run([sys.executable, "informes.py", pedido, str(carpeta), "--nombre", nombre],
                                        stdout=log, stderr=subprocess.STDOUT, timeout=LIMITE_SEGUNDOS).returncode
            except subprocess.TimeoutExpired:
                codigo = "límite de tiempo"
            log.write(f"===== resultado: {'bien' if codigo == 0 else codigo}\n")
            if codigo == 0 and (carpeta / "informe.pdf").exists():
                return "bien"
    return f"falló ({codigo}, {INTENTOS} intentos; ver {carpeta / 'ejecucion.log'})"


def main():
    hoy = date.fromisoformat(sys.argv[sys.argv.index("--hoy") + 1]) if "--hoy" in sys.argv else date.today()
    simulado = " (fecha simulada)" if hoy != date.today() else ""
    # Si la PC estaba apagada el lunes, el temporizador corre después: cuenta el último lunes
    lunes = hoy - timedelta(days=hoy.weekday())

    # Antes de gastar en el modelo: si la base quedó mal después de una ingesta, no se arma nada con ella
    resultados, _ = verificar()
    rotos = [f"{nombre} ({malas})" for nombre, malas in resultados if malas]
    if rotos:
        anotar(f"lunes {lunes}{simulado} · no corrió: la base no pasa verificar_base.py · " + "; ".join(rotos))
        avisar("Los informes no corrieron", "La base no pasa verificar_base.py: " + "; ".join(rotos))
        sys.exit(1)
    with duckdb.connect(BASE, read_only=True) as con:
        primero, ultimo = con.execute("SELECT MIN(fecha), MAX(fecha) FROM ventas").fetchone()

    resumen = []
    for clave, desde, hasta, pedido in informes_del(lunes):
        if (CARPETA / clave / "informe.pdf").exists():  # ya salió (por ejemplo, si se corre dos veces el mismo día)
            estado = "ya estaba"
        elif hasta > ultimo or desde < primero:
            # Calendario real: si faltan datos, se avisa; no se informa otro período en su lugar
            estado = f"faltan datos (la base llega hasta el {fecha(ultimo)})"
        else:
            inicio = time.monotonic()
            estado = correr(clave, pedido)
            estado += f" · {time.monotonic() - inicio:.0f} s"
        anotar(f"lunes {lunes}{simulado} · {clave} · {estado}")
        resumen.append(f"{clave}: {estado}")

    todo_bien = all(r.split(": ", 1)[1].startswith(("bien", "ya estaba")) for r in resumen)
    avisar("Informes listos" if todo_bien else "Informes con avisos", "\n".join(resumen))
    print("\n".join(resumen))
    sys.exit(0 if todo_bien else 1)


if __name__ == "__main__":
    main()
