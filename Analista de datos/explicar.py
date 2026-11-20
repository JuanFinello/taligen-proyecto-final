"""La consulta explicada en castellano (decisión 83, «lo que sube la vara»): junto al número, qué se filtró y cómo se
calculó, dicho para alguien que no lee SQL. Lo arma el código con los argumentos que de verdad corrieron y las
descripciones de la capa semántica, no el modelo: así no puede contar una consulta distinta de la que se hizo."""
import json
from datetime import date

from graficos import NOMBRES
from procesador_capa_semantica import ver_modelo

MEDIDAS = {m["id"]: m for m in ver_modelo()["medidas"]}
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]
DIMENSIONES = {"region": "región", "categoria": "categoría", "subcategoria": "subcategoría", "sucursal": "sucursal",
               "nombre_sucursal": "sucursal", "formato": "formato", "marca": "marca", "producto": "producto",
               "proveedor": "proveedor", "nombre_proveedor": "proveedor", "mes": "mes", "anio": "año",
               "anio_fiscal": "año fiscal", "trimestre_fiscal": "trimestre fiscal", "mes_fiscal": "mes fiscal",
               "semana": "semana", "fecha": "día", "es_marca_propia": "marca propia o no"}
PERIODO = {"anio", "mes", "anio_fiscal", "trimestre_fiscal", "mes_fiscal", "fecha", "semana"}


def lista(valores):
    valores = [str(v) for v in valores]
    return valores[0] if len(valores) == 1 else ", ".join(valores[:-1]) + " o " + valores[-1]


def fecha(texto):
    return date.fromisoformat(str(texto)[:10]).strftime("%d-%m-%Y")


def mes_calendario(mes_fiscal, anio_fiscal):
    """El AF N arranca en mayo de N−1: el mes fiscal 1 es mayo."""
    mes = (mes_fiscal + 3) % 12 + 1
    return mes, anio_fiscal - 1 if mes >= 5 else anio_fiscal


def periodo(filtros):
    """El período de los filtros, en palabras: «el T2 del año fiscal 2026 (agosto a octubre de 2025)»."""
    f = {k: v for k, v in filtros.items() if k in PERIODO}
    como_lista = lambda v: v if isinstance(v, list) else [v]
    if isinstance(f.get("fecha"), dict):
        return f"del {fecha(f['fecha']['desde'])} al {fecha(f['fecha']['hasta'])}"
    if "fecha" in f:
        return "los días " + lista(fecha(x) for x in como_lista(f["fecha"]))
    if isinstance(f.get("semana"), dict):  # un rango de semanas, como el de días (decisión 69)
        return f"las semanas del {fecha(f['semana']['desde'])} al {fecha(f['semana']['hasta'])}"
    if "semana" in f:
        return "la semana del " + lista(fecha(x) for x in como_lista(f["semana"]))
    if "anio_fiscal" in f and not isinstance(f["anio_fiscal"], list):
        af = f["anio_fiscal"]
        if "trimestre_fiscal" in f:
            partes = []
            for t in como_lista(f["trimestre_fiscal"]):
                (m1, a1), (m3, a3) = mes_calendario(3 * t - 2, af), mes_calendario(3 * t, af)
                partes.append(f"el T{t} del año fiscal {af} ({MESES[m1 - 1]}" + (f" de {a1}" if a1 != a3 else "")
                              + f" a {MESES[m3 - 1]} de {a3})")
            return lista(partes)
        if "mes_fiscal" in f and len(como_lista(f["mes_fiscal"])) > 6:  # «el año fiscal 2026 sin diciembre de 2025»
            faltan = [m for m in range(1, 13) if m not in como_lista(f["mes_fiscal"])]
            return (f"el año fiscal {af} sin " + lista(f"{MESES[m - 1]} de {a}" for m, a in
                                                        (mes_calendario(x, af) for x in faltan)).replace(" o ", " ni "))
        if "mes_fiscal" in f:
            return lista(f"{MESES[m - 1]} de {a}" for m, a in (mes_calendario(x, af) for x in como_lista(f["mes_fiscal"])))
        if "mes" in f:  # meses del calendario dentro del año fiscal: de mayo a diciembre son del año anterior
            meses = [(m, af - 1 if m >= 5 else af) for m in como_lista(f["mes"])]
            if len(meses) == 1:
                return f"{MESES[meses[0][0] - 1]} de {meses[0][1]}"
            (m1, a1), (m2, a2) = meses[0], meses[-1]
            return f"de {MESES[m1 - 1]} de {a1} a {MESES[m2 - 1]} de {a2} (año fiscal {af})"
        return f"el año fiscal {af} (mayo de {af - 1} a abril de {af})"
    if "anio_fiscal" in f:
        return "los años fiscales " + lista(f["anio_fiscal"])
    if "mes" in f:
        seguidos = sorted(como_lista(f["mes"]))
        if len(seguidos) > 2 and seguidos == list(range(seguidos[0], seguidos[-1] + 1)):
            meses = f"{MESES[seguidos[0] - 1]} a {MESES[seguidos[-1] - 1]}"  # «agosto a octubre», no «agosto, septiembre o octubre»
        else:
            meses = lista(MESES[m - 1] for m in como_lista(f["mes"]))
        return meses + (f" de {lista(como_lista(f['anio']))}" if "anio" in f else " (de todos los años)")
    if "anio" in f:
        return "el año calendario " + lista(como_lista(f["anio"]))
    return "todo el período de la base"


def valor(dimension, v):
    if isinstance(v, bool):
        return "marca propia" if v else "marcas de terceros"
    nombre = NOMBRES.get(str(v))
    return f"{v} ({nombre})" if nombre and dimension in ("sucursal", "proveedor") else str(v)


def alcance(filtros):
    """Los filtros que no son de período: «categoría Perfumería · región Sur o Norte»."""
    partes = []
    for d, v in filtros.items():
        if d in PERIODO:
            continue
        if d == "es_marca_propia":
            partes.append("solo " + valor(d, v))
            continue
        valores = v if isinstance(v, list) else [v]
        partes.append(f"{DIMENSIONES.get(d, d)} {lista(valor(d, x) for x in valores)}")
    return " · ".join(partes) or "toda la cadena"


def explicar(consulta):
    """Una consulta registrada ({tool, argumentos, …}) en castellano, en pocas líneas."""
    a = consulta["argumentos"]
    if consulta["tool"] == "buscar_producto":
        return f"Buscó en el maestro de productos los que se llaman parecido a «{a.get('texto', '')}», para usar su código."
    if consulta["tool"] == "consultar_sql":
        # Del SQL no se puede saber qué calcula: si empieza con un comentario, ese comentario lo dice (decisión 106)
        comentario = []
        for linea in str(a.get("sql", "")).strip().splitlines():
            if not linea.strip().startswith("--"):
                break
            comentario.append(linea.strip().removeprefix("--").strip())
        que = " ".join(comentario).rstrip(".")
        return ((f"{que}. " if que else "Listado sacado directo de la base. ")
                + "Con SQL directo sobre la base: no es una medida de la capa semántica, se usa para lo que la capa no "
                  "cubre.")
    if consulta["tool"] != "calcular":
        return f"{consulta['tool']} {json.dumps(a, ensure_ascii=False)}"
    medida = MEDIDAS.get(a.get("medida"), {"nombre": a.get("medida"), "descripcion": ""})
    filtros = a.get("filtros") or {}
    descripcion = medida.get("descripcion", "").split(". ")[0].rstrip(".")  # la primera oración: el resto es para Haiku
    lineas = [f"Qué se midió: {medida['nombre']}" + (f". {descripcion}." if descripcion else "."),
              f"De qué: {alcance(filtros)}.", f"Cuándo: {periodo(filtros)}."]
    if a.get("comparar_con"):
        lineas.append(f"Contra: {periodo({**filtros, **a['comparar_con']})}"
                      + (", solo con las sucursales que estaban abiertas en los dos períodos (comparables)"
                         if a.get("comparables") else ", con todas las sucursales") + ".")
    elif a.get("comparables"):
        lineas.append("Solo sucursales comparables (abiertas en todo el período).")
    if a.get("agrupar_por"):
        grupos = [DIMENSIONES.get(d, d) for d in a["agrupar_por"] if not d.startswith("nombre_")]
        orden = "de mayor a menor" if a.get("orden", "desc") == "desc" else "de menor a mayor"
        if a["agrupar_por"][0] in PERIODO:  # por tiempo, el informe lo muestra en orden de fechas
            orden = "en orden de fechas"
        corte = f", los {a['limite']} primeros" if a.get("limite") else ""
        lineas.append(f"Abierto por {lista(grupos) if len(grupos) == 1 else ' y '.join(grupos)}, {orden}{corte}.")
    return "\n".join(lineas)
