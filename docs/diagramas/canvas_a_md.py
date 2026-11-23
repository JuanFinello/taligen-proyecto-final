"""Genera las páginas Markdown de los canvas de Obsidian, para leerlos en GitHub: el diagrama Mermaid con los
nodos, grupos y flechas del canvas, y abajo el texto de cada tarjeta.
Uso, desde la raíz del repo: python3 docs/diagramas/canvas_a_md.py docs/diagramas"""
import json, re, sys
from pathlib import Path

D = Path(sys.argv[1])

def titulo(n):
    if n["type"] == "group":
        return n["label"]
    t = n["text"].strip().split("\n")[0]
    return re.sub(r"^#+\s*", "", t)

def etiqueta(n, cortar=True):
    t = titulo(n).replace("`", "").replace("*", "").replace('"', "'")
    t = re.sub(r"\s*·\s*[\w_]+\.py.*$", "", t) if cortar else t
    t = re.sub(r"\(medida, filtros.*\)", "()", t)
    return t

def dentro(n, g):
    return (g["x"] <= n["x"] < g["x"] + g["width"]) and (g["y"] <= n["y"] < g["y"] + g["height"])

def ancla(t):
    t = re.sub(r"[^\w\s-]", "", t.lower()).strip()
    return re.sub(r"\s+", "-", t)

def md_github(texto):
    """Obsidian respeta los saltos de línea; GitHub no. Saltos duros y tablas separadas."""
    out, en_codigo = [], False
    lineas = texto.strip().split("\n")
    lineas[0] = re.sub(r"^#+\s*", "", lineas[0])
    lineas = lineas[1:]
    for i, l in enumerate(lineas):
        if l.startswith("```"):
            en_codigo = not en_codigo
            out.append(l); continue
        if en_codigo:
            out.append(l); continue
        l = re.sub(r"^(#+)\s", lambda m: "#" * min(len(m.group(1)) + 2, 6) + " ", l)
        es_tabla = l.lstrip().startswith("|")
        prev = out[-1] if out else ""
        prev_tabla = prev.lstrip().startswith("|")
        if es_tabla and prev.strip() and not prev_tabla:
            out.append("")
        if not es_tabla and prev_tabla and l.strip():
            out.append("")
        sig = lineas[i + 1] if i + 1 < len(lineas) else ""
        duro = (l.strip() and sig.strip() and not es_tabla and not l.startswith("#")
                and not sig.lstrip().startswith(("|", "- ", "* ", "#", "```"))
                and not re.match(r"\s*\d+\.\s", sig))
        out.append(l + ("  " if duro else ""))
    return "\n".join(out).strip()

def pagina(canvas, nombre_md, titulo_pag, intro, orden, direccion="LR", excluir_diagrama=(), subgrupos=None):
    d = json.loads((D / canvas).read_text())
    nodos = {n["id"]: n for n in d["nodes"]}
    aristas = d.get("edges", [])
    grupos = [n for n in d["nodes"] if n["type"] == "group"]
    usados = {e["fromNode"] for e in aristas} | {e["toNode"] for e in aristas}
    # grupos con aristas: sus miembros también van
    for g in grupos:
        if g["id"] in usados:
            usados |= {n["id"] for n in d["nodes"] if n["type"] == "text" and dentro(n, g)}
    usados -= set(excluir_diagrama)
    # grupo contenedor (el más chico que lo contiene y está en el diagrama, o el que agrupa varias)
    def grupo_de(n):
        cand = [g for g in grupos if g["id"] != n["id"] and dentro(n, g)
                and sum(1 for m in d["nodes"] if m["type"] == "text" and dentro(m, g)) > 1]
        return min(cand, key=lambda g: g["width"] * g["height"]) if cand else None
    orden_canvas = [n["id"] for n in d["nodes"] if n["id"] in usados]  # orden estable: el del archivo
    sub = {}
    for i in orden_canvas:
        n = nodos[i]
        if n["type"] == "group":
            continue
        g = grupo_de(n)
        sub.setdefault(g["id"] if g else None, []).append(i)
    if subgrupos:
        sub = {}
        for nombre, ids in subgrupos.items():
            sub[nombre] = [i for i in ids if i in usados]
            nodos.setdefault(nombre, {"type": "group", "label": nombre, "id": nombre})
        resto = [i for i in orden_canvas if nodos[i]["type"] != "group" and not any(i in v for v in subgrupos.values())]
        if resto: sub[None] = resto
    L = [f"# {titulo_pag}", "", intro, "", "```mermaid", f"flowchart {direccion}"]
    for gid, miembros in sub.items():
        if gid is None:
            for i in miembros:
                L.append(f'    {i}["{etiqueta(nodos[i])}"]')
        else:
            sid = re.sub(r"\W", "_", gid)
            L.append(f'    subgraph {sid}["{etiqueta(nodos[gid], cortar=False)}"]')
            for i in miembros:
                L.append(f'        {i}["{etiqueta(nodos[i])}"]')
            L.append("    end")
    for e in aristas:
        if e["fromNode"] in excluir_diagrama or e["toNode"] in excluir_diagrama:
            continue
        lab = e.get("label", "").replace('"', "'")
        flecha = f' -->|"{lab}"| ' if lab else " --> "
        L.append(f"    {e['fromNode']}{flecha}{e['toNode']}")
    L += ["```", ""]
    # tarjetas
    vistos = set()
    for item in orden:
        if isinstance(item, str) and item.startswith("## "):
            L += [item, ""]; continue
        n = nodos[item]; vistos.add(item)
        L += [f"### {titulo(n).replace('`', '')}" if n["type"] == "text" else "", "", md_github(n["text"]), ""]
    falt = [n["id"] for n in d["nodes"] if n["type"] == "text" and n["id"] not in vistos]
    assert not falt, falt
    (D / nombre_md).write_text("\n".join(L).rstrip() + "\n")

pagina("Diseño del agente.canvas", "diseno_del_agente.md", "Diseño del agente",
    "Versión para leer en GitHub del canvas [`Diseño del agente.canvas`](Diseño%20del%20agente.canvas) (que se abre con Obsidian): el diagrama con sus flechas y, abajo, el texto de cada tarjeta. Es el canvas de trabajo del proyecto: los resultados al día están en [evaluacion.md](../evaluacion.md).",
    ["titulo",
     "## El recorrido", "pregunta", "interfaz", "programado", "puerta", "agente", "s3_plan", "editor",
     "s3_analistas", "analista2", "analista3", "analista4", "t_ver", "t_calc", "capa", "glosario", "capa_py",
     "base", "verificar", "hooks", "s3_registro", "s3_pdf", "salida", "evaluador", "chequeos", "resumen_s1", "pruebas",
     "## Por qué el diseño multi-agente", "s3_porque", "s3_permisos", "s3_costo",
     "## Avance por semana", "s2", "s3", "s4", "s5", "s7"],
    excluir_diagrama=("titulo",), direccion="TD")

dims = ["fechas", "sucursales", "productos", "proveedores", "promociones"]
d = json.loads((D / "Modelo de datos.canvas").read_text())
xs = sorted([n["id"] for n in d["nodes"] if n["type"] == "text" and n["id"].startswith("x_")],
            key=lambda i: (dims.index(i.split("_")[1]) if i.split("_")[1] in dims else 9, i))
pagina("Modelo de datos.canvas", "modelo_de_datos.md", "Modelo de datos",
    "Versión para leer en GitHub del canvas [`Modelo de datos.canvas`](Modelo%20de%20datos.canvas) (que se abre con Obsidian): el esquema con sus joins y, abajo, cada tabla y cada cruce entre tablas, con lo que se encontró en los datos. El resumen está en [datos.md](../datos.md).",
    ["titulo", "## Hechos", "ventas", "stock", "presupuesto",
     "## Dimensiones", *dims,
     "## Cruces", "datos_presupuesto", *xs],
    excluir_diagrama=("titulo",), direccion="LR",
    subgrupos={"Hechos": ["ventas", "stock", "presupuesto"], "Dimensiones": dims,
               "Cruces": ["datos_presupuesto", *xs]})
print("ok")
