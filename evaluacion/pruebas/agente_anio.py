"""Fase 4 del año simulado (decisión 90): el agente sobre el AF2027 simulado (salidas/anio/limpia.duckdb, de
evaluacion/pruebas/anio_simulado.py). Las preguntas salen de los eventos plantados; los valores esperados se calculan con SQL
escrito acá, sin el procesador, y se guardan antes de correr el agente. Todo se califica por código:
- las preguntas con número, con los chequeos del evaluador (medida y valor, decisión 75);
- los diagnósticos, con reglas escritas abajo (un número dentro de un rango, o qué tiene que decir y qué no). El
  texto queda en la traza para leerlo.
Además, un segundo oráculo: lo que se plantó (una caída de −30 %) contra lo que mide el agente.

Uso: .venv/bin/python evaluacion/pruebas/agente_anio.py      (~US$ 0,08, unos 3 minutos)
Deja salidas/anio_agente/ (esperados.json antes de correr, resultado.md) y copia el resultado a trazas/agente_anio.md."""
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(RAIZ / "analista"), str(RAIZ / "evaluacion")]
ANIO = Path("salidas/anio/limpia.duckdb")
os.environ["BASE_ALMACENES"] = str(ANIO)  # antes de importar el agente y el procesador
CARPETA = Path("salidas/anio_agente")

import duckdb  # noqa: E402

AF27 = "fecha BETWEEN DATE '2026-05-01' AND DATE '2027-04-30'"
AF26 = "fecha BETWEEN DATE '2025-05-01' AND DATE '2026-04-30'"
T3_27 = "fecha BETWEEN DATE '2026-11-01' AND DATE '2027-01-31'"
T3_26 = "fecha BETWEEN DATE '2025-11-01' AND DATE '2026-01-31'"
T4_27 = "fecha BETWEEN DATE '2027-02-01' AND DATE '2027-04-30'"
T4_26 = "fecha BETWEEN DATE '2026-02-01' AND DATE '2026-04-30'"


def esperados(ev):
    """Los valores con SQL a mano. Comparables como el procesador (decisión 12): abiertas al inicio del período
    anterior. Y también como deberían ser si se supiera del cierre: sin S07."""
    with duckdb.connect(str(ANIO), read_only=True) as con:
        q = lambda sql, *p: con.execute(sql, list(p)).fetchone()[0]
        var = lambda a, b: round((a - b) / b * 100, 4)
        comparables = "sucursal_id IN (SELECT sucursal_id FROM sucursales WHERE fecha_apertura <= DATE '2025-05-01')"
        neto = lambda periodo, extra="TRUE": q(f"SELECT SUM(importe_neto) FROM ventas v JOIN productos p USING (sku) "
                                                f"JOIN sucursales s USING (sucursal_id) WHERE {periodo} AND {extra}")
        precio = lambda periodo: q(f"SELECT SUM(importe_neto) / SUM(unidades) FROM ventas v JOIN productos p USING (sku) "
                                   f"WHERE {periodo} AND p.categoria = '{ev['precios']['categoria']}'")
        c = ev["caida"]
        caida = f"p.categoria = '{c['categoria']}' AND s.region = '{c['region']}'"
        cierre = ev["cierre"]["sucursal"]
        return {
            "ventas_af2027": round(neto(AF27), 2),
            "comparables_af2027_como_el_sistema": var(neto(AF27, comparables), neto(AF26, comparables)),
            "comparables_af2027_sin_la_cerrada": var(neto(AF27, f"{comparables} AND sucursal_id <> '{cierre}'"),
                                                     neto(AF26, f"{comparables} AND sucursal_id <> '{cierre}'")),
            "todas_af2027": var(neto(AF27), neto(AF26)),
            "mascotas_af2027": round(neto(AF27, "p.categoria = 'Mascotas'"), 2),
            "precio_promedio_t3_variacion": var(precio(T3_27), precio(T3_26)),
            "marca_propia_t4_variacion": var(neto(T4_27, "p.es_marca_propia"), neto(T4_26, "p.es_marca_propia")),
            "caida_t3_todas": var(neto(T3_27, caida), neto(T3_26, caida)),
            "caida_t3_comparables": var(neto(T3_27, f"{caida} AND s.{comparables}"), neto(T3_26, f"{caida} AND s.{comparables}")),
            # El segundo oráculo: el T3 del AF2027 contra lo que habría sido sin el evento (el AF2025 × crecimiento²)
            "caida_plantada_medida": round((neto(T3_27, f"{caida} AND s.fecha_apertura < DATE '2024-05-01'")
                                            / (neto("fecha BETWEEN DATE '2024-11-01' AND DATE '2025-01-31'",
                                                    f"{caida} AND s.fecha_apertura < DATE '2024-05-01'") * 1.0205 ** 2) - 1) * 100, 2),
            "nombres": {s: n for s, n in con.execute("SELECT sucursal_id, nombre FROM sucursales").fetchall()},
            "descripcion_discontinuado": q("SELECT descripcion FROM productos WHERE sku = ?", ev["discontinuado"]["sku"]),
        }


def en_rango(desde, hasta, medida="ventas_netas"):
    """Regla: alguna consulta de esa medida trajo una variación dentro del rango."""
    def regla(r):
        vs = [c["resultado"].get("variacion") for c in r["consultas"] if c["argumentos"].get("medida") == medida]
        vs += [f.get("variacion") for c in r["consultas"] if c["argumentos"].get("medida") == medida
               for f in c["resultado"].get("filas", [])]
        ok = [v for v in vs if isinstance(v, (int, float)) and desde <= v <= hasta]
        return bool(ok), f"variación en [{desde}, {hasta}]: {'sí, ' + str(round(ok[0], 2)) if ok else 'no'}"
    return regla


def dice(si=(), no=(), etiqueta=""):
    """Regla de texto: tiene que decir alguno de `si` y ninguno de `no` (expresiones regulares, sin mayúsculas)."""
    def regla(r):
        t = r["texto"].lower()
        falta = si and not any(re.search(x, t) for x in si)
        sobra = [x for x in no if re.search(x, t)]
        return not falta and not sobra, etiqueta + (" · no dice lo esperado" if falta else "") + \
            (f" · dice lo que no debería ({sobra[0]})" if sobra else "")
    return regla


def preguntas(ev, e):
    n = e["nombres"]
    valor = lambda medida, esperado, tol=1: [{"medida": medida, "tipo": "valor", "esperado": esperado, "tolerancia": tol}]
    variacion = lambda medida, esperado, comparables=False: [{"medida": medida, "tipo": "variacion", "esperado": esperado,
                                                              "tolerancia": 0.01, "comparables": comparables}]
    c, q = ev["caida"], ev["quiebre"]
    bajo = min(e["caida_t3_todas"], e["caida_t3_comparables"]) - 3
    alto = max(e["caida_t3_todas"], e["caida_t3_comparables"]) + 3
    return [
        ("total", "¿Cuánto vendimos en el AF2027?", valor("ventas_netas", e["ventas_af2027"]), None),
        ("comparables", "¿Cómo vinieron las ventas del AF2027 contra el AF2026 en sucursales comparables?",
         variacion("ventas_netas", e["comparables_af2027_como_el_sistema"], True), None),
        ("mascotas", "¿Cuánto vendió la categoría Mascotas en el AF2027?", valor("ventas_netas", e["mascotas_af2027"]), None),
        ("precio", f"¿Cómo cambió el precio promedio de {ev['precios']['categoria']} en el T3 del AF2027 contra el T3 del AF2026?",
         variacion("precio_promedio", e["precio_promedio_t3_variacion"]), None),
        ("marca_propia", "¿Cómo vinieron las ventas de marca propia en el T4 del AF2027 contra el T4 del AF2026?",
         variacion("ventas_netas", e["marca_propia_t4_variacion"]), None),
        ("caida", f"¿Por qué cayeron las ventas de {c['categoria']} en la región {c['region']} en el T3 del AF2027?",
         None, en_rango(round(bajo, 1), round(alto, 1))),
        ("corte", f"¿Por qué cayeron las ventas de la región {ev['corte']['region']} en agosto de 2026?", None,
         dice(si=[r"sin ventas", r"no (hubo|hay|registr|tuv)\w*[^.]{0,30}ventas", r"(10|11|12)[^.]{0,25}agosto", r"cero ventas"],
              etiqueta="encuentra los días sin ventas")),
        ("discontinuado", f"¿Por qué dejó de venderse {e['descripcion_discontinuado']} ({ev['discontinuado']['sku']}) desde enero de 2027?",
         None, dice(no=[r"(se debe|debido|explica|causa)[^.]{0,40}quiebre", r"quiebre de stock (explica|causa)"],
                    etiqueta="no lo atribuye a un quiebre")),
        ("quiebre", f"¿Por qué cayeron las ventas de {q['subcategoria']} en la sucursal {n[q['sucursal']]} en marzo de 2027?",
         None, dice(si=[r"quiebre", r"stock (en )?(0|cero)", r"sin stock", r"agotad", r"faltante"], etiqueta="encuentra el quiebre")),
        ("cierre", f"¿Qué pasó con las ventas de la sucursal {n[ev['cierre']['sucursal']]} en 2027?", None,
         dice(si=[r"sin ventas", r"no (hubo|hay|registr|tiene|tuv)\w*[^.]{0,30}ventas", r"dej[óo] de vender", r"cero", r"cerr", r"cierre"],
              etiqueta="ve que no vende desde enero")),
    ]


async def correr(lista):
    from evaluador import falla, fallos
    from puerta import atender
    salida = []
    for id_, texto, chequeos, regla in lista:
        inicio = time.monotonic()
        r = (await atender([texto], carpeta=str(CARPETA / id_)))[-1]
        if chequeos:
            malos = falla(fallos(chequeos, r["consultas"], r))
            paso, detalle = not malos, "; ".join(malos)
        else:
            paso, detalle = regla(r)
        habla_de_cierre = bool(re.search(r"cerr|cierre", r["texto"].lower()))
        salida.append({"id": id_, "pregunta": texto, "tipo": r.get("tipo"), "ruta": r.get("ruta"), "paso": paso,
                       "detalle": detalle, "texto": r["texto"], "segundos": round(time.monotonic() - inicio),
                       "habla_de_cierre": habla_de_cierre})
        print(f"· {id_}: {'✓' if paso else '✗'} {detalle}", flush=True)
    return salida


def costo():
    import registro
    return sum(l["costo_usd"] for l in registro.leer(registro.LLAMADAS) if l.get("corrida") == registro.CORRIDA)


def main():
    if not ANIO.exists():
        sys.exit("Falta el año simulado: correr antes .venv/bin/python evaluacion/pruebas/anio_simulado.py")
    CARPETA.mkdir(parents=True, exist_ok=True)
    ev = json.loads(Path("salidas/anio/eventos.json").read_text())["eventos"]
    e = esperados(ev)
    (CARPETA / "esperados.json").write_text(json.dumps({"calculados": datetime.now().isoformat(timespec="seconds"), **e},
                                                       ensure_ascii=False, indent=2))
    print("Esperados guardados antes de correr el agente:", CARPETA / "esperados.json", flush=True)
    resultados = asyncio.run(correr(preguntas(ev, e)))
    usd = costo()
    si = lambda x: "✓" if x else "✗"
    coma = lambda x: str(x).replace(".", ",")
    lineas = ["# El agente sobre el año simulado (decisión 90)", "",
              f"Comando: `.venv/bin/python evaluacion/pruebas/agente_anio.py` · base: el AF2027 simulado (decisión 88) · US$ {usd:.3f}", "",
              f"**{sum(r['paso'] for r in resultados)} de {len(resultados)}** pasan los chequeos por código.", "",
              "| Caso | Qué prueba | Tipo → camino | Chequeo |", "|---|---|---|---|"]
    que = {"total": "el AF2027 completo", "comparables": "comparables con una sucursal que cerró",
           "mascotas": "la categoría nueva", "precio": "el aumento de precios (y el efecto mix)",
           "marca_propia": "el cambio de mix", "caida": "una caída de −30 % (segundo oráculo)",
           "corte": "una región sin ventas tres días", "discontinuado": "un producto discontinuado (no es un quiebre)",
           "quiebre": "un quiebre de stock", "cierre": "una sucursal que cerró (la base no lo sabe)"}
    for r in resultados:
        lineas.append(f"| {r['id']} | {que[r['id']]} | {r['tipo']} → {r['ruta']} | {si(r['paso'])} {r['detalle']} |")
    lineas += ["", "## Valores esperados (SQL a mano, guardados antes de correr)", "",
               f"- Ventas AF2027: $ {e['ventas_af2027']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
               f"- Comparables AF2027 contra AF2026: **{coma(e['comparables_af2027_como_el_sistema'])} %** como las define el sistema "
               f"(incluye a {ev['cierre']['sucursal']}, que cerró el {ev['cierre']['fecha']}); "
               f"**{coma(e['comparables_af2027_sin_la_cerrada'])} %** sin ella; todas: {coma(e['todas_af2027'])} %",
               f"- Precio promedio de {ev['precios']['categoria']}, T3 contra T3: {coma(e['precio_promedio_t3_variacion'])} % "
               f"(se plantó +15 % de precio de lista)",
               f"- Marca propia, T4 contra T4: {coma(e['marca_propia_t4_variacion'])} %",
               f"- Caída de {ev['caida']['categoria']} en el {ev['caida']['region']}, T3 contra T3: {coma(e['caida_t3_todas'])} % "
               f"(comparables: {coma(e['caida_t3_comparables'])} %)",
               f"- **Segundo oráculo**: se plantó −30 %; contra lo que habría sido sin el evento se mide "
               f"**{coma(e['caida_plantada_medida'])} %**",
               "", "## Respuestas", ""]
    for r in resultados:
        lineas += [f"**{r['id']}.** {r['pregunta']} ({r['segundos']} s)", "", "> " + r["texto"].replace("\n", "\n> "), ""]
    texto = "\n".join(lineas) + "\n"
    (CARPETA / "resultado.md").write_text(texto)
    Path("trazas/agente_anio.md").write_text(texto)
    print(texto)


if __name__ == "__main__":
    main()
