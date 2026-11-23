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
    return [numero[:3] for numero in _numeros(texto)]


def _numeros(texto):
    """Como numeros_del_texto, con un cuarto dato: si el número está escrito como porcentaje («9 %»)."""
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
        # Y hacia adelante: en «1.722,1 millones frente a 1.825,6 del año anterior», el 1.825,6 también son millones
        # (decisión 105: el control lo leía como 1.825,6 pesos y el informe no salía). Solo si el número tiene la
        # forma del anterior (con decimales o con miles), para no tomar «millones contra 3 sucursales»
        anterior = coincidencias[i - 1] if i > 0 else None
        if (not millones and anterior and anterior.group(2) and ("," in escrito or "." in escrito)
                and not re.match(r"\s*(?:%|pp|puntos)", texto[coincidencia.end():])
                and re.fullmatch(r"\s*(?:frente a|contra|vs\.?|y|a|al|-|–|,)\s*", texto[anterior.end():coincidencia.start()])):
            millones = anterior.group(2)
        if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", escrito):  # 1.247 o 663.149.556,5: puntos de miles
            entero, _, decimales = escrito.replace(".", "").partition(",")
        else:  # 25,9 (coma decimal) o 25.9 (por si escribe con punto)
            entero, _, decimales = escrito.replace(",", ".").partition(".")
        valor = float(f"{entero}.{decimales}" if decimales else entero)
        escala = 1e6 if millones else 1
        porcentaje = bool(re.match(r"\s*%", texto[coincidencia.end():]))
        numeros.append((valor * escala, 0.5001 * 10 ** -len(decimales) * escala, coincidencia.group(0).strip(), porcentaje))
    return numeros


def _valores(objeto, salida, fechas=True):
    """Todos los números de un resultado de una tool (y el año, mes y día de sus fechas, salvo con fechas=False)."""
    if isinstance(objeto, bool):
        return
    if isinstance(objeto, (int, float)):
        salida.append(float(objeto))
    elif isinstance(objeto, str) and FECHA.match(objeto):
        if fechas:
            salida.extend(float(parte) for parte in objeto[:10].split("-"))
    elif isinstance(objeto, str):
        # De un texto solo valen los tamaños («Gaseosa cola Del Sur 2,25 L», «300 g»), no cualquier número: un texto
        # puede traer cifras que no son datos, como el «crecieron 50 %» de la descripción de P0040 (decisión 57)
        for tamaño in TAMAÑO.finditer(objeto):
            salida.extend(v for v, _, _ in numeros_del_texto(tamaño.group(1)))
    elif isinstance(objeto, dict):
        for clave, valor in objeto.items():
            if clave != "sql":  # el SQL tiene números de la fórmula (100, 0) que no son datos
                _valores(valor, salida, fechas)
    elif isinstance(objeto, list):
        for valor in objeto:
            _valores(valor, salida, fechas)


def _nombre(bloque, campo):
    return bloque.get(campo) if isinstance(bloque, dict) else getattr(bloque, campo, None)


def respaldos(mensajes, para_porcentajes=False):
    """Los números que el modelo puede usar: los de los resultados de las tools y los que escribió quien pregunta.
    Con para_porcentajes, sin las partes de las fechas ni ver_modelo (meses 1 a 12): un «9 %» no sale de un mes 9."""
    valores = []
    tools = {_nombre(b, "id"): _nombre(b, "name") for m in mensajes if m["role"] == "assistant" and isinstance(m["content"], list)
             for b in m["content"] if _nombre(b, "type") == "tool_use"}
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
            if para_porcentajes and tools.get(bloque.get("tool_use_id")) == "ver_modelo":
                continue
            try:
                _valores(json.loads(bloque["content"]), valores, fechas=not para_porcentajes)
            except (json.JSONDecodeError, TypeError):
                pass
    return valores


def numeros_sin_respaldo(texto, mensajes):
    """Los números del texto que no coinciden (redondeados como están escritos) con ningún número de respaldo.
    Compara en valor absoluto: «cayó 0,24 pp» respalda a una variación de −0,24."""
    return sin_respaldo(texto, respaldos(mensajes), respaldos(mensajes, para_porcentajes=True))


def valores_de(resultados):
    """Los números de una lista de resultados de calcular (para controlar un texto fuera del loop, como el informe)."""
    valores = []
    _valores(resultados, valores)
    return valores


def sin_respaldo(texto, valores, valores_pct=None):
    """Con valores_pct (decisión 122), un número escrito con % se controla aunque sea un entero chico, y solo contra
    esos valores: el «9 %» de PROMO001 (era 0,09 %) pasaba por chico y por el mes 9 de ver_modelo."""
    valores = [abs(v) for v in valores]
    pct = None if valores_pct is None else [abs(v) for v in valores_pct]
    sueltos = []
    for valor, tolerancia, escrito, porcentaje in _numeros(texto):
        controlar_pct = porcentaje and pct is not None
        if valor.is_integer() and valor <= MAX_SIN_CONTROL and "," not in escrito and not controlar_pct:
            continue
        # Redondeado (25,6664 → 25,67) o truncado (→ 25,66): los dos salen de la consulta. Truncar no es inventar,
        # y marcarlo costaba una vuelta de corrección (P07, decisión 71). La tolerancia es medio dígito del último decimal
        digito = tolerancia / 0.5001
        if not any(abs(valor - v) <= tolerancia or 0 <= v - valor < digito for v in (pct if controlar_pct else valores)):
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


FECHA_ESCRITA = re.compile(r"\b\d{1,2}\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|"
                           r"octubre|noviembre|diciembre)\b|\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b", re.IGNORECASE)


def numeros_de_consultas_en(texto, consultas):
    """¿El texto trae alguna cifra de los resultados de estas consultas? (sin contar los enteros chicos ni el año).
    Lo usan el evaluador (la sin dato, decisión 76) y el control de períodos fuera de la base (decisión 97)."""
    valores = valores_de([c["resultado"] for c in consultas])
    # El día de una fecha no es una cifra: «hasta el 30 de abril de 2026» coincidía con un resultado igual a 30 y una
    # respuesta sin dato contaba como respondida (decisión 97)
    texto = FECHA_ESCRITA.sub(" ", texto)
    for valor, tolerancia, escrito in numeros_del_texto(texto):
        if (valor.is_integer() and valor <= MAX_SIN_CONTROL and "," not in escrito) or 1900 <= valor <= 2100:
            continue
        if any(abs(valor - abs(v)) <= tolerancia for v in valores):
            return True
    return False


# Decisión 97. El test 3 (decisión 96): ante «el AF2027» o «marzo de 2024», fuera de la base, el agente dice que no hay
# datos pero a veces agrega el número del período más cercano, y una vez el registro lo guardó como la respuesta. Si
# todos los períodos que la pregunta escribe explícitamente caen fuera de la base, la respuesta no lleva números de
# consultas ni valor: dice que no hay datos y puede ofrecer el período más cercano, sin su número (lo eligió el usuario).
# Solo períodos escritos («AF2027», «año fiscal 2027», «marzo de 2024», «en 2023», «15/03/2024»); lo relativo («el mes
# pasado», «ayer») se cuenta desde el último dato y ya se declara (decisión 62).
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]


def _fin_de_mes(anio, mes):
    from datetime import date, timedelta
    return (date(anio + mes // 12, mes % 12 + 1, 1) - timedelta(days=1))


def periodos_escritos(pregunta):
    """[(cómo está escrito, desde, hasta)] de los períodos explícitos de la pregunta."""
    from datetime import date
    texto = sin_tildes(pregunta)
    salida = []
    for m in re.finditer(r"\b(?:af|ano fiscal|anio fiscal)\s*(20\d\d)\b", texto):
        n = int(m.group(1))
        salida.append((m.group(0), date(n - 1, 5, 1), date(n, 4, 30)))
    fiscales = [m.span() for m in re.finditer(r"\b(?:af|ano fiscal|anio fiscal)\s*20\d\d\b", texto)]
    for m in re.finditer(rf"\b({'|'.join(MESES)})\s+(?:de|del)\s+(20\d\d)\b", texto):
        mes, anio = MESES.index(m.group(1)) + 1, int(m.group(2))
        salida.append((m.group(0), date(anio, mes, 1), _fin_de_mes(anio, mes)))
    meses = [m.span() for m in re.finditer(rf"\b(?:{'|'.join(MESES)})\s+(?:de|del)\s+20\d\d\b", texto)]
    for m in re.finditer(r"\b(?:en|de|del|ano|anio|el)\s+(20\d\d)\b", texto):
        dentro = lambda s: any(a <= m.start(1) < b for a, b in fiscales + meses)  # el año de «marzo de 2024» o «AF2027»
        if not dentro(m):
            n = int(m.group(1))
            salida.append((m.group(0), date(n, 1, 1), date(n, 12, 31)))
    for m in re.finditer(r"\b(\d{1,2})[/-](\d{1,2})[/-](20\d\d)\b", texto):
        try:
            d = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            continue
        salida.append((m.group(0), d, d))
    return salida


def periodo_fuera_de_la_base(pregunta):
    """Los períodos escritos, si todos caen enteros fuera de la base; si no, []."""
    from datetime import date
    from procesador_capa_semantica import COBERTURA
    desde, hasta = date.fromisoformat(COBERTURA["ventas_desde"]), date.fromisoformat(COBERTURA["ventas_hasta"])
    periodos = periodos_escritos(pregunta)
    if periodos and all(h < desde or d > hasta for _, d, h in periodos):
        return periodos
    return []


# Decisión 116. El test 4 (decisión 115): ante «la sucursal S99», «la región Este» o «la categoría Electrónica», que no
# están en la base, el agente dice que no existen pero 7 de 9 veces agrega números de otra cosa «de referencia» (el
# total de la cadena, las cuatro regiones, las seis categorías). Es el patrón de la 97 con valores en lugar de períodos.
# Si todos los valores que la pregunta nombra junto a «sucursal», «región», «categoría» o «subcategoría» no están en la
# base, la respuesta no lleva números de consultas ni valor. Solo con la palabra de la dimensión delante (o un código
# S99): sin ella, el código no puede saber qué es un nombre («Coca-Cola» puede ser un producto, una marca o nada).
PALABRA_DE = {"sucursal": r"(?i:sucursal(?:es)?)", "region": r"(?i:regi[oó]n(?:es)?)",
              "categoria": r"(?i:(?:sub)?categor[ií]as?)"}
NOMBRE = r"((?:[A-ZÁÉÍÓÚÑ0-9][\wáéíóúñ-]*)(?:\s+(?:(?:de|del|la|las|los)\s+)?[A-ZÁÉÍÓÚÑ][\wáéíóúñ-]*){0,3})"


@functools.cache
def valores_conocidos():
    """Por dimensión, los valores de la base sin tildes y en minúscula (las sucursales, por código y por nombre)."""
    import duckdb
    from procesador_capa_semantica import BASE
    with duckdb.connect(BASE, read_only=True) as con:
        lista = lambda sql: [sin_tildes(str(v)) for (v,) in con.execute(sql).fetchall()]
        sucursales = lista("SELECT sucursal_id FROM sucursales UNION SELECT nombre FROM sucursales")
        regiones = lista("SELECT DISTINCT region FROM sucursales")
        # «las sucursales del Oeste»: después de «sucursal» también puede venir una región
        return {"sucursal": sucursales + [n.removeprefix("almacenes del sur ").strip() for n in sucursales] + regiones,
                "region": regiones,
                "categoria": lista("SELECT DISTINCT categoria FROM productos UNION SELECT DISTINCT subcategoria FROM productos")}


def valores_nombrados(pregunta):
    """[(dimensión, cómo está escrito, ¿está en la base?)] de los valores que la pregunta nombra con su dimensión."""
    conocidos = valores_conocidos()
    esta = lambda dimension, escrito: any(sin_tildes(escrito).startswith(k) or k.startswith(sin_tildes(escrito))
                                          for k in conocidos[dimension])
    salida = []
    for dimension, palabra in PALABRA_DE.items():
        for m in re.finditer(rf"\b{palabra}\s+(?:(?:de|del|la|el)\s+)?{NOMBRE}", pregunta):
            if not re.match(r"(?i)(af|t|q)\d|20\d\d|" + "|".join(MESES), sin_tildes(m.group(1))):  # «top 5 sucursales AF26»
                salida.append((dimension, m.group(1), esta(dimension, m.group(1))))
    escritos = {e for _, e, _ in salida}
    for m in re.finditer(r"\bS\d{2,3}\b", pregunta):  # un código de sucursal suelto: «¿cuánto vendió S99?»
        if m.group(0) not in escritos:
            salida.append(("sucursal", m.group(0), esta("sucursal", m.group(0))))
    return salida


def valores_que_no_estan(pregunta):
    """Los valores nombrados, si ninguno está en la base; si alguno está, [] (la respuesta puede tener su número)."""
    nombrados = valores_nombrados(pregunta)
    return [(d, e) for d, e, esta in nombrados] if nombrados and not any(esta for *_, esta in nombrados) else []
