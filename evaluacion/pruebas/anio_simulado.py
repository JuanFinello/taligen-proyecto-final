"""Un año simulado, el AF2027 (mayo de 2026 a abril de 2027), con eventos que no existen en la historia (decisión 88).
Sobre una copia de la base: salidas/anio/limpia.duckdb. La original no se toca.

Cómo se arman los datos (el método del test 1, decisión 87, llevado a un año):
- Ingenuo estacional: cada día copia el mismo día de la semana de 728 días antes (el AF2025), por el crecimiento
  anual medido en la base (comparables, AF2026 contra AF2025) dos veces. Se copia el AF2025 y no el AF2026 porque el
  AF2026 tiene dos hechos conocidos (el error de carga del presupuesto de enero y el quiebre de Lácteos del Norte de
  septiembre) que se repetirían como si fueran nuevos.
- S39 y S40 (abrieron en 2025) copian 364 días antes desde su primer aniversario; antes, su último mismo día de la
  semana de la base, sin crecimiento.
- S41 (Oeste, express, abre el 04-05-2026) copia a S40 por la curva de apertura medida en S40: su mes k desde la
  apertura rindió tanto de su nivel actual (feb–abr 2026).
- Ruido lognormal de media 1 con semilla fija, redondeo estocástico, importes recalculados (comun.py).

Eventos nuevos (ninguno pasó en la historia de la base), en lugares y fechas sorteados y anotados en eventos.json:
cierre de una sucursal, aumento de precios de una categoría, una categoría nueva (Mascotas), un producto
discontinuado, una región sin ventas unos días (un corte) y un cambio gradual del mix hacia la marca propia.
Más dos hechos conocidos, para medir: un quiebre de stock y una caída de demanda de una categoría en una región.

Uso: .venv/bin/python evaluacion/pruebas/anio_simulado.py      (arma la base, la verifica y escribe salidas/anio/resultado.md)"""
import json
import os
import random
import shutil
import sys
import time
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(RAIZ / "analista"), str(RAIZ / "evaluacion")]  # los módulos del proyecto
CARPETA = Path("salidas/anio")
LIMPIA = CARPETA / "limpia.duckdb"
os.environ["BASE_ALMACENES"] = str(LIMPIA)  # antes de importar el procesador

import duckdb  # noqa: E402

from comun import MESES, RUIDO, cargar, redondeo_estocastico, ruido  # noqa: E402

ORIGINAL = "Data/base/almacenes_del_sur.duckdb"
SEMILLA = 2027
DESDE, HASTA = date(2026, 5, 1), date(2027, 4, 30)
ULTIMO_DE_LA_BASE = date(2026, 4, 30)
DOS_ANIOS, UN_ANIO = 728, 364  # múltiplos de 7: el mismo día de la semana
NUEVA = {"sucursal_id": "S41", "nombre": "Almacenes del Sur Las Lomas", "region": "Oeste", "formato": "express",
         "superficie_m2": 410, "fecha_apertura": date(2026, 5, 4), "analoga": "S40"}
MASCOTAS = {
    "categoria": "Mascotas", "proveedor_id": "PR17", "proveedor": "Distribuidora Patitas S.A.",
    "lanzamiento": date(2026, 8, 1), "escala": 0.6,
    "productos": [  # (descripción, marca, subcategoría, precio de lista)
        ("Alimento para perros adultos Huellitas 3 kg", "Huellitas", "Alimento para perros", 9800.0),
        ("Alimento para perros cachorros Huellitas 1,5 kg", "Huellitas", "Alimento para perros", 6400.0),
        ("Alimento para gatos Bigotes 1,5 kg", "Bigotes", "Alimento para gatos", 7200.0),
        ("Snacks para perros Huellitas 200 g", "Huellitas", "Alimento para perros", 2100.0),
        ("Arena sanitaria Gatuna 4 kg", "Gatuna", "Higiene de mascotas", 5300.0),
        ("Piedras sanitarias Gatuna 2 kg", "Gatuna", "Higiene de mascotas", 3600.0)],
}
PRECIOS = {"desde": date(2026, 10, 1), "aumento": 1.15, "unidades": 0.95}  # +15 % de precio, −5 % de unidades
MIX = {"desde": date(2026, 11, 1), "propia": 0.40, "terceros": -0.08}  # al final del año: +40 % y −8 % de unidades
CORTE_DIAS = 3
QUIEBRE = {"semanas": 3, "queda": 0.15}
CAIDA = {"factor": 0.7, "desde": date(2026, 11, 1), "hasta": date(2027, 1, 31)}  # el T3 fiscal


def primero_de_mes(d, meses):
    m = d.month - 1 + meses
    return date(d.year + m // 12, m % 12 + 1, 1)


def medir(con):
    """Los factores salen de la base."""
    q = lambda sql, *p: con.execute(sql, list(p)).fetchone()[0]
    viejas = "sucursal_id IN (SELECT sucursal_id FROM sucursales WHERE fecha_apertura < '2024-05-01')"
    anual = q(f"""SELECT SUM(CASE WHEN fecha >= '2025-05-01' THEN importe_neto END)
                       / SUM(CASE WHEN fecha < '2025-05-01' THEN importe_neto END) FROM ventas WHERE {viejas}""")
    # La curva de apertura sin estacionalidad (revisión del 19-11): el mes k de S40 contra su nivel de feb–abr de 2026,
    # dividido por lo mismo en las sucursales viejas. Sin esto, el pico de diciembre de S40 (su mes 5) pasaba a S41 en octubre
    meses = con.execute(f"""SELECT DATE_TRUNC('month', fecha)::DATE AS m,
                                   SUM(importe_neto) FILTER (WHERE sucursal_id = ?) AS nueva,
                                   SUM(importe_neto) FILTER (WHERE {viejas}) AS viejas
                            FROM ventas WHERE fecha >= (SELECT fecha_apertura FROM sucursales WHERE sucursal_id = ?)
                            GROUP BY 1 ORDER BY 1""", [NUEVA["analoga"], NUEVA["analoga"]]).fetchall()
    nivel = [(n, v) for m, n, v in meses if m >= date(2026, 2, 1)]
    nivel_nueva, nivel_viejas = sum(n for n, _ in nivel) / len(nivel), sum(v for _, v in nivel) / len(nivel)
    curva = [(n / nivel_nueva) / (v / nivel_viejas) for _, n, v in meses]
    return {"crecimiento_anual": round(anual, 4), "curva_apertura": [round(x, 3) for x in curva]}


def sortear(con, rng):
    """Dónde y cuándo cae cada evento. Sin superponerse: cada uno se tiene que poder ver solo."""
    q = lambda sql: [r[0] for r in con.execute(sql).fetchall()]
    viejas = q("SELECT sucursal_id FROM sucursales WHERE fecha_apertura < '2024-05-01' ORDER BY 1")
    categorias = q("SELECT DISTINCT categoria FROM productos ORDER BY 1")
    regiones = q("SELECT DISTINCT region FROM sucursales ORDER BY 1")
    cierre = {"sucursal": rng.choice(viejas),
              "fecha": str(rng.choice([date(2026, 10, 1), date(2026, 11, 1), date(2026, 12, 1), date(2027, 1, 1)]))}
    precios = {"categoria": rng.choice(categorias), **{k: str(v) if isinstance(v, date) else v for k, v in PRECIOS.items()}}
    caida = {"categoria": rng.choice([c for c in categorias if c != precios["categoria"]]),
             "region": rng.choice(regiones), "factor": CAIDA["factor"], "desde": str(CAIDA["desde"]), "hasta": str(CAIDA["hasta"])}
    region_corte = rng.choice([r for r in regiones if r != caida["region"]])
    inicio_corte = DESDE + timedelta(days=rng.randrange(61, 122))  # julio o agosto
    corte = {"region": region_corte, "dias": [str(inicio_corte + timedelta(days=i)) for i in range(CORTE_DIAS)]}
    otras = [s for s in viejas if s != cierre["sucursal"]]
    subcategorias = q(f"SELECT DISTINCT subcategoria FROM productos WHERE categoria NOT IN "
                      f"('{precios['categoria']}', '{caida['categoria']}') ORDER BY 1")
    lunes = [DESDE + timedelta(days=i) for i in range(365) if (DESDE + timedelta(days=i)).weekday() == 0
             and date(2026, 9, 1) <= DESDE + timedelta(days=i) <= date(2027, 3, 1)]
    inicio = rng.choice(lunes)
    quiebre = {"sucursal": rng.choice(otras), "subcategoria": rng.choice(subcategorias), "desde": str(inicio),
               "hasta": str(inicio + timedelta(weeks=QUIEBRE["semanas"] - 1)), "se_vende": QUIEBRE["queda"]}
    discontinuado = {"sku": rng.choice(q(f"""SELECT sku FROM productos WHERE NOT es_marca_propia AND categoria NOT IN
                         ('{precios['categoria']}', '{caida['categoria']}') AND subcategoria <> '{quiebre['subcategoria']}'
                         ORDER BY 1""")), "desde": "2027-01-01"}
    analogos = rng.sample(q("SELECT sku FROM productos WHERE categoria = 'Almacén' AND NOT es_marca_propia ORDER BY 1"), 6)
    return {"cierre": cierre, "precios": precios, "categoria_nueva": {"analogos": analogos}, "discontinuado": discontinuado,
            "corte": corte, "mix": {k: str(v) if isinstance(v, date) else v for k, v in MIX.items()},
            "quiebre": quiebre, "caida": caida}


def origen(sucursal, apertura, dia):
    """(día de origen, crecimiento en años) para un día nuevo de una sucursal que no es la nueva."""
    if apertura <= dia - timedelta(days=DOS_ANIOS):
        return dia - timedelta(days=DOS_ANIOS), 2
    if apertura <= dia - timedelta(days=UN_ANIO):
        return dia - timedelta(days=UN_ANIO), 1
    atras = dia
    while atras > ULTIMO_DE_LA_BASE:  # su último mismo día de la semana en la base
        atras -= timedelta(days=7)
    return atras, 0


def armar():
    CARPETA.mkdir(parents=True, exist_ok=True)
    if LIMPIA.exists():
        LIMPIA.unlink()
    shutil.copy(ORIGINAL, LIMPIA)
    rng = random.Random(SEMILLA)
    con = duckdb.connect(str(LIMPIA))
    factores = medir(con)
    ev = sortear(con, rng)
    g = factores["crecimiento_anual"]
    curva = factores["curva_apertura"]
    def rampa(dia):
        """Cuánto rinde S41 en su mes k desde la apertura: lo que rindió S40 en su mes k (desde el mes 10, su nivel)."""
        k = (dia.year - 2026) * 12 + dia.month - 5
        return curva[k] if k < len(curva) else 1.0

    # Dimensiones: calendario, sucursal nueva, proveedor y productos de la categoría nueva
    con.execute(f"""INSERT INTO fechas SELECT d::DATE, YEAR(d), MONTH(d), DAY(d), ({MESES})[MONTH(d)], ISODOW(d),
                       YEAR(d) + (MONTH(d) >= 5)::INT, (MONTH(d) + 7) % 12 + 1, ((MONTH(d) + 7) % 12) // 3 + 1,
                       DATE_TRUNC('week', d)::DATE
                   FROM generate_series(DATE '{DESDE}', DATE '{HASTA}', INTERVAL 1 DAY) t(d)""")
    con.execute("INSERT INTO sucursales VALUES (?, ?, ?, ?, ?, ?)",
                [NUEVA[k] for k in ("sucursal_id", "nombre", "region", "formato", "superficie_m2", "fecha_apertura")])
    con.execute("INSERT INTO proveedores VALUES (?, ?)", [MASCOTAS["proveedor_id"], MASCOTAS["proveedor"]])
    ultimo = int(con.execute("SELECT MAX(CAST(SUBSTR(sku, 2) AS INT)) FROM productos").fetchone()[0])
    mascotas = {}  # sku nuevo → (sku análogo, precio)
    for i, (descripcion, marca, subcategoria, precio) in enumerate(MASCOTAS["productos"]):
        sku = f"P{ultimo + 1 + i:04d}"
        con.execute("INSERT INTO productos VALUES (?, ?, ?, ?, ?, ?, ?, false)",
                    [sku, descripcion, marca, MASCOTAS["proveedor_id"], MASCOTAS["categoria"], subcategoria, precio])
        mascotas[sku] = (ev["categoria_nueva"]["analogos"][i], precio)
    ev["categoria_nueva"].update({"categoria": MASCOTAS["categoria"], "proveedor": MASCOTAS["proveedor_id"],
                                  "lanzamiento": str(MASCOTAS["lanzamiento"]), "skus": list(mascotas)})

    productos = {s: (cat, sub, precio, propia) for s, cat, sub, precio, propia in con.execute(
        "SELECT sku, categoria, subcategoria, precio_lista, es_marca_propia FROM productos").fetchall()}
    sucursales = {s: (reg, ap) for s, reg, ap in con.execute("SELECT sucursal_id, region, fecha_apertura FROM sucursales").fetchall()}
    cierre_suc, cierre = ev["cierre"]["sucursal"], date.fromisoformat(ev["cierre"]["fecha"])
    corte_dias = {date.fromisoformat(d) for d in ev["corte"]["dias"]}
    q_suc, q_sub = ev["quiebre"]["sucursal"], ev["quiebre"]["subcategoria"]
    q_desde, q_hasta = date.fromisoformat(ev["quiebre"]["desde"]), date.fromisoformat(ev["quiebre"]["hasta"])
    disc, disc_desde = ev["discontinuado"]["sku"], date.fromisoformat(ev["discontinuado"]["desde"])
    abierta = lambda s, dia: sucursales[s][1] <= dia and not (s == cierre_suc and dia >= cierre)

    def mix(propia, dia):
        t = min(max((dia - MIX["desde"]).days / (HASTA - MIX["desde"]).days, 0), 1)
        return 1 + t * (MIX["propia"] if propia else MIX["terceros"])

    # Promociones: las de origen, corridas con otro id
    promos = {p[0]: p for p in con.execute("SELECT * FROM promociones").fetchall()}
    siguiente = [int(con.execute("SELECT MAX(CAST(SUBSTR(promocion_id, 6) AS INT)) FROM promociones").fetchone()[0])]
    nuevas, corridas = [], {}

    def promo_corrida(promo_id, corrimiento):
        if (promo_id, corrimiento) not in corridas:
            p = promos[promo_id]
            siguiente[0] += 1
            nuevo, desde = f"PROMO{siguiente[0]:03d}", p[4] + timedelta(days=corrimiento)
            nuevas.append((nuevo, f"{p[1].rsplit(' ', 1)[0]} {desde.month:02d}/{desde.year}", p[2], p[3], desde,
                           p[5] + timedelta(days=corrimiento)))
            corridas[(promo_id, corrimiento)] = (nuevo, p[3])
        return corridas[(promo_id, corrimiento)]

    def fila(dia, sucursal, sku, tipo, unidades, costo_unitario, promo, precio):
        pct = promo[1] if promo else 0.0
        bruto = round(unidades * precio, 2)
        descuento = round(bruto * pct / 100, 2)
        return (dia, sucursal, sku, tipo, unidades, bruto, descuento, round(bruto - descuento, 2),
                round(costo_unitario * unidades, 2), promo[0] if promo else None)

    # Ventas, mes por mes (para no tener el año entero de origen en memoria)
    ventas_por_mes = {}
    mes = DESDE
    while mes <= HASTA:
        dias = [mes + timedelta(days=i) for i in range(31) if (mes + timedelta(days=i)).month == mes.month]
        origenes = {(s, d): origen(s, ap, d) for d in dias for s, (_, ap) in sucursales.items() if s != NUEVA["sucursal_id"]}
        fechas_origen = sorted({o[0] for o in origenes.values()})
        filas_origen = {}
        for f in con.execute("""SELECT fecha, sucursal_id, sku, tipo_movimiento, unidades, costo, promocion_id FROM ventas
                                WHERE fecha IN (SELECT UNNEST(?::DATE[])) ORDER BY fecha, sucursal_id, sku, tipo_movimiento""",
                             [fechas_origen]).fetchall():
            filas_origen.setdefault((f[0], f[1]), []).append(f)
        ventas = []
        for dia in dias:
            del_dia = {}
            for sucursal in sorted(sucursales):
                region = sucursales[sucursal][0]
                if not abierta(sucursal, dia) or (region == ev["corte"]["region"] and dia in corte_dias):
                    continue
                if sucursal == NUEVA["sucursal_id"]:  # la nueva: S40 de ese día, por su curva de apertura
                    for (d, _, sku, tipo, u, b, de, n, c, pr) in del_dia.get(NUEVA["analoga"], []):
                        cantidad = redondeo_estocastico(abs(u) * rampa(dia), rng)
                        if cantidad:
                            precio = b / u
                            promo = (pr, de / b * 100) if pr else None
                            ventas.append(fila(dia, sucursal, sku, tipo, cantidad if tipo == "venta" else -cantidad,
                                               c / u, promo, precio))
                    continue
                desde_dia, anios = origenes[(sucursal, dia)]
                propias = []
                for _, _, sku, tipo, unidades, costo, promo_id in filas_origen.get((desde_dia, sucursal), []):
                    if sku == disc and dia >= disc_desde:
                        continue
                    categoria, subcategoria, precio, propia = productos[sku]
                    factor = g ** anios * ruido(rng) * mix(propia, dia)
                    if sucursal == q_suc and subcategoria == q_sub and q_desde < dia <= q_hasta + timedelta(days=6):
                        factor *= QUIEBRE["queda"]
                    if (categoria == ev["caida"]["categoria"] and region == ev["caida"]["region"]
                            and CAIDA["desde"] <= dia <= CAIDA["hasta"]):
                        factor *= CAIDA["factor"]
                    if categoria == ev["precios"]["categoria"] and dia >= PRECIOS["desde"]:
                        precio, factor = precio * PRECIOS["aumento"], factor * PRECIOS["unidades"]
                    cantidad = redondeo_estocastico(abs(unidades) * factor, rng)
                    if not cantidad:
                        continue
                    promo = promo_corrida(promo_id, (dia - desde_dia).days) if promo_id and tipo == "venta" else None
                    propias.append(fila(dia, sucursal, sku, tipo, cantidad if tipo == "venta" else -cantidad,
                                        costo / unidades, promo, precio))
                # La categoría nueva: las ventas de sus análogos, a escala y con su precio
                if dia >= MASCOTAS["lanzamiento"]:
                    por_sku = {f[2]: f for f in propias if f[3] == "venta"}
                    for sku, (analogo, precio) in mascotas.items():
                        if analogo in por_sku:
                            a = por_sku[analogo]
                            n = redondeo_estocastico(a[4] * MASCOTAS["escala"], rng)
                            if n:
                                propias.append(fila(dia, sucursal, sku, "venta", n, precio * a[8] / a[5], None, precio))
                del_dia[sucursal] = propias
                ventas += propias
        ventas_por_mes[mes] = len(ventas)
        cargar(con, "ventas", ventas, CARPETA)
        mes = primero_de_mes(mes, 1)

    # Stock: la foto de cada lunes
    stock, fotos_s40 = [], {}
    lunes = [DESDE + timedelta(days=i) for i in range(365) if (DESDE + timedelta(days=i)).weekday() == 0]
    for semana in lunes:
        origenes = {s: origen(s, ap, semana)[0] for s, (_, ap) in sucursales.items() if s != NUEVA["sucursal_id"]}
        fotos = {}
        for fecha, sucursal, sku, unidades in con.execute(
                "SELECT semana, sucursal_id, sku, stock_unidades FROM stock_semanal WHERE semana IN (SELECT UNNEST(?::DATE[]))",
                [sorted(set(origenes.values()))]).fetchall():
            fotos.setdefault((fecha, sucursal), []).append((sku, unidades))
        for sucursal in sorted(sucursales):
            if not abierta(sucursal, semana):
                continue
            if sucursal == NUEVA["sucursal_id"]:
                stock += [(semana, sucursal, sku, u) for sku, u in fotos_s40.get(semana, [])]
                continue
            de_esta = []
            for sku, unidades in fotos.get((origenes[sucursal], sucursal), []):
                if sku == disc and semana >= disc_desde:
                    continue
                cantidad = redondeo_estocastico(unidades * ruido(rng), rng)
                if sucursal == q_suc and productos[sku][1] == q_sub and q_desde <= semana <= q_hasta:
                    cantidad = 0
                de_esta.append((sku, cantidad))
                if semana >= MASCOTAS["lanzamiento"]:
                    # Si el análogo tiene stock, el nuevo también: escalar y redondear un stock chico daba 0 y
                    # quiebres falsos (revisión del 19-11: 2,11 % contra 1,48 % del resto)
                    de_esta += [(nuevo, max(redondeo_estocastico(cantidad * MASCOTAS["escala"], rng), 1 if cantidad else 0))
                                for nuevo, (analogo, _) in mascotas.items() if analogo == sku]
            if sucursal == NUEVA["analoga"]:
                fotos_s40[semana] = de_esta
            stock += [(semana, sucursal, sku, u) for sku, u in de_esta]
    cargar(con, "stock_semanal", stock, CARPETA)

    # Presupuesto: el de dos años antes por el crecimiento (S39 y S40: un año antes, o abril de 2026 por la
    # estacionalidad del AF2025); S41, el de S40 por su curva; Mascotas, desde septiembre, sus ventas del mes ± 5 %
    base_presu = {(m, s, c): i for m, s, c, i in con.execute(
        "SELECT mes, sucursal_id, categoria, importe_presupuesto FROM presupuesto WHERE mes < '2026-05-01'").fetchall()}
    total_mes = {}
    for (m, _, _), i in base_presu.items():
        total_mes[m] = total_mes.get(m, 0) + i
    ventas_mascotas = {(m, s): v for m, s, v in con.execute(
        f"""SELECT DATE_TRUNC('month', fecha)::DATE, sucursal_id, SUM(importe_neto) FROM ventas JOIN productos USING (sku)
            WHERE categoria = '{MASCOTAS['categoria']}' GROUP BY 1, 2""").fetchall()}
    presupuesto = []
    categorias = sorted({c for (_, _, c) in base_presu})
    mes = DESDE
    while mes <= HASTA:
        del_mes = {}
        for sucursal in sorted(sucursales):
            if sucursal == NUEVA["sucursal_id"] or not abierta(sucursal, mes):
                continue
            for categoria in categorias:
                hace_dos, hace_uno = primero_de_mes(mes, -24), primero_de_mes(mes, -12)
                if (hace_dos, sucursal, categoria) in base_presu:
                    importe = base_presu[(hace_dos, sucursal, categoria)] * g ** 2
                elif (hace_uno, sucursal, categoria) in base_presu:
                    importe = base_presu[(hace_uno, sucursal, categoria)] * g
                else:
                    importe = base_presu[(date(2026, 4, 1), sucursal, categoria)] * total_mes[hace_dos] / total_mes[date(2025, 4, 1)]
                del_mes[(sucursal, categoria)] = round(importe, 2)
        for (sucursal, categoria), importe in list(del_mes.items()):
            if sucursal == NUEVA["analoga"] and NUEVA["fecha_apertura"] <= mes + timedelta(days=31):
                del_mes[(NUEVA["sucursal_id"], categoria)] = round(importe * rampa(mes), 2)
        if mes >= date(2026, 9, 1):
            for sucursal in sorted(sucursales):
                if (mes, sucursal) in ventas_mascotas:
                    del_mes[(sucursal, MASCOTAS["categoria"])] = round(ventas_mascotas[(mes, sucursal)] * ruido(rng, 0.05), 2)
        presupuesto += [(mes, s, c, i) for (s, c), i in sorted(del_mes.items())]
        mes = primero_de_mes(mes, 1)
    cargar(con, "presupuesto", presupuesto, CARPETA)
    cargar(con, "promociones", nuevas, CARPETA)
    con.close()
    return factores, ev, {"ventas": sum(ventas_por_mes.values()), "stock_semanal": len(stock),
                          "presupuesto": len(presupuesto), "promociones": len(nuevas)}


def verificar_base_nueva():
    from verificar_base import verificar
    resultados, notas, raras = verificar(str(LIMPIA))
    return {"errores": [(n, m) for n, m in resultados if m], "controles": len(resultados), "notas": notas,
            "avisos": [(n, c, ej) for n, c, ej in raras]}


def informe(factores, ev, filas, v, segundos):
    si = lambda x: "✓" if x else "✗"
    coma = lambda x: str(x).replace(".", ",")
    e = ev
    lineas = [
        "# Año simulado: AF2027 con eventos nuevos (decisión 88)", "",
        f"Comando: `.venv/bin/python evaluacion/pruebas/anio_simulado.py` · semilla {SEMILLA} · {segundos:.0f} s", "",
        "## Cómo se armaron los datos", "",
        f"- Cada día copia el mismo día de la semana del AF2025 (728 días antes), por el crecimiento anual medido "
        f"(**×{coma(factores['crecimiento_anual'])}** por año, comparables AF2026 contra AF2025), con ruido lognormal "
        f"de media 1 y σ = {coma(RUIDO)}.",
        f"- S41 copia a S40 con su curva de apertura medida (mes 1: {coma(factores['curva_apertura'][0])} de su nivel actual).",
        f"- Filas nuevas: {filas['ventas']:,} ventas, {filas['stock_semanal']:,} fotos de stock, {filas['presupuesto']:,} "
        f"presupuestos, {filas['promociones']} promociones.".replace(",", "."),
        "", "## Eventos (sorteados con la semilla)", "", "| Evento | Dónde y cuándo | ¿Pasó antes en la base? |", "|---|---|---|",
        f"| Cierre de una sucursal | {e['cierre']['sucursal']}, desde el {e['cierre']['fecha']} | no: ninguna cerró |",
        f"| Aumento de precios +15 % (unidades −5 %) | {e['precios']['categoria']}, desde el {e['precios']['desde']} | "
        f"no: cada producto tiene un solo precio |",
        f"| Categoría nueva | Mascotas (6 productos, proveedor nuevo), desde el {e['categoria_nueva']['lanzamiento']} | no |",
        f"| Producto discontinuado | {e['discontinuado']['sku']}, desde el {e['discontinuado']['desde']} | no |",
        f"| Región sin ventas (un corte) | {e['corte']['region']}, {', '.join(e['corte']['dias'])} | no |",
        f"| Mix hacia la marca propia (+40 % y −8 % de unidades al final) | toda la cadena, desde nov-2026, gradual | no |",
        f"| Quiebre de stock | {e['quiebre']['subcategoria']} en {e['quiebre']['sucursal']}, "
        f"{e['quiebre']['desde']} a {e['quiebre']['hasta']} | sí (conocido) |",
        f"| Caída de demanda −30 % | {e['caida']['categoria']} en el {e['caida']['region']}, T3 (nov a ene) | sí (conocido) |",
        "", "## Verificación de la base (`verificar_base.py`)", "",
        f"- {si(not v['errores'])} {v['controles'] - len(v['errores'])} de {v['controles']} controles bien · "
        f"{len(v['avisos'])} avisos",
    ]
    lineas += [f"  - **error**: {n} ({m} filas)" for n, m in v["errores"]]
    lineas += [f"  - aviso: {n} ({c}): {'; '.join(ej)}" for n, c, ej in v["avisos"]]
    lineas += [f"  - {nota}" for nota in v["notas"]]
    return "\n".join(lineas) + "\n"


def main():
    inicio = time.monotonic()
    factores, ev, filas = armar()
    v = verificar_base_nueva()
    (CARPETA / "eventos.json").write_text(json.dumps({"semilla": SEMILLA, "factores": factores, "eventos": ev},
                                                     ensure_ascii=False, indent=2, default=str))
    texto = informe(factores, ev, filas, v, time.monotonic() - inicio)
    (CARPETA / "resultado.md").write_text(texto)
    print(texto)


if __name__ == "__main__":
    main()
