"""Hooks del loop del agente (semana 4): qué se revisa antes de cada tool, después de cada tool y al terminar.
Si un hook frena, devuelve el motivo y el loop se lo pasa al modelo como el error de la tool, para que corrija."""
import json

import duckdb

from controles import AVISO, grupos_sin_filtro, numeros_sin_respaldo

_PARSER = duckdb.connect()  # en memoria, sin base: solo para leer el tipo de cada sentencia

# Qué tools puede usar cada agente. Lo impone el código, no el prompt: el modelo solo ve las suyas, y si pide otra,
# antes_de_tool la frena. Una tool nueva del servidor no le llega a nadie hasta que se la agregue acá
PERMITIDAS = {
    "analista": {"ver_modelo", "calcular", "buscar_producto", "consultar_sql"},
    "coordinador": set(),  # planifica y redacta con lo que traen los analistas: no consulta la base
}


def tools_de(agente, tools):
    """De las tools que ofrece el servidor, las que puede ver este agente."""
    return [tool for tool in tools if tool["name"] in PERMITIDAS[agente]]


def antes_de_tool(agente, nombre, argumentos):
    """Motivo para no correr la tool, o None si puede correr."""
    if nombre not in PERMITIDAS[agente]:
        return f"La tool {nombre} no está permitida para el {agente}."
    if nombre == "consultar_sql":
        return _solo_un_select(argumentos.get("sql", ""))
    return None


def _solo_un_select(sql):
    # El parser de DuckDB dice el tipo de cada sentencia: no hace falta adivinarlo mirando el texto
    try:
        sentencias = _PARSER.extract_statements(sql)
    except duckdb.Error as error:
        return f"El SQL no se pudo leer: {error}"
    if len(sentencias) != 1:
        return f"consultar_sql acepta una sola sentencia y llegaron {len(sentencias)}."
    if sentencias[0].type != duckdb.StatementType.SELECT:
        return f"consultar_sql solo acepta SELECT; esta sentencia es {sentencias[0].type.name}."
    return None


def despues_de_tool(nombre, argumentos, resultado):
    """La consulta para registrar (qué se pidió y qué volvió, con su SQL), o None si no hay nada que registrar."""
    if nombre == "ver_modelo" or resultado.is_error:
        return None
    return {"tool": nombre, "argumentos": argumentos, "resultado": json.loads(resultado.content[0].text)}


def al_terminar(texto, mensajes):
    """Los números de la respuesta final que no salen de ninguna consulta ni de la pregunta (decisión 49)."""
    return numeros_sin_respaldo(texto, mensajes)


def pedido_de_correccion(sueltos):
    """El motivo que recibe el modelo cuando al_terminar encuentra números sin respaldo."""
    return (f"{AVISO}: {', '.join(sueltos)}. "
            "No hagas cuentas propias (restas, sumas, promedios). Reescribí la respuesta completa: "
            "sacá esos números o reemplazalos por uno que salga de una consulta; si necesitás un dato "
            "que no consultaste, consultalo con calcular.")


def grupos_no_usados(pregunta, consultas, supuestos):
    """Al terminar, también: las categorías y regiones que nombra la pregunta y ninguna consulta usa (decisión 95)."""
    return grupos_sin_filtro(pregunta, consultas, supuestos)


def pedido_de_filtro(faltan):
    """El motivo que recibe el modelo cuando la pregunta nombra un grupo que ninguna consulta usa."""
    nombres = ", ".join(f"{'la categoría' if d == 'categoria' else 'la región'} {v}" for d, v in faltan)
    return (f"La pregunta nombra {nombres} y ninguna de tus consultas la filtra ni abre por esa dimensión: la respuesta "
            "puede ser de toda la cadena y no de lo que se preguntó. Si la pregunta se refiere a eso, volvé a consultar "
            "con ese filtro y reescribí la respuesta completa. Si no se refiere a eso, decí en supuestos por qué no lo usaste.")
