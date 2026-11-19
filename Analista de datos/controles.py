"""Controles que corre el código sobre lo que escribe el modelo (decisión 49; son los hooks de la semana 4).
numeros_sin_respaldo: cada número de una respuesta tiene que salir de una consulta (o de la pregunta).
grupos_sin_filtro: cada categoría o región que nombra la pregunta tiene que estar en alguna consulta (decisión 95)."""
import functools
import json
import re
import unicodedata

# Un número en castellano: 1.247 · 25,9 · 663.149.556 · 0,24. Pegado a una letra no cuenta (AF2026, T2, PR01, C3)
NUMERO = re.compile(r"(?<![\w.,])(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)(?![\w])(\s*(?:M\b|millones|mill\.))?")
FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}")
TAMAÑO = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:g|kg|ml|cc|l|lt|lts|L|un|u)\b")
AVISO = "Estos números de tu respuesta no salen de ninguna consulta"  # el mensaje de corrección no respalda nada
MAX_SIN_CONTROL = 12  # enteros chicos sin decimales (los 4 trimestres, las 6 categorías, «2 o 3 oraciones»): no se controlan


def numeros_del_texto(texto):
    """[(valor, tolerancia, como_esta_escrito)] de cada número del texto, con la tolerancia de su redondeo."""
    numeros = []
    coincidencias = list(NUMERO.finditer(texto))
    for i, coincidencia in enumerate(coincidencias):
        escrito, millones = coincidencia.group(1), coincidencia.group(2)
        # Un rango comparte la escala: en «entre 101 y 120 millones» o «de 101 a 120 millones», el 101 también son
        # millones (decisión 82; el control lo leía como 101 pesos y frenaba el informe)
        siguiente = coincidencias[i + 1] if i + 1 < len(coincidencias) else None
        if (not millones and siguiente and siguiente.group(2) and not re.fullmatch(r"(?:19|20)\d\d", escrito)  # un año, no
                and re.fullmatch(r"\s*(?:y|a|al|-|–)\s*", texto[coincidencia.end():siguiente.start()])):
            millones = siguiente.group(2)
        if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", escrito):  # 1.247 o 663.149.556,5: puntos de miles
            entero, _, decimales = escrito.replace(".", "").partition(",")
        else:  # 25,9 (coma decimal) o 25.9 (por si escribe con punto)
            entero, _, decimales = escrito.replace(",", ".").partition(".")
        valor = float(f"{entero}.{decimales}" if decimales else entero)
        escala = 1e6 if millones else 1
        numeros.append((valor * escala, 0.5001 * 10 ** -len(decimales) * escala, coincidencia.group(0).strip()))
    return numeros


def _valores(objeto, salida):
    """Todos los números de un resultado de una tool (y el año, mes y día de sus fechas)."""
    if isinstance(objeto, bool):
        return
    if isinstance(objeto, (int, float)):
        salida.append(float(objeto))
    elif isinstance(objeto, str) and FECHA.match(objeto):
        salida.extend(float(parte) for parte in objeto[:10].split("-"))
    elif isinstance(objeto, str):
        # De un texto solo valen los tamaños («Gaseosa cola Del Sur 2,25 L», «300 g»), no cualquier número: un texto
        # puede traer cifras que no son datos, como el «crecieron 50 %» de la descripción de P0040 (decisión 57)
        for tamaño in TAMAÑO.finditer(objeto):
            salida.extend(v for v, _, _ in numeros_del_texto(tamaño.group(1)))
    elif isinstance(objeto, dict):
        for clave, valor in objeto.items():
            if clave != "sql":  # el SQL tiene números de la fórmula (100, 0) que no son datos
                _valores(valor, salida)
    elif isinstance(objeto, list):
        for valor in objeto:
            _valores(valor, salida)


def respaldos(mensajes):
    """Los números que el modelo puede usar: los de los resultados de las tools y los que escribió quien pregunta."""
    valores = []
    for mensaje in mensajes:
        if mensaje["role"] != "user":
            continue
        if isinstance(mensaje["content"], str):
            if mensaje["content"].startswith(AVISO):
                continue
            valores += [v for v, _, _ in numeros_del_texto(mensaje["content"])]
            continue
        for bloque in mensaje["content"]:
            if bloque.get("type") != "tool_result" or bloque.get("is_error"):
                continue
            try:
                _valores(json.loads(bloque["content"]), valores)
            except (json.JSONDecodeError, TypeError):
                pass
    return valores


def numeros_sin_respaldo(texto, mensajes):
    """Los números del texto que no coinciden (redondeados como están escritos) con ningún número de respaldo.
    Compara en valor absoluto: «cayó 0,24 pp» respalda a una variación de −0,24."""
    return sin_respaldo(texto, respaldos(mensajes))


def valores_de(resultados):
    """Los números de una lista de resultados de calcular (para controlar un texto fuera del loop, como el informe)."""
    valores = []
    _valores(resultados, valores)
    return valores


def sin_respaldo(texto, valores):
    valores = [abs(v) for v in valores]
    sueltos = []
    for valor, tolerancia, escrito in numeros_del_texto(texto):
        if valor.is_integer() and valor <= MAX_SIN_CONTROL and "," not in escrito:
            continue
        # Redondeado (25,6664 → 25,67) o truncado (→ 25,66): los dos salen de la consulta. Truncar no es inventar,
        # y marcarlo costaba una vuelta de corrección (P07, decisión 71). La tolerancia es medio dígito del último decimal
        digito = tolerancia / 0.5001
        if not any(abs(valor - v) <= tolerancia or 0 <= v - valor < digito for v in valores):
            sueltos.append(escrito)
    return sueltos


# Decisión 95. El test 2 (decisión 94) mostró que «Almacén: diferencia de margen %…» se respondía con toda la cadena
# las tres veces, aunque el glosario dice que «Almacén» es la categoría: lo escrito en el prompt no alcanza siempre.
# Este control es código: si la pregunta nombra una categoría o una región y ninguna consulta la filtra, la abre por
# esa dimensión o filtra algo más fino de adentro (un producto de la categoría, una sucursal de la región), la
# respuesta vuelve a Haiku para que la corrija o explique en supuestos por qué no la usó.
NOMBRADAS = {"categoria": ("subcategoria", "producto", "marca"), "region": ("sucursal",)}


def sin_tildes(texto):
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


@functools.cache
def nombres_propios():
    """Los nombres de la base que traen una palabra de categoría o de región («Almacenes del Sur», la marca «Del Sur»,
    el proveedor «Lácteos La Pradera», la sucursal «Puerto Norte», 37 productos): antes de buscar se sacan de la
    pregunta, los más largos primero, para que «la gaseosa cola Del Sur» no cuente como la región Sur."""
    import duckdb
    from procesador_capa_semantica import BASE
    with duckdb.connect(BASE, read_only=True) as con:
        nombres = [n for (n,) in con.execute("""SELECT marca FROM productos UNION SELECT descripcion FROM productos
                                                UNION SELECT nombre FROM proveedores UNION SELECT nombre FROM sucursales""").fetchall()]
    largos = {sin_tildes(n) for n in nombres}
    largos |= {re.sub(r"\s*(s\.a\.|\(marca propia\))", "", n).strip() for n in largos}  # «Industrias Del Sur S.A. (marca propia)»
    largos |= {n.removeprefix("almacenes del sur ").strip() for n in largos} | {"almacenes del sur"}  # «Puerto Norte» solo
    return sorted((n for n in largos if n), key=len, reverse=True)


@functools.cache
def valores_de_dimension(dimension):
    from procesador_capa_semantica import ver_modelo  # acá y no arriba: los valores salen de la base (decisión 62)
    return ver_modelo()["dimensiones"][dimension]["valores"]


def _usa(consulta, dimension, valor):
    """¿Esta consulta tiene en cuenta ese valor: lo filtra, abre por su dimensión o filtra algo más fino de adentro?"""
    argumentos = consulta.get("argumentos") or {}
    if consulta.get("tool") == "consultar_sql":
        return sin_tildes(valor) in sin_tildes(argumentos.get("sql", ""))
    filtros = argumentos.get("filtros") or {}
    elegido = filtros.get(dimension)
    return (elegido == valor or (isinstance(elegido, list) and valor in elegido)
            or dimension in (argumentos.get("agrupar_por") or [])
            or any(filtros.get(fina) for fina in NOMBRADAS[dimension]))


def grupos_sin_filtro(pregunta, consultas, supuestos=()):
    """[(dimensión, valor)] que la pregunta nombra y ninguna consulta usa. No cuentan los que ya explicó en supuestos."""
    texto = sin_tildes(pregunta)
    for nombre in nombres_propios():
        texto = re.sub(rf"\b{re.escape(nombre)}\b", " ", texto)
    explicados = sin_tildes(" ".join(supuestos))
    faltan = []
    for dimension in NOMBRADAS:
        for valor in valores_de_dimension(dimension):
            palabra = rf"\b{re.escape(sin_tildes(valor))}\b"
            if re.search(palabra, texto) and not re.search(palabra, explicados) \
                    and not any(_usa(c, dimension, valor) for c in consultas):
                faltan.append((dimension, valor))
    return faltan
