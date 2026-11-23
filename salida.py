"""El registro de cada respuesta (semana 5, decisión 73): sale por salida estructurada y se valida antes de guardarse.
Haiku escribe lo que es suyo (el texto, el número principal, los supuestos y las cuentas) con un esquema JSON fijo;
las consultas las pone el código, con lo que de verdad corrió, para que la traza no dependa de lo que el modelo diga.
Forma: la del enunciado, Respuesta = {pregunta, tipo (el de la puerta, decisión 78), texto, valor, unidad, supuestos, consultas: [{medida, filtros, sql}],
cuentas}. Las respuestas válidas se suman a registros/respuestas.jsonl (no se commitea)."""
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError

import registro
from controles import sin_respaldo, valores_de
from procesador_capa_semantica import sqls

RESPUESTAS = Path("registros/respuestas.jsonl")


class RespuestaFinal(BaseModel):
    """Lo que escribe Haiku al terminar. Las descripciones le llegan con el esquema."""
    model_config = ConfigDict(extra="forbid")
    texto: str = Field(description="La respuesta para quien preguntó, en español, como la escribirías normalmente")
    valor: Optional[float] = Field(description="El número principal de la respuesta, tal cual salió de la consulta "
                                               "(sin redondear), o null si la respuesta no tiene un número principal")
    unidad: Optional[str] = Field(description="La unidad de valor: ARS, %, pp, unidades… o null si valor es null")
    supuestos: List[str] = Field(description="Las lecturas que elegiste ante una ambigüedad y lo que se pidió y la "
                                             "base no tiene. Vacía si no hubo ninguno")
    cuentas: List[str] = Field(description="Las cuentas que hiciste con los resultados de las consultas, escritas "
                                           "completas («a − b = c»). Vacía si no hiciste ninguna")


def _esquema(modelo):
    """El JSON Schema del modelo, como lo pide la API: todo requerido y sin propiedades de más."""
    esquema = modelo.model_json_schema()
    esquema["required"] = list(esquema["properties"])
    esquema["additionalProperties"] = False
    for propiedad in esquema["properties"].values():
        propiedad.pop("title", None)
    esquema.pop("title", None)
    return esquema


FORMATO = {"format": {"type": "json_schema", "schema": _esquema(RespuestaFinal)}}


def leer(texto_del_modelo):
    """La respuesta final de Haiku validada contra el esquema, o (None, motivo)."""
    try:
        return RespuestaFinal.model_validate_json(texto_del_modelo), None
    except ValidationError as error:
        return None, f"la respuesta no cumple el esquema: {error.errors()[0]['msg']}"


def consulta_registrada(consulta):
    """Una consulta como la pide el enunciado: medida (o None si no es de la capa), filtros y su SQL."""
    argumentos = dict(consulta["argumentos"])
    medida = argumentos.pop("medida", None) if consulta["tool"] == "calcular" else None
    return {"tool": consulta["tool"], "medida": medida, "filtros": argumentos,
            "sql": [sql for _, sql, _ in sqls(consulta["resultado"])]}


class ConsultaRegistrada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool: str
    medida: Optional[str]
    filtros: dict
    sql: List[str]


class Registro(BaseModel):
    """El registro que se guarda. Se valida entero antes de escribirlo."""
    model_config = ConfigDict(extra="forbid")
    fecha: str
    corrida: str
    version: str
    pregunta: str
    tipo: Optional[str]
    texto: str
    valor: Optional[float]
    unidad: Optional[str]
    supuestos: List[str]
    consultas: List[ConsultaRegistrada]
    cuentas: List[str]
    salida: Optional[str] = None  # informe o diagnóstico: dónde quedó el PDF o el .md


def validar(final, pregunta, consultas, sin_respaldo_=(), tipo=None):
    """El registro armado y validado, o (None, [problemas]). Además del esquema: si hay un valor, tiene que salir de
    una consulta (redondeado o no), y una respuesta con número no puede no tener consultas. Si después de las
    correcciones quedaron números sin respaldo, tampoco se guarda: el registro diría algo que no se puede rastrear."""
    problemas = [f"números sin respaldo después de las correcciones: {', '.join(sin_respaldo_)}"] if sin_respaldo_ else []
    if not final.texto.strip():
        problemas.append("el texto está vacío")
    if final.valor is not None:
        if not consultas:
            problemas.append("tiene un valor pero ninguna consulta")
        elif sin_respaldo(f"{final.valor:.10f}".rstrip("0").rstrip(".").replace(".", ","),
                          valores_de([c["resultado"] for c in consultas])):
            problemas.append(f"el valor {final.valor} no sale de ninguna consulta")
        if not final.unidad:
            problemas.append("tiene un valor sin unidad")
    try:
        datos = Registro(fecha=f"{datetime.now():%Y-%m-%d %H:%M:%S}", corrida=registro.CORRIDA, version=registro.VERSION,
                         pregunta=pregunta, tipo=tipo, **final.model_dump(), consultas=[consulta_registrada(c) for c in consultas])
    except ValidationError as error:
        problemas.append(f"el registro no cumple el esquema: {error.errors()[0]['msg']}")
        datos = None
    return (None, problemas) if problemas else (datos, [])


def guardar(datos):
    RESPUESTAS.parent.mkdir(parents=True, exist_ok=True)
    with open(RESPUESTAS, "a") as archivo:
        archivo.write(datos.model_dump_json() + "\n")
