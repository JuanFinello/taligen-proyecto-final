"""Test 1: una ingesta simulada de mayo de 2026 (el primer mes del AF2027), sobre copias de la base (decisión 87).
La base original no se toca: se arma salidas/ingesta/limpia.duckdb (datos nuevos con hechos reales plantados) y
salidas/ingesta/sucia.duckdb (la misma, más errores de carga).

Cómo se arman los datos (bibliografía en el README, decisión 87):
- Ingenuo estacional con bloques que respetan la semana: cada día copia el mismo día de la semana de 364 días antes,
  por el crecimiento medido en la base (sucursales comparables, feb–abr 2026 contra feb–abr 2025). Las sucursales que
  no estaban abiertas un año antes (S39 y S40) copian 35 días antes, sin crecimiento: su nivel reciente.
- Ruido chico (lognormal, σ = 0,15) con semilla fija y redondeo estocástico de las unidades (con 1 o 2 unidades por
  fila, redondear siempre borraría el crecimiento). Los importes se recalculan: bruto = unidades × precio de lista,
  descuento = el % de su promoción, neto = bruto − descuento, costo = costo unitario de origen × unidades.
- Sucursal nueva S41 (Oeste, express, abre el lunes 04-05-2026): análoga de S40, la misma región y formato, por la
  rampa de apertura medida en S40 (su primer mes completo contra su nivel de feb–abr 2026).
- Producto nuevo P0309 (lanzamiento el 11-05-2026): análogo de un producto de la misma subcategoría.
- Hechos reales, en lugares sorteados con la semilla y anotados: un quiebre de stock (una subcategoría en una
  sucursal), una promoción fuerte de una semana y una caída de demanda de una categoría en una región.
- Errores de carga, solo en la sucia: un presupuesto ×10 (lo tiene que marcar como sospechoso) y un día de una
  sucursal cargado dos veces (lo tiene que bloquear).

Uso: .venv/bin/python evaluacion/robustez/ingesta_simulada.py            (arma las dos bases, las verifica y calcula lo esperado)
     .venv/bin/python evaluacion/robustez/ingesta_simulada.py --agente   (además le pregunta al agente y corre el informe programado
                                                              de ese lunes sobre la limpia: ~US$ 0,10)
Deja en salidas/ingesta/: las dos bases, eventos.json (qué se plantó, dónde, y los valores esperados) y resultado.md,
que se copia a trazas/ingesta_simulada.md."""
import json
import os
import random
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(RAIZ / "analista"), str(RAIZ / "evaluacion")]  # los módulos del proyecto
CARPETA = Path("salidas/ingesta")
LIMPIA, SUCIA = CARPETA / "limpia.duckdb", CARPETA / "sucia.duckdb"
# El agente, el servidor MCP y el informe programado leen esta base: tiene que quedar fijada antes de importarlos
os.environ["BASE_ALMACENES"] = str(LIMPIA)

import duckdb  # noqa: E402

from comun import RUIDO, cargar, redondeo_estocastico, ruido  # noqa: E402

ORIGINAL = "Data/base/almacenes_del_sur.duckdb"
SEMILLA = 2026
DIAS = [date(2026, 5, 1) + timedelta(days=i) for i in range(31)]
LUNES = [d for d in DIAS if d.weekday() == 0]
UN_ANIO, RECIENTE = 364, 35  # múltiplos de 7: el mismo día de la semana
NUEVA = {"sucursal_id": "S41", "nombre": "Almacenes del Sur Las Lomas", "region": "Oeste", "formato": "express",
         "superficie_m2": 410, "fecha_apertura": date(2026, 5, 4), "analoga": "S40"}
PRODUCTO = {"sku": "P0309", "lanzamiento": date(2026, 5, 11), "escala": 0.4, "precio": 0.9}
QUIEBRE = {"desde": date(2026, 5, 11), "queda": 0.15}  # stock en 0 desde esa foto; se vende el 15 % (reposición parcial)
PROMO = {"pct": 30.0, "desde": date(2026, 5, 18), "hasta": date(2026, 5, 24), "multiplica": 3.0}
CAIDA = 0.7  # la demanda de una categoría en una región cae 30 % todo el mes


def medir(con):
    """Los factores salen de la base, no se inventan."""
    q = lambda sql, *p: con.execute(sql, list(p)).fetchone()[0]
    crecimiento = q("""SELECT SUM(CASE WHEN fecha >= '2026-02-01' THEN importe_neto END)
                            / SUM(CASE WHEN fecha < '2025-05-01' THEN importe_neto END)
                       FROM ventas v JOIN sucursales s USING (sucursal_id)
                       WHERE s.fecha_apertura < '2024-05-01'
                         AND (fecha BETWEEN '2025-02-01' AND '2025-04-30' OR fecha BETWEEN '2026-02-01' AND '2026-04-30')""")
    primer_mes = q("SELECT SUM(importe_neto) FROM ventas WHERE sucursal_id = ? AND fecha BETWEEN '2025-07-01' AND '2025-07-31'",
                   NUEVA["analoga"])
    nivel = q("SELECT SUM(importe_neto) / 3 FROM ventas WHERE sucursal_id = ? AND fecha BETWEEN '2026-02-01' AND '2026-04-30'",
              NUEVA["analoga"])
    return {"crecimiento": round(crecimiento, 4), "rampa_apertura": round(primer_mes / nivel, 4)}


def sortear(con, rng):
    """Dónde caen los hechos reales y los errores. Solo sucursales comparables (abiertas antes de la base)."""
    q = lambda sql: [r[0] for r in con.execute(sql).fetchall()]
    viejas = q("SELECT sucursal_id FROM sucursales WHERE fecha_apertura < '2024-05-01' ORDER BY 1")
    subcategorias = q("SELECT DISTINCT subcategoria FROM productos ORDER BY 1")
    quiebre = {"sucursal": rng.choice(viejas), "subcategoria": rng.choice(subcategorias)}
    quiebre["categoria"] = con.execute("SELECT ANY_VALUE(categoria) FROM productos WHERE subcategoria = ?",
                                       [quiebre["subcategoria"]]).fetchone()[0]
    candidatos = q(f"SELECT sku FROM productos WHERE subcategoria <> '{quiebre['subcategoria']}' ORDER BY 1")
    promo = {"sku": rng.choice(candidatos)}
    caida = {"categoria": rng.choice([c for c in q("SELECT DISTINCT categoria FROM productos ORDER BY 1")
                                      if c != quiebre["categoria"]]),
             "region": rng.choice(q("SELECT DISTINCT region FROM sucursales ORDER BY 1"))}
    analogo = rng.choice(q(f"SELECT sku FROM productos WHERE sku NOT IN ('{promo['sku']}') AND subcategoria <> "
                           f"'{quiebre['subcategoria']}' ORDER BY 1"))
    presupuesto = {"sucursal": rng.choice(viejas), "categoria": rng.choice(q("SELECT DISTINCT categoria FROM productos ORDER BY 1")),
                   "multiplica": 10}
    duplicado = {"sucursal": rng.choice(viejas), "fecha": str(rng.choice(DIAS))}
    return {"quiebre": quiebre, "promocion": promo, "caida": caida, "analogo": analogo}, \
           {"presupuesto_x10": presupuesto, "dia_duplicado": duplicado}


def origen(sucursal, apertura, dia):
    """(sucursal y día de donde se copia, si aplica el crecimiento) para un día nuevo de una sucursal."""
    if sucursal == NUEVA["sucursal_id"]:
        return NUEVA["analoga"], dia - timedelta(days=RECIENTE), False
    if apertura <= dia - timedelta(days=UN_ANIO):
        return sucursal, dia - timedelta(days=UN_ANIO), True
    return sucursal, dia - timedelta(days=RECIENTE), False


def armar_limpia():
    CARPETA.mkdir(parents=True, exist_ok=True)
    if LIMPIA.exists():
        LIMPIA.unlink()
    shutil.copy(ORIGINAL, LIMPIA)
    rng = random.Random(SEMILLA)
    con = duckdb.connect(str(LIMPIA))
    factores = medir(con)
    hechos, errores = sortear(con, rng)
    q, e = hechos["quiebre"], hechos["promocion"]

    # 1. Calendario: mayo de 2026, con las columnas fiscales de la regla del glosario
    con.execute("""INSERT INTO fechas SELECT d::DATE, YEAR(d), MONTH(d), DAY(d), 'mayo', ISODOW(d),
                       YEAR(d) + (MONTH(d) >= 5)::INT, (MONTH(d) + 7) % 12 + 1, ((MONTH(d) + 7) % 12) // 3 + 1,
                       DATE_TRUNC('week', d)::DATE
                   FROM generate_series(DATE '2026-05-01', DATE '2026-05-31', INTERVAL 1 DAY) t(d)""")
    # 2. Dimensiones: la sucursal y el producto nuevos
    con.execute("INSERT INTO sucursales VALUES (?, ?, ?, ?, ?, ?)",
                [NUEVA[k] for k in ("sucursal_id", "nombre", "region", "formato", "superficie_m2", "fecha_apertura")])
    a = con.execute("SELECT * FROM productos WHERE sku = ?", [hechos["analogo"]]).fetchone()
    precio_nuevo = round(a[6] * PRODUCTO["precio"], -1)
    nombre_nuevo = f"{a[1].split(' ')[0]} Nueva Cosecha {a[1].split(' ')[-1]}"
    con.execute("INSERT INTO productos VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [PRODUCTO["sku"], nombre_nuevo, a[2], a[3], a[4], a[5], precio_nuevo, a[7]])
    hechos["producto_nuevo"] = {"sku": PRODUCTO["sku"], "descripcion": nombre_nuevo, "analogo": a[0],
                                "precio_lista": precio_nuevo, "lanzamiento": str(PRODUCTO["lanzamiento"])}

    productos = {s: (cat, sub, precio) for s, cat, sub, precio in
                 con.execute("SELECT sku, categoria, subcategoria, precio_lista FROM productos").fetchall()}
    sucursales = {s: (reg, ap) for s, reg, ap in con.execute("SELECT sucursal_id, region, fecha_apertura FROM sucursales").fetchall()}

    # 3. Promociones: las de origen, corridas al período nuevo con otro id; más la promoción plantada
    promos = {p[0]: p for p in con.execute("SELECT * FROM promociones").fetchall()}
    siguiente = [int(con.execute("SELECT MAX(CAST(SUBSTR(promocion_id, 6) AS INT)) FROM promociones").fetchone()[0])]
    nuevas, corridas = [], {}

    def promo_corrida(promo_id, corrimiento):
        if (promo_id, corrimiento) not in corridas:
            p = promos[promo_id]
            siguiente[0] += 1
            nuevo, desde, hasta = f"PROMO{siguiente[0]:03d}", p[4] + timedelta(days=corrimiento), p[5] + timedelta(days=corrimiento)
            nuevas.append((nuevo, f"{p[1].rsplit(' ', 1)[0]} {desde.month:02d}/{desde.year}", p[2], p[3], desde, hasta))
            corridas[(promo_id, corrimiento)] = (nuevo, p[3])
        return corridas[(promo_id, corrimiento)]

    siguiente[0] += 1
    promo_plantada = f"PROMO{siguiente[0]:03d}"
    nuevas.append((promo_plantada, f"Promo Semana Fuerte {PROMO['desde'].month:02d}/{PROMO['desde'].year}", e["sku"],
                   PROMO["pct"], PROMO["desde"], PROMO["hasta"]))
    e.update({"promocion_id": promo_plantada, "descuento_pct": PROMO["pct"], "desde": str(PROMO["desde"]),
              "hasta": str(PROMO["hasta"]), "unidades_por": PROMO["multiplica"]})

    # 4. Ventas: cada día nuevo copia su día de origen, con crecimiento, ruido y los hechos plantados
    filas_origen = {}
    for fila in con.execute("""SELECT fecha, sucursal_id, sku, tipo_movimiento, unidades, costo, promocion_id FROM ventas
                               WHERE fecha BETWEEN DATE '2025-05-01' AND DATE '2025-06-01'
                                  OR fecha BETWEEN DATE '2026-03-27' AND DATE '2026-04-30'
                               ORDER BY fecha, sucursal_id, sku, tipo_movimiento""").fetchall():
        filas_origen.setdefault((fila[0], fila[1]), []).append(fila)
    ventas = []
    for dia in DIAS:
        for sucursal, (region, apertura) in sorted(sucursales.items()):
            if apertura > dia:
                continue
            desde_suc, desde_dia, crece = origen(sucursal, apertura, dia)
            for _, _, sku, tipo, unidades, costo, promo_id in filas_origen.get((desde_dia, desde_suc), []):
                categoria, subcategoria, precio = productos[sku]
                factor = (factores["crecimiento"] if crece else 1.0) * ruido(rng)
                if sucursal == NUEVA["sucursal_id"]:
                    factor *= factores["rampa_apertura"]
                if sucursal == q["sucursal"] and subcategoria == q["subcategoria"] and dia > QUIEBRE["desde"]:
                    factor *= QUIEBRE["queda"]
                if categoria == hechos["caida"]["categoria"] and region == hechos["caida"]["region"]:
                    factor *= CAIDA
                pct, nuevo_promo = 0.0, None
                if promo_id:
                    nuevo_promo, pct = promo_corrida(promo_id, (dia - desde_dia).days)
                if sku == e["sku"] and PROMO["desde"] <= dia <= PROMO["hasta"]:
                    nuevo_promo, pct = promo_plantada, PROMO["pct"]
                    if tipo == "venta":
                        factor *= PROMO["multiplica"]
                cantidad = redondeo_estocastico(abs(unidades) * factor, rng)
                if cantidad == 0:
                    continue
                cantidad = cantidad if tipo == "venta" else -cantidad
                # Una devolución no lleva promoción en la base original: se respeta
                if tipo == "devolucion":
                    nuevo_promo, pct = None, 0.0
                bruto = round(cantidad * precio, 2)
                descuento = round(bruto * pct / 100, 2)
                ventas.append((dia, sucursal, sku, tipo, cantidad, bruto, descuento, round(bruto - descuento, 2),
                               round(costo / unidades * cantidad, 2), nuevo_promo))
    # El producto nuevo: las ventas de su análogo desde el lanzamiento, a escala y con su precio
    for dia, sucursal, sku, tipo, cantidad, bruto, descuento, neto, costo, promo_id in list(ventas):
        if sku == hechos["analogo"] and dia >= PRODUCTO["lanzamiento"] and tipo == "venta":
            n = redondeo_estocastico(cantidad * PRODUCTO["escala"], rng)
            if n:
                b = round(n * precio_nuevo, 2)
                ventas.append((dia, sucursal, PRODUCTO["sku"], "venta", n, b, 0.0, b, round(costo / cantidad * n, 2), None))

    # 5. Stock: la foto de cada lunes, copiada del lunes de origen; el quiebre deja en 0 su subcategoría
    stock = []
    fotos = {}
    for semana, sucursal, sku, unidades in con.execute(
            """SELECT semana, sucursal_id, sku, stock_unidades FROM stock_semanal
               WHERE semana BETWEEN DATE '2025-05-01' AND DATE '2025-06-01'
                  OR semana BETWEEN DATE '2026-03-27' AND DATE '2026-04-30'""").fetchall():
        fotos.setdefault((semana, sucursal), []).append((sku, unidades))
    for lunes in LUNES:
        for sucursal, (_, apertura) in sorted(sucursales.items()):
            if apertura > lunes:
                continue
            desde_suc, desde_lunes, _ = origen(sucursal, apertura, lunes)
            for sku, unidades in fotos.get((desde_lunes, desde_suc), []):
                cantidad = redondeo_estocastico(unidades * ruido(rng), rng)
                if sucursal == q["sucursal"] and productos[sku][1] == q["subcategoria"] and lunes >= QUIEBRE["desde"]:
                    cantidad = 0
                stock.append((lunes, sucursal, sku, cantidad))
                if sku == hechos["analogo"] and lunes >= PRODUCTO["lanzamiento"]:  # antes del lanzamiento no tiene foto
                    stock.append((lunes, sucursal, PRODUCTO["sku"], redondeo_estocastico(cantidad * PRODUCTO["escala"], rng)))

    # 6. Presupuesto de mayo: el de mayo de 2025 por el crecimiento; S39 y S40, su abril de 2026 por la
    #    estacionalidad abril → mayo de 2025; S41, el de S40 por la rampa
    estacional = con.execute("""SELECT SUM(CASE WHEN mes = '2025-05-01' THEN importe_presupuesto END)
                                     / SUM(CASE WHEN mes = '2025-04-01' THEN importe_presupuesto END) FROM presupuesto""").fetchone()[0]
    presupuesto = {}
    for mes, sucursal, categoria, importe in con.execute(
            "SELECT mes, sucursal_id, categoria, importe_presupuesto FROM presupuesto WHERE mes IN ('2025-05-01', '2026-04-01')").fetchall():
        if mes == date(2025, 5, 1):
            presupuesto[(sucursal, categoria)] = round(importe * factores["crecimiento"], 2)
        elif (sucursal, categoria) not in presupuesto:
            presupuesto[(sucursal, categoria)] = round(importe * estacional, 2)
    for (sucursal, categoria), importe in list(presupuesto.items()):
        if sucursal == NUEVA["analoga"]:
            presupuesto[(NUEVA["sucursal_id"], categoria)] = round(importe * factores["rampa_apertura"], 2)

    CARPETA.mkdir(parents=True, exist_ok=True)
    for tabla, filas in (("promociones", nuevas), ("ventas", ventas), ("stock_semanal", stock),
                         ("presupuesto", [(date(2026, 5, 1), s, c, i) for (s, c), i in sorted(presupuesto.items())])):
        cargar(con, tabla, filas, CARPETA)
    con.close()
    return factores, hechos, errores, {"ventas": len(ventas), "stock_semanal": len(stock),
                                       "presupuesto": len(presupuesto), "promociones": len(nuevas)}


def armar_sucia(errores):
    """La limpia más los errores de carga."""
    shutil.copy(LIMPIA, SUCIA)
    with duckdb.connect(str(SUCIA)) as con:
        p, d = errores["presupuesto_x10"], errores["dia_duplicado"]
        con.execute("UPDATE presupuesto SET importe_presupuesto = importe_presupuesto * ? "
                    "WHERE mes = '2026-05-01' AND sucursal_id = ? AND categoria = ?", [p["multiplica"], p["sucursal"], p["categoria"]])
        d["filas"] = con.execute("SELECT COUNT(*) FROM ventas WHERE fecha = ? AND sucursal_id = ?", [d["fecha"], d["sucursal"]]).fetchone()[0]
        con.execute("INSERT INTO ventas SELECT * FROM ventas WHERE fecha = ? AND sucursal_id = ?", [d["fecha"], d["sucursal"]])


def esperados(hechos):
    """Los valores que tiene que dar el agente, con SQL escrito acá, sin el procesador (decisión 87: antes de correrlo)."""
    with duckdb.connect(str(LIMPIA), read_only=True) as con:
        q = lambda sql, *p: con.execute(sql, list(p)).fetchone()[0]
        mayo = "fecha BETWEEN '2026-05-01' AND '2026-05-31'"
        antes = "fecha BETWEEN '2025-05-01' AND '2025-05-31'"
        # Comparables (decisión 12): abiertas el primer día del período anterior
        comparables = "sucursal_id IN (SELECT sucursal_id FROM sucursales WHERE fecha_apertura <= '2025-05-01')"
        variacion = lambda a, b: round((a - b) / b * 100, 4)
        total = q(f"SELECT SUM(importe_neto) FROM ventas WHERE {mayo}")
        comp_a = q(f"SELECT SUM(importe_neto) FROM ventas WHERE {mayo} AND {comparables}")
        comp_b = q(f"SELECT SUM(importe_neto) FROM ventas WHERE {antes} AND {comparables}")
        todas_b = q(f"SELECT SUM(importe_neto) FROM ventas WHERE {antes}")
        qb = hechos["quiebre"]
        sub = lambda periodo: q(f"""SELECT SUM(importe_neto) FROM ventas v JOIN productos p USING (sku)
                                    WHERE {periodo} AND sucursal_id = ? AND subcategoria = ?""", qb["sucursal"], qb["subcategoria"])
        quiebre_pct = lambda desde, hasta: q("""SELECT AVG(CASE WHEN stock_unidades = 0 THEN 100.0 ELSE 0 END)
                                               FROM stock_semanal st JOIN productos p USING (sku)
                                               WHERE semana BETWEEN ? AND ? AND sucursal_id = ? AND subcategoria = ?""",
                                             desde, hasta, qb["sucursal"], qb["subcategoria"])
        c = hechos["caida"]
        cat = lambda periodo: q(f"""SELECT SUM(importe_neto) FROM ventas v JOIN productos p USING (sku)
                                    JOIN sucursales s USING (sucursal_id)
                                    WHERE {periodo} AND v.{comparables} AND categoria = ? AND region = ?""", c["categoria"], c["region"])
        return {
            "ventas_mayo_2026": round(total, 2),
            "ventas_S41_mayo_2026": round(q(f"SELECT SUM(importe_neto) FROM ventas WHERE {mayo} AND sucursal_id = 'S41'"), 2),
            "variacion_comparables_pct": variacion(comp_a, comp_b),
            "variacion_todas_pct": variacion(total, todas_b),
            "ventas_producto_nuevo": round(q(f"SELECT SUM(importe_neto) FROM ventas WHERE {mayo} AND sku = ?", PRODUCTO["sku"]), 2),
            "quiebre": {"variacion_ventas_pct": variacion(sub(mayo), sub(antes)),
                        "tasa_quiebre_mayo_2026_pct": round(quiebre_pct(date(2026, 5, 1), date(2026, 5, 31)), 2),
                        "tasa_quiebre_mayo_2025_pct": round(quiebre_pct(date(2025, 5, 1), date(2025, 5, 31)), 2)},
            "caida": {"variacion_comparables_pct": variacion(cat(mayo), cat(antes))},
        }


def verificar_las_dos(errores):
    """La limpia tiene que pasar todos los controles; la sucia, fallar por el día duplicado y marcar el presupuesto."""
    from procesador_capa_semantica import celdas_de_presupuesto_sospechosas
    from verificar_base import verificar
    salida = {}
    for nombre, ruta in (("limpia", LIMPIA), ("sucia", SUCIA)):
        resultados, notas, raras = verificar(str(ruta))
        salida[nombre] = {"errores": [(n, m) for n, m in resultados if m], "controles": len(resultados),
                          "avisos": [(n, c, ej) for n, c, ej in raras], "notas": notas}
    p = errores["presupuesto_x10"]
    salida["sucia_bloquea_duplicado"] = any("una fila por fecha, sucursal, producto y tipo" in n for n, _ in salida["sucia"]["errores"])
    with duckdb.connect(str(SUCIA), read_only=True) as con:  # el aviso muestra 3 ejemplos: se mira la lista entera
        salida["sucia_marca_presupuesto"] = any((a, m, s, c) == (2026, 5, p["sucursal"], p["categoria"])
                                                for a, m, s, c, *_ in celdas_de_presupuesto_sospechosas(con))
    salida["limpia_sin_errores"] = not salida["limpia"]["errores"]
    return salida


def preguntas(hechos, valores):
    """(id, pregunta, chequeos para evaluador.fallos, o None si se lee). Chequeos con la forma de esperados.yaml."""
    with duckdb.connect(str(LIMPIA), read_only=True) as con:
        nombre = lambda s: con.execute("SELECT nombre FROM sucursales WHERE sucursal_id = ?", [s]).fetchone()[0]
        q, c = hechos["quiebre"], hechos["caida"]
        return [
            ("ultimo_mes", "¿Cuánto vendimos el último mes?",
             [{"medida": "ventas_netas", "tipo": "valor", "esperado": valores["ventas_mayo_2026"], "tolerancia": 1}]),
            ("sucursal_nueva", "¿Cuánto vendió la sucursal S41 en mayo de 2026?",
             [{"medida": "ventas_netas", "tipo": "valor", "esperado": valores["ventas_S41_mayo_2026"], "tolerancia": 1}]),
            ("comparables", "¿Cómo vinieron las ventas de mayo de 2026 contra mayo de 2025 en sucursales comparables?",
             [{"medida": "ventas_netas", "tipo": "variacion", "esperado": valores["variacion_comparables_pct"],
               "tolerancia": 0.01, "comparables": True}]),
            ("producto_nuevo", f"¿Cuánto vendió el producto {hechos['producto_nuevo']['descripcion']} en mayo de 2026?",
             [{"medida": "ventas_netas", "tipo": "valor", "esperado": valores["ventas_producto_nuevo"], "tolerancia": 1}]),
            ("quiebre", f"¿Por qué cayeron las ventas de {q['subcategoria']} en la sucursal {nombre(q['sucursal'])} "
                        f"en mayo de 2026?", None),
            ("caida", f"¿Por qué cayeron las ventas de {c['categoria']} en la región {c['region']} en mayo de 2026?", None),
        ]


async def preguntar(lista):
    from evaluador import falla, fallos
    from puerta import atender
    salida = []
    for id_, texto, chequeos in lista:
        respuestas = await atender([texto], carpeta=str(CARPETA / id_))
        r = respuestas[-1]
        malos = falla(fallos(chequeos, r["consultas"], r)) if chequeos else None
        salida.append({"id": id_, "pregunta": texto, "tipo": r.get("tipo"), "ruta": r.get("ruta"), "texto": r["texto"],
                       "chequeo": None if chequeos is None else (not malos), "fallas": malos or []})
    return salida


def programado():
    """El informe programado del lunes 01-06-2026 sobre la limpia: el semanal (25 al 31-05) y el mensual de mayo."""
    import informe_programado
    informe_programado.CARPETA = CARPETA / "programado"
    shutil.rmtree(informe_programado.CARPETA, ignore_errors=True)
    sys.argv = ["informe_programado.py", "--hoy", "2026-06-01"]
    try:
        informe_programado.main()
    except SystemExit as fin:
        return fin.code in (0, None)
    return True


def coma(x):
    return str(x).replace(".", ",")


def informe(factores, hechos, errores, filas, valores, verificacion, agente=None, programado_bien=None):
    v = verificacion
    si = lambda x: "✓" if x else "✗"
    lineas = [
        "# Test 1: ingesta simulada (decisión 87)", "",
        f"Comando: `.venv/bin/python evaluacion/robustez/ingesta_simulada.py{' --agente' if agente is not None else ''}` · semilla {SEMILLA}",
        "", "## Cómo se armaron los datos", "",
        f"- Mayo de 2026 (AF2027, mes fiscal 1): cada día copia el mismo día de la semana de 364 días antes, por el "
        f"crecimiento medido en la base (**×{coma(factores['crecimiento'])}**, comparables feb–abr 2026 contra 2025), con ruido "
        f"lognormal de media 1 y σ = {coma(RUIDO)}. S39 y S40, que no estaban abiertas un año antes, copian 35 días antes.",
        f"- S41 ({NUEVA['nombre']}, {NUEVA['region']}, {NUEVA['formato']}, abre el {NUEVA['fecha_apertura']:%d-%m-%Y}): "
        f"análoga de {NUEVA['analoga']} por su rampa de apertura medida (**×{coma(factores['rampa_apertura'])}**).",
        f"- Producto nuevo {hechos['producto_nuevo']['sku']} ({hechos['producto_nuevo']['descripcion']}), desde el "
        f"{PRODUCTO['lanzamiento']:%d-%m-%Y}: {PRODUCTO['escala'] * 100:.0f} % de las unidades de su análogo "
        f"{hechos['producto_nuevo']['analogo']}.",
        f"- Filas nuevas: {filas['ventas']:,} ventas, {filas['stock_semanal']:,} fotos de stock, {filas['presupuesto']} "
        f"presupuestos, {filas['promociones']} promociones.".replace(",", "."),
        "", "## Lo que se plantó (sorteado con la semilla)", "",
        "| Qué | Dónde | Es |", "|---|---|---|",
        f"| Quiebre de stock | {hechos['quiebre']['subcategoria']} en {hechos['quiebre']['sucursal']}, desde el "
        f"{QUIEBRE['desde']:%d-%m} | hecho real |",
        f"| Promoción fuerte ({PROMO['pct']:.0f} %, unidades ×{PROMO['multiplica']:.0f}) | {hechos['promocion']['sku']}, "
        f"{PROMO['desde']:%d-%m} al {PROMO['hasta']:%d-%m} | hecho real |",
        f"| Caída de demanda (−{(1 - CAIDA) * 100:.0f} %) | {hechos['caida']['categoria']} en el {hechos['caida']['region']} | hecho real |",
        f"| Presupuesto ×{errores['presupuesto_x10']['multiplica']} | {errores['presupuesto_x10']['categoria']} en "
        f"{errores['presupuesto_x10']['sucursal']}, mayo | error de carga (solo en la sucia) |",
        f"| Día cargado dos veces | {errores['dia_duplicado']['sucursal']}, {errores['dia_duplicado']['fecha']} "
        f"({errores['dia_duplicado']['filas']} filas) | error de carga (solo en la sucia) |",
        "", "## Verificación de la base (`verificar_base.py`)", "",
        f"- {si(v['limpia_sin_errores'])} Limpia: {v['limpia']['controles'] - len(v['limpia']['errores'])} de "
        f"{v['limpia']['controles']} controles bien · {len(v['limpia']['avisos'])} avisos",
    ]
    lineas += [f"  - aviso: {n} ({c}): {'; '.join(ej)}" for n, c, ej in v["limpia"]["avisos"]]
    lineas += [f"- {si(v['sucia_bloquea_duplicado'])} Sucia: bloquea el día duplicado · "
               f"{si(v['sucia_marca_presupuesto'])} marca el presupuesto ×10 como sospechoso"]
    lineas += [f"  - error: {n} ({m} filas)" for n, m in v["sucia"]["errores"]]
    lineas += ["", "## Valores esperados (SQL a mano, antes de correr el agente)", "", "```json",
               json.dumps(valores, ensure_ascii=False, indent=2), "```"]
    if agente is not None:
        lineas += ["", "## El agente sobre la base limpia", "", "| Caso | Pregunta | Tipo → camino | Chequeo |", "|---|---|---|---|"]
        for r in agente:
            chequeo = "se lee" if r["chequeo"] is None else (si(r["chequeo"]) + (" " + "; ".join(r["fallas"]) if r["fallas"] else ""))
            lineas.append(f"| {r['id']} | {r['pregunta']} | {r['tipo']} → {r['ruta']} | {chequeo} |")
        lineas += ["", "### Respuestas", ""]
        for r in agente:
            lineas += [f"**{r['id']}.** {r['pregunta']}", "", "> " + r["texto"].replace("\n", "\n> "), ""]
        lineas += [f"## Informe programado del lunes 01-06-2026", "",
                   f"- {si(programado_bien)} semanal (25 al 31-05) y mensual de mayo: ver `salidas/ingesta/programado/`"]
    return "\n".join(lineas) + "\n"


def main():
    import asyncio
    con_agente = "--agente" in sys.argv
    factores, hechos, errores, filas = armar_limpia()
    armar_sucia(errores)
    valores = esperados(hechos)
    verificacion = verificar_las_dos(errores)
    (CARPETA / "eventos.json").write_text(json.dumps(
        {"semilla": SEMILLA, "factores": factores, "hechos": hechos, "errores": errores, "esperados": valores},
        ensure_ascii=False, indent=2, default=str))
    agente = programado_bien = None
    if con_agente:
        agente = asyncio.run(preguntar(preguntas(hechos, valores)))
        programado_bien = programado()
    texto = informe(factores, hechos, errores, filas, valores, verificacion, agente, programado_bien)
    (CARPETA / "resultado.md").write_text(texto)
    if con_agente:
        Path("trazas/ingesta_simulada.md").write_text(texto)
    print(texto)


if __name__ == "__main__":
    main()
