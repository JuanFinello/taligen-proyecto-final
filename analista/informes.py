"""Informes y diagnósticos con dos tipos de agente (decisión 42): el coordinador parte el pedido y redacta,
sin acceso a la base; el analista (el agente de las preguntas sueltas) resuelve cada pregunta."""
import asyncio
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import List, Literal, Optional

import anthropic
from pydantic import BaseModel, Field

import registro
import salida
from agente import CACHE, con_cache, glosario_del_servidor, resumen, responder
from controles import AVISO, MAX_SIN_CONTROL, numeros_del_texto, sin_respaldo, valores_de
from graficos import CALCULADOS, NOMBRES, color_de, es_destacado, graficar, que_dibujar
from explicar import DIMENSIONES, MEDIDAS, explicar, periodo
from informe_pdf import armar_pdf, escribir_sql, fecha
from procesador_capa_semantica import calcular, sqls, ver_modelo

MODELO = "claude-haiku-5-5"

# El coordinador no consulta: el menú de medidas va en su prompt en vez de pedirlo con ver_modelo (una vuelta menos).
# El glosario se suma al correr: lo sirve el servidor MCP como prompt (glosario_del_servidor)
INSTRUCCIONES_COORDINADOR = (
    "Sos el coordinador de los informes y diagnósticos de Almacenes del Sur. No consultás datos: repartís el trabajo "
    "entre analistas que sí consultan, y después redactás con lo que encuentran. Respondé en español.\n\n"
    "## Qué puede hacer un analista\n"
    "Cada consulta es una llamada a calcular: una medida del modelo, con filtros, y opcionalmente comparada con otro "
    "período (comparar_con; comparables=True para mismas sucursales) y agrupada por una dimensión (o por código y "
    "nombre, como proveedor y nombre_proveedor). Con eso ya vienen calculados la variación, la participación de cada "
    "grupo, su aporte a la suba o caída, el desvío contra presupuesto y los efectos precio y costo del margen. "
    "Nada más: el analista no suma, resta ni promedia resultados, ni filtra por umbrales. Cada consulta es de una sola "
    "medida; desvio_presupuesto_pct ya trae las ventas netas y el presupuesto, y efectos_margen ya trae el margen % "
    "de los dos períodos.\n"
    "Además de calcular, el analista puede listar las promociones de un período (qué producto, qué descuento, "
    "desde y hasta cuándo) y buscar un producto por su nombre.\n\n"
    "## Cómo planificar\n"
    "- Un diagnóstico lleva 1 o 2 preguntas; un informe, de 2 a 4. No más.\n"
    "- Cada pregunta se responde con 1 a 3 consultas, que escribís en `consultas`. Si necesita más, partila o dejá "
    "afuera lo menos importante para el pedido.\n"
    "- Cada pregunta se resuelve sola: los analistas trabajan por separado y no ven lo que encontraron los otros. "
    "Si un paso depende de otro (por ejemplo, encontrar qué cayó y después explicarlo), van juntos en la misma pregunta.\n"
    "- Cada pregunta lleva el período y los filtros del pedido escritos completos, porque el analista no ve el pedido.\n"
    "- El analista devuelve un hallazgo corto: 2 o 3 oraciones con los números clave. No pidas tablas ni listas: "
    "las tablas y los gráficos los arma el código con las consultas.\n"
    "- Solo pedí lo que el modelo de datos tiene (abajo). Si el pedido necesita algo que no está, no lo encargues: "
    "anotalo en supuestos.\n"
    "- Si el pedido se puede leer de dos maneras (período, calendario fiscal o comercial), elegí una y anotala en supuestos.\n"
    "- Pensá qué gráfico prueba cada razón (el código lo dibuja según la consulta): por categoría, región o proveedor, "
    "barras de cuánto se movió cada uno; por mes y comparada con el período anterior, dos líneas, que muestran si un "
    "cambio es sostenido o de unos meses; por sucursal, una columna por sucursal en orden, que muestra si el cambio es de todas o "
    "de unas pocas.\n\n"
    "## Modelo de datos (medidas y dimensiones que pueden consultar los analistas)\n"
    + json.dumps(ver_modelo(), ensure_ascii=False) + "\n\n")
LIMITES = {"diagnostico": (1, 2), "informe": (2, 4)}  # cuántas preguntas; cada una, de 1 a 3 consultas
MAX_CONSULTAS = 3


class Encargo(BaseModel):
    objetivo: str = Field(description="Para qué sirve esta pregunta en el informe, en una oración")
    pregunta: str = Field(description="La pregunta para el analista, con período y filtros completos")
    consultas: List[str] = Field(description="De 1 a 3 consultas a calcular, una por línea: medida, filtros, "
                                             "comparación y agrupación (por ejemplo: margen_pct de T2 AF2026 contra "
                                             "T2 AF2025, por categoría)")
    devolver: str = Field(description="El hallazgo que se espera, en 2 o 3 oraciones con los números clave; sin tablas")
    limites: str = Field(description="Qué no tiene que mirar, para no superponerse con otros encargos")


class Plan(BaseModel):
    tipo: Literal["informe", "diagnostico"]
    titulo: str
    supuestos: List[str] = Field(description="Lecturas elegidas ante ambigüedades y lo que el pedido pide y la base no "
                                             "tiene. Se leen en el informe: en castellano, sin nombres de tablas, "
                                             "campos ni medidas del modelo")
    encargos: List[Encargo]


def revisar(plan):
    """Lo que el código controla del plan (el prompt lo pide, pero el modelo puede no cumplirlo)."""
    problemas = []
    minimo, maximo = LIMITES[plan.tipo]
    if not minimo <= len(plan.encargos) <= maximo:
        problemas.append(f"{len(plan.encargos)} preguntas en un {plan.tipo} (van de {minimo} a {maximo})")
    for numero, encargo in enumerate(plan.encargos, 1):
        if not 1 <= len(encargo.consultas) <= MAX_CONSULTAS:
            problemas.append(f"la pregunta {numero} tiene {len(encargo.consultas)} consultas (van de 1 a {MAX_CONSULTAS})")
    # Los supuestos van al informe (decisión 104): un nombre interno («stock_semanal») no le dice nada a la gerencia
    internos = sorted({n for s in plan.supuestos for n in JERGA.findall(s)})
    if internos:
        problemas.append(f"los supuestos usan nombres internos ({', '.join(internos)}): escribilos en castellano")
    return problemas


JERGA = re.compile(r"\b[a-z]+(?:_[a-z0-9]+)+\b")  # stock_semanal, ventas_netas, anio_fiscal


async def planificar(pedido, claude, sistema, contexto="", tipo=None):
    """Paso 1 del coordinador: el plan con su estructura garantizada (salida estructurada). Si no cumple los límites,
    el código le devuelve los problemas una vez para que corrija, como en la redacción (decisión 75); antes el
    informe se cortaba y el programado lo reintentaba entero. Devuelve (plan, problemas que quedaron)."""
    # contexto: lo que pasa la puerta (decisión 78): el tipo que reconoció y, en una conversación, los turnos anteriores
    mensajes = [{"role": "user", "content": contexto + pedido}]
    for intento in (1, 2):
        inicio = time.monotonic()
        # Sin tools: el coordinador no consulta la base (PERMITIDAS["coordinador"] en hooks.py está vacía)
        respuesta = await claude.messages.parse(model=MODELO, max_tokens=16000, system=sistema, messages=mensajes,
                                                output_format=Plan)
        plan = respuesta.parsed_output
        if tipo and plan.tipo != tipo:
            # El tipo lo decide la puerta (decisión 78): si el coordinador eligió otro, se impone y los límites se
            # controlan con el de la puerta. Si no, la puerta quedaría de adorno
            print(f"⚠ el coordinador lo planificó como {plan.tipo}; la puerta dijo {tipo}, y queda {tipo}")
            plan.tipo = tipo
        problemas = revisar(plan)
        registro.anotar("coordinador", pedido, intento, respuesta, time.monotonic() - inicio,
                        errores=["plan"] if problemas else [])
        if not problemas:
            break
        mensajes += [{"role": "assistant", "content": respuesta.content[-1].text},
                     {"role": "user", "content": "El plan no cumple los límites. Corregilo y devolvé el plan completo:\n- "
                                                 + "\n- ".join(problemas)}]
    return plan, problemas


def encargo_para_analista(encargo):
    """El texto que recibe el analista: la pregunta completa, las consultas sugeridas y el formato de la respuesta."""
    return (f"{encargo.pregunta}\n\n"
            "Consultas sugeridas (podés ajustarlas si el modelo de datos lo pide):\n"
            + "\n".join(f"- {c}" for c in encargo.consultas) + "\n\n"
            f"Qué devolver: {encargo.devolver}\n"
            f"No mires: {encargo.limites}\n"
            "Respondé con un hallazgo de 2 o 3 oraciones con los números clave, sin tablas ni listas.")


async def investigar(plan):
    """Paso 2: cada pregunta va a un analista que arranca de cero (decisión 42); todos a la vez, porque no dependen
    entre sí (decisión 74). Las consultas se numeran C1, C2… en el orden de los encargos y, dentro de cada uno, en el
    que salieron: la numeración no depende de cuál terminó primero."""
    respuestas = await asyncio.gather(*(responder(encargo_para_analista(e)) for e in plan.encargos))
    hallazgos, numero = [], 0
    for encargo, respuesta in zip(plan.encargos, respuestas):
        consultas = []
        for consulta in respuesta["consultas"]:
            numero += 1
            consultas.append({"id": f"C{numero}", **consulta})
        hallazgos.append({"objetivo": encargo.objetivo, "pregunta": encargo.pregunta,
                          "hallazgo": respuesta["texto"], "consultas": consultas})
    return hallazgos


# Profundización en código (decisión 113). Después de los analistas nadie volvía a la base: si nadie pedía la medida
# por mes, el informe no podía decir desde cuándo (I3, 0 de 6); si nadie bajaba de la categoría al proveedor, no podía
# decir quién (I1, 1 de 6). En vez de un agente más, el código corre siempre dos consultas sobre lo que ya pidieron
# los analistas: la medida principal por mes y un nivel más abajo en el grupo que más bajó. Solo en informes: los
# diagnósticos quedan como estaban
SIGUIENTE_NIVEL = {"categoria": "nombre_proveedor", "region": "nombre_sucursal"}
TEMPORALES = {"mes", "mes_fiscal", "semana", "fecha", "trimestre_fiscal"}
CAMPO_DEL_CAMBIO = {"efectos_margen": "variacion_pp", "ventas_netas": "diferencia", "margen_pct": "variacion",
                    "tasa_quiebre_pct": "variacion"}
MESES_DEL_AF = ["mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre", "enero",
                "febrero", "marzo", "abril"]


def medidas_principales(pedido):
    """La medida de la que trata el informe: las ventas, salvo que el pedido nombre otra. Si se profundiza en otra
    (el margen en un informe regional), el informe se va de tema (I3 lo hacía 2 de 6 veces)."""
    texto = pedido.lower()
    if "margen" in texto or "rentab" in texto:
        return {"margen_pct", "efectos_margen"}
    if any(p in texto for p in ("faltante", "quiebre", "stock")):
        return {"tasa_quiebre_pct"}
    return {"ventas_netas"}


def de_calcular(consultas, medidas=None):
    """Las comparaciones de calcular() que salieron bien; con medidas, solo las de esas."""
    return [c for c in consultas if c["tool"] == "calcular" and c["argumentos"].get("comparar_con")
            and "error" not in c["resultado"] and (medidas is None or c["argumentos"].get("medida") in medidas)]


def por_mes(consultas, medidas):
    """La medida principal abierta por mes fiscal, con el período y la comparación de la primera consulta que la
    compara (si alguna usó comparables, también). None si no aplica o ya está."""
    candidatas = sorted(de_calcular(consultas, medidas), key=lambda c: bool(c["argumentos"].get("agrupar_por")))
    principal = candidatas[0]["argumentos"] if candidatas else None  # mejor una sin agrupar: su filtro es el del pedido
    if not principal:
        return None
    filtros = principal.get("filtros") or {}
    if "anio_fiscal" not in filtros or any(k in filtros for k in ("fecha", "semana", "mes_fiscal")) or isinstance(
            filtros.get("mes"), int):  # un año o un trimestre fiscal: por día o por semana no hay meses que abrir
        return None
    medida = "margen_pct" if principal["medida"] == "efectos_margen" else principal["medida"]
    comparables = any(c["argumentos"].get("comparables") for c in de_calcular(consultas, medidas))
    if any(c["argumentos"]["medida"] == medida and set(c["argumentos"].get("agrupar_por") or []) & {"mes", "mes_fiscal"}
           and bool(c["argumentos"].get("comparables")) == comparables for c in de_calcular(consultas)):
        return None  # un analista ya la pidió
    return {"medida": medida, "filtros": filtros, "comparar_con": principal["comparar_con"],
            "agrupar_por": ["mes_fiscal"], **({"comparables": True} if comparables else {})}


def un_nivel_mas(consultas, medidas):
    """El grupo que más bajó en una comparación por categoría o región, abierto un nivel más abajo (proveedores,
    sucursales). Devuelve (argumentos, nombre del grupo) o None."""
    for c in de_calcular(consultas, medidas):
        a = c["argumentos"]
        grupos = [d for d in a.get("agrupar_por") or [] if not d.startswith("nombre_")]
        campo = CAMPO_DEL_CAMBIO.get(a["medida"])
        if len(grupos) != 1 or grupos[0] not in SIGUIENTE_NIVEL or not campo:
            continue
        filas = [f for f in c["resultado"].get("filas") or [] if isinstance(f.get(campo), (int, float))]
        if not filas:
            continue
        peor = min(filas, key=lambda f: f[campo])
        if peor[campo] >= 0:
            continue
        dimension, grupo = grupos[0], peor[grupos[0]]
        siguiente = SIGUIENTE_NIVEL[dimension]
        if any((x["argumentos"].get("filtros") or {}).get(dimension) == grupo
               and siguiente in (x["argumentos"].get("agrupar_por") or []) for x in de_calcular(consultas)):
            return None  # un analista ya bajó a ese nivel
        return ({"medida": a["medida"], "filtros": {**(a.get("filtros") or {}), dimension: grupo},
                 "comparar_con": a["comparar_con"], "agrupar_por": [siguiente],
                 **({"comparables": True} if a.get("comparables") else {})}, grupo)
    return None


def desde_cuando(resultado, campo="variacion"):
    """«desde agosto, debajo del año anterior todos los meses»: el último tramo de 3 meses o más con el mismo signo
    hasta el final del período. None si no hay un tramo así."""
    filas = sorted((f for f in resultado.get("filas") or [] if isinstance(f.get(campo), (int, float))),
                   key=lambda f: f["mes_fiscal"])
    if len(filas) < 3:
        return None
    signo = filas[-1][campo] < 0
    inicio = len(filas) - 1
    while inicio > 0 and (filas[inicio - 1][campo] < 0) == signo:
        inicio -= 1
    if len(filas) - inicio < 3 or inicio == 0:
        return None  # todo el período igual (no hay un «desde») o menos de 3 meses
    return (f"desde {MESES_DEL_AF[filas[inicio]['mes_fiscal'] - 1]}, "
            f"{'debajo' if signo else 'arriba'} del período anterior todos los meses")


def correr(argumentos):
    """calcular() como lo devuelve el servidor MCP a los analistas: en JSON (las fechas, como texto). Sin esto, una
    fecha en el resultado (abiertas_hasta, con comparables) rompía el paso de redactar."""
    return json.loads(json.dumps(calcular(**argumentos), ensure_ascii=False, default=str))


def profundizar(consultas, pedido):
    """Las dos consultas del código, ya corridas, y lo que muestran en una oración cada una (sin cuentas propias:
    nombres y signos que trae el resultado)."""
    nuevas, notas = [], []
    medidas = medidas_principales(pedido)
    argumentos = por_mes(consultas, medidas)
    if argumentos:
        resultado = correr(argumentos)
        if "error" not in resultado:
            nuevas.append({"tool": "calcular", "argumentos": argumentos, "resultado": resultado})
            tramo = desde_cuando(resultado)
            notas.append("La medida principal por mes" + (f": {tramo}." if tramo else "."))
    hallado = un_nivel_mas(consultas, medidas)
    if hallado:
        argumentos, grupo = hallado
        resultado = correr(argumentos)
        campo = CAMPO_DEL_CAMBIO[argumentos["medida"]]
        filas = [f for f in resultado.get("filas") or [] if isinstance(f.get(campo), (int, float))]
        if filas:
            nuevas.append({"tool": "calcular", "argumentos": argumentos, "resultado": resultado})
            peor = min(filas, key=lambda f: f[campo])
            nombre = str(peor.get(argumentos["agrupar_por"][0]) or "").removesuffix(" S.A.")
            notas.append(f"Dentro de {grupo}, el que más bajó: {nombre}.")
    return nuevas, " ".join(notas)


class Indicador(BaseModel):
    nombre: str = Field(description="Nombre corto, por ejemplo «Margen %» o «Ventas netas»")
    consulta: str = Field(description="El id de la consulta de donde sale (C1, C2…)")
    dato: str = Field(description="El campo del total de esa consulta que se muestra grande, el nivel: valor, "
                                  "actual, o uno de efectos_margen (margen_pct_actual…). En una comparación, actual: "
                                  "el cambio va en variacion")
    variacion: Optional[str] = Field(description="El campo de la misma consulta con su cambio (variacion, diferencia, "
                                                 "variacion_pp), o null si no hay comparación")
    contra: Optional[str] = Field(description="Contra qué es el cambio, corto y sin cifras calculadas: «vs T2 AF2025», "
                                              "«vs presupuesto». Null si no hay comparación")


class Grafico(BaseModel):
    consulta: str = Field(description="El id de una consulta agrupada que prueba el punto: el código la grafica")
    destacar: List[str] = Field(description="Exactamente los grupos que nombra el punto, por código o nombre "
                                            "(«Almacén», «PR01»): van en color y el resto en gris. Si el punto dice "
                                            "«cinco proveedores», son esos cinco")


class Punto(BaseModel):
    texto: str = Field(description="Una oración con lo que hay que saber, como afirmación: «Sur concentra la suba "
                                   "del quiebre» (no «Quiebre por región»). Como máximo 2 cifras, cada una con su "
                                   "consulta [Cn], y ninguna que ya muestre un indicador. Si lleva gráfico, es su "
                                   "titular: el gráfico no lleva otro texto")
    grafico: Optional[Grafico] = Field(description="El gráfico que prueba el punto, o null si el punto no lo necesita")


class Redaccion(BaseModel):
    titulo: str = Field(description="El mensaje del informe en una oración de hasta 22 palabras: la conclusión, "
                                    "no el tema. Ejemplo: «El margen cayó por la suba de costo de un proveedor»")
    bajada: str = Field(description="Una oración debajo del título que le da escala al mensaje, con como máximo 2 "
                                    "cifras, cada una con su consulta [Cn] y contra qué se compara: «el margen bajó "
                                    "0,2 pp, a 26,8 %, y en pesos creció 3,9 %». No repite el título ni un punto")
    indicadores: List[Indicador] = Field(description="1 o 2: el número del mensaje y, si existe, el mismo dato en "
                                                     "la otra escala. No se muestran en la página: fechan el informe "
                                                     "y van al anexo")
    puntos: List[Punto] = Field(description="2 o 3 puntos que sostienen el mensaje, en orden: cada uno responde lo "
                                            "que deja abierto el anterior (¿dónde? → ¿quién?), y ninguno repite a "
                                            "otro, al título ni a un indicador. 1 o 2 llevan su gráfico")


# El lector, descripto una vez y compartido por el coordinador y el editor (decisión 105; Anthropic recomienda
# describir la audiencia)
LECTOR = ("un gerente con experiencia, que sabe de números (% y pp se usan como en cualquier empresa) y no es "
          "analista: lee la página en un minuto y tiene que decidir")

# Los ejemplos salen de informes de esta base corregidos con el usuario (Data/ejemplos_informes/, decisiones 106 a
# 108), de pedidos que no se miden. Van completos los dos que no tocan ningún hallazgo medido (una semana sin
# novedades y la marca propia); del tercero (el margen del año) van solo las lecciones, sin nombres ni cifras: su
# causa es la respuesta de I1, P13 y P16. Reemplazan a los tres ejemplos inventados de la decisión 105
EJEMPLOS_REDACCION = (
    "<ejemplos>\nDos informes de esta empresa, corregidos (sus números son de otros pedidos: no los uses), y las "
    "lecciones de un tercero.\n"
    "<ejemplo>\nPedido: informe semanal, qué requiere la atención de la gerencia.\n"
    "Mal: «No hay alarma general: la caída es puntual en Espuma Clara y Valle Hermoso» (en cualquier semana alguna "
    "sucursal y algún producto caen: el que más cayó no es un culpable).\n"
    "Bien:\nTítulo: «Semana sin novedades: nada requiere la atención de la gerencia»\n"
    "Bajada: «Las ventas netas subieron 2,2 % contra la misma semana de 2024 y los faltantes bajaron a 1,0 %.»\n"
    "1. «Los faltantes están entre 0,9 % y 1,1 % en las cuatro regiones, y el proveedor con más faltantes tiene "
    "2,1 %.»\n"
    "2. «Las ventas por sucursal fueron de −16,6 % a +20,0 %, sin ninguna aislada del resto; la mayor baja en pesos, "
    "Valle Hermoso ($ 0,48 M), había subido 3,3 % la semana anterior.» (gráfico: una columna por sucursal)\n"
    "3. «Tampoco hay un producto para mirar. La mayor baja en pesos es de un producto grande que varió 9,1 %; las "
    "mayores en porcentaje, de productos que venden menos de $ 0,5 M por semana.»\n"
    "Por qué: si no pasa nada, se dice, y se prueba: el rango de todas, la cifra en pesos, la semana anterior.\n"
    "</ejemplo>\n"
    "<ejemplo>\nPedido: informe de la marca propia, ¿conviene empujarla?\n"
    "Mal: «La marca propia deja más margen, pero pesa poco y crece menos que la cadena» (un margen % más alto no "
    "alcanza para contestar: hay que mirarlo también en pesos por unidad).\n"
    "Bien:\nTítulo: «La marca propia tiene mejor margen %, pero cada unidad deja menos pesos: conviene si trae "
    "ventas nuevas, no si reemplaza a otras marcas»\n"
    "Bajada: «Es el 2,2 % de las ventas del AF2026.»\n"
    "1. «Su margen % es mayor que el de las otras marcas en las seis categorías: en Almacén, 34,0 % contra 24,3 %.» "
    "(gráfico: las dos, lado a lado, por categoría)\n"
    "2. «Cada unidad deja menos pesos en todas las subcategorías donde compite salvo dos, porque es más barata.» "
    "(gráfico: margen por unidad, las dos lado a lado, por subcategoría)\n"
    "3. «El caso más claro son las dos colas de 2,25 L: a precio normal, la de marca propia dejó $ 511 por unidad y "
    "la otra, $ 629.»\n"
    "Por qué: el pedido preguntaba si conviene, y el título lo contesta con los dos lados (solo por eso dice "
    "«conviene»); cada razón prueba una mitad del título.\n</ejemplo>\n"
    "Lecciones de un informe de margen:\n"
    "- No cuentes meses («cayó en 8 de 12»): decí desde cuándo cambió y qué cambió en ese momento.\n"
    "- Partí el período donde cambian los hechos, no por la mitad: un promedio puede esconder cuándo empezó.\n"
    "- El cambio de margen de una categoría, en pp, no dice cuánto movió el total: depende de cuánto vende.\n"
    "- Si sube el costo de una categoría, llegá al proveedor: quién, desde cuándo, cuánto y si se trasladó al "
    "precio.\n"
    "- La razón habla en la unidad de su gráfico. Y «compensó» lleva cantidad: «compensó la mitad».\n"
    "</ejemplos>\n")

INSTRUCCIONES_REDACCION = (
    "Ahora redactá el informe con los hallazgos de los analistas y sus consultas (abajo). Es una sola página que se "
    "lee de arriba abajo: el mensaje como título, una bajada que le da escala y 2 o 3 razones, con sus pruebas. Sin "
    "recomendaciones: qué hacer lo decide la gerencia.\n"
    "- Primero decidí el mensaje: la única conclusión que el lector tiene que llevarse. Todo lo demás está para "
    "sostenerlo; lo que no lo sostiene, va afuera aunque sea cierto.\n"
    "- Cada idea aparece una sola vez en la página. El título resume los puntos; cada punto dice algo que no dicen "
    "el título, los otros puntos ni los indicadores; y si un punto lleva gráfico, el punto es su titular.\n"
    "- Los títulos y los puntos son afirmaciones, no temas: «Almacén explica la caída», no «Margen por categoría».\n"
    "- Cada cifra que escribas tiene que estar en el resultado de una consulta, tal cual o redondeada, y lleva su "
    "consulta entre corchetes: «cayó 0,24 pp [C2]». No hagas cuentas propias; si un hallazgo trae una cifra que no "
    "está en ninguna consulta, no la uses.\n"
    "- Los indicadores y los gráficos no llevan números tuyos: elegís la consulta y el campo, y el código pone los "
    "valores y dibuja. En un gráfico, resaltá exactamente los grupos que nombra su punto.\n"
    "- Escribí para la gerencia, que decide con esta página en un minuto: corto, sin nombres de campos ni de medidas "
    "del modelo.\n"
    f"- El lector es {LECTOR}. Escribí los % y los pp como en cualquier empresa («el margen bajó 0,2 pp, a "
    "26,8 %»), sin traducirlos a «centavos por peso». Oraciones cortas: ninguna de más de 30 palabras.\n"
    "- Contá la historia entera. Si dos medidas del mismo tema se mueven al revés (el margen % baja y el margen en "
    "pesos sube; las ventas totales suben y las comparables bajan), el título dice las dos cosas y su porqué, y "
    "los puntos explican cada una: «Se ganó más porque se vendió más, pero cada venta dejó menos por el costo de "
    "Almacén». Con una sola, el lector entiende la mitad.\n"
    "- Si entre los hallazgos está la profundización del código (la medida por mes y un nivel más abajo), usala "
    "para decir desde cuándo y quién, si sostiene el mensaje.\n"
    "- Dale escala a cada cambio, para que se entienda si es grave o menor: contra lo normal (el glosario dice cuánto, "
    "si lo dice), contra el total o en pesos. Si el cambio es chico, decilo así: no lo presentes como alarma.\n"
    + EJEMPLOS_REDACCION + "\n")


class Diagnostico(BaseModel):
    respuesta: str = Field(description="La respuesta a la pregunta en una oración: la conclusión, con como máximo "
                                       "2 cifras, cada una con su consulta [Cn]")
    evidencia: List[str] = Field(description="2 o 3 oraciones que la prueban, en orden (cada una responde lo que "
                                             "deja abierta la anterior); como máximo 2 cifras cada una, con su [Cn]")
    siguiente_paso: str = Field(description="Qué conviene hacer o mirar después, sin cifras")


INSTRUCCIONES_DIAGNOSTICO = (
    "Ahora respondé la pregunta con los hallazgos de los analistas y sus consultas (abajo). Es un diagnóstico: "
    "la respuesta primero, en una oración, y después solo la evidencia que la prueba.\n"
    "- Cada cifra que escribas tiene que estar en el resultado de una consulta, tal cual o redondeada, y lleva su "
    "consulta entre corchetes: «cayó 1,20 pp [C2]». No hagas cuentas propias; si un hallazgo trae una cifra que no "
    "está en ninguna consulta, no la uses.\n"
    "- Si los datos no alcanzan para afirmar la causa, decilo y separá lo que muestran de lo que sería una "
    "interpretación.\n"
    "- Escribí para alguien de negocio: corto, sin nombres de campos ni de medidas del modelo.\n\n")


class Grave(str):
    """Un problema que impide entregar: un número sin respaldo, o una cita, un campo o un gráfico que no existen.
    Los demás son de forma (largo, cantidad de cifras): se piden corregir, pero si siguen se entrega igual."""


def revisar_diagnostico(diagnostico, consultas):
    """Lo que controla el código antes de dar la respuesta: forma, cifras por oración, citas y respaldo."""
    problemas = []
    if not 2 <= len(diagnostico.evidencia) <= 3:
        problemas.append(f"tiene {len(diagnostico.evidencia)} oraciones de evidencia: van 2 o 3")
    for texto in [diagnostico.respuesta, *diagnostico.evidencia]:
        if cifras(texto) > 2:
            problemas.append(f"«{texto[:60]}…» tiene {cifras(texto)} cifras: van como máximo 2 por oración")
    textos = [diagnostico.respuesta, *diagnostico.evidencia, diagnostico.siguiente_paso]
    return problemas + revisar_citas(textos, consultas)


def revisar_citas(textos, consultas):
    """Las consultas citadas existen y cada número del texto está en alguna consulta (decisión 49)."""
    ids = {c["id"] for c in consultas}
    problemas = []
    citadas_ = set(re.findall(r"\[(C\d+)\]", " ".join(textos)))
    if citadas_ - ids:
        problemas.append(Grave(f"el texto cita consultas que no existen: {', '.join(sorted(citadas_ - ids))}"))
    sueltos = sin_respaldo(" ".join(re.sub(r"\[C\d+\]", "", t) for t in textos),
                           valores_de([c["resultado"] for c in consultas]))
    if sueltos:
        problemas.append(Grave(f"{AVISO}: {', '.join(sueltos)}"))
    return problemas


def para_redactar(consulta):
    """Lo que el coordinador lee de una consulta: qué se pidió y sus números, sin el SQL."""
    def sin_sql(o):
        if isinstance(o, dict):
            return {k: sin_sql(v) for k, v in o.items() if k not in ("sql", "parametros", "medida", "unidad", "filtros")}
        if isinstance(o, list):
            return [sin_sql(x) for x in o]
        return round(o, 4) if isinstance(o, float) else o
    return {"id": consulta["id"], "pidio": consulta["argumentos"], "resultado": sin_sql(consulta["resultado"])}


def dato_de(resultado, campo):
    """(valor, unidad, con_signo) de un campo del total de una consulta, o None si no está.
    En una consulta agrupada el total viene aparte: un número (medida aditiva) o un dict (desvío, efectos)."""
    total = resultado.get("total")
    fuente = {**resultado, **total} if isinstance(total, dict) else resultado
    if "." in campo:  # «total.valor», «sin_presupuesto_sospechoso.valor»: Haiku a veces nombra el campo con su
        parte, resto = campo.split(".", 1)  # camino, y el informe no salía (decisión 84). El total ya está en fuente
        sub = fuente.get(parte) if parte != "total" else fuente
        if not isinstance(sub, dict):
            return None
        return dato_de({**{k: v for k, v in resultado.items() if k != "total"}, **sub}, resto)
    valor = fuente.get(campo)
    if valor is None and campo in ("valor", "total") and isinstance(total, (int, float)):
        valor = total
    if isinstance(valor, dict):  # actual o anterior de una comparación
        valor = valor.get("valor")
    if not isinstance(valor, (int, float)) or isinstance(valor, bool):
        return None
    unidad = resultado.get("unidad") or (resultado.get("actual") or {}).get("unidad")
    if (campo in ("ventas_netas", "presupuesto") or campo.startswith(("precio_", "costo_unitario_"))
            or (campo == "diferencia" and resultado.get("medida") == "desvio_presupuesto_pct")):
        unidad = "ARS"  # los montos dentro de un desvío o de efectos_margen (cuya unidad es % o pp)
    elif campo.startswith("margen_pct_"):
        unidad = "%"
    elif campo == "variacion":
        unidad = resultado.get("unidad_variacion", "%")
    elif campo.endswith("_pp"):
        unidad = "pp"
    elif campo.endswith("_pct"):
        unidad = "%"
    con_signo = (campo in ("variacion", "diferencia") or campo.endswith(("_pp", "_pct"))
                 or (campo == "valor" and resultado.get("medida") == "desvio_presupuesto_pct"))
    return valor, unidad, con_signo


def cifras(texto):
    """Cuántas cifras tiene un texto (sin contar los números de consulta [Cn] ni los enteros chicos)."""
    return sum(1 for valor, _, escrito in numeros_del_texto(re.sub(r"\[C\d+\]", "", texto))
               if not (valor.is_integer() and valor <= MAX_SIN_CONTROL and "," not in escrito))


MAX_PALABRAS = 30  # eran 25; los ejemplos aprobados por el usuario necesitaban más (decisión 108)
NUMEROS_ESCRITOS = {"dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9}
GRUPOS = r"(?:regiones|sucursales|categor[ií]as|subcategor[ií]as|proveedores|productos|marcas|meses|formatos)"


def cuantos_nombra(texto):
    """Cuántos grupos dice el texto que hay («cinco proveedores», «3 categorías»), o None si no dice un número."""
    hallado = re.search(rf"\b(\d|{'|'.join(NUMEROS_ESCRITOS)})\s+{GRUPOS}\b", texto.lower())
    if not hallado:
        return None
    return int(hallado.group(1)) if hallado.group(1).isdigit() else NUMEROS_ESCRITOS[hallado.group(1)]


def que_muestra(resultado):
    """Lo que dibuja un gráfico de esa consulta, en palabras: «el cambio del margen %, en pp»."""
    _, campo, unidad = que_dibujar(resultado)
    medida = MEDIDAS.get(resultado.get("medida"), {}).get("nombre", resultado.get("medida", "")).lower()
    if resultado.get("medida") == "efectos_margen":  # por mes van los dos márgenes, en líneas (decisión 106)
        return "el margen bruto %" if campo == "margen_pct_actual" else "el cambio del margen %, en pp"
    if resultado.get("medida") == "desvio_presupuesto_pct":
        return "el desvío contra presupuesto, en %"
    if campo in ("diferencia", "variacion"):
        return f"el cambio de {medida}, en {'pesos' if unidad == 'ARS' else unidad}"
    return medida


def etiquetas_del_grafico(resultado):
    """Los números como los muestra el gráfico, para que el coordinador los copie igual: «Perfumería −68,0 %, …»."""
    from graficos import CALCULADOS as calculados, etiqueta, formato
    _, campo, unidad = que_dibujar(resultado)
    filas = [f for f in resultado.get("filas") or [] if isinstance(f.get(campo), (int, float))]
    dimensiones = [d for d in filas[0] if d not in calculados] if filas else []
    return ", ".join(f"{etiqueta(f, dimensiones)} {formato(f[campo], unidad, True)}" for f in filas[:6])


def se_ve_en_el_grafico(texto, resultado):
    """¿Algún número del texto está entre los que muestra el gráfico (el valor de cada barra o el nivel a su lado)?
    Un texto sin números no se controla."""
    filas = resultado.get("filas") or []
    if not filas:
        return True
    _, campo, _ = que_dibujar(resultado)
    visibles = [abs(f[c]) for f in filas for c in (campo, "actual", "margen_pct_actual", "anterior", "margen_pct_anterior")
                if isinstance(f.get(c), (int, float)) and not isinstance(f.get(c), bool)]
    numeros = [(n, tol) for n, tol, escrito in numeros_del_texto(re.sub(r"\[C\d+\]", "", texto))
               if not (n.is_integer() and (n <= MAX_SIN_CONTROL or 1900 <= n <= 2100) and "," not in escrito)]
    if not numeros:
        return True
    return any(abs(n - v) <= tol for n, tol in numeros for v in visibles)


def repite_indicador(texto, indicadores, por_id):
    """Los indicadores cuyo número grande o cuyo cambio aparece en el texto, tal cual o redondeado como se muestra."""
    repetidos = []
    numeros = numeros_del_texto(re.sub(r"\[C\d+\]", "", texto))
    for ind in indicadores:
        resultado = por_id.get(ind.consulta, {}).get("resultado", {})
        for campo in filter(None, [ind.dato, ind.variacion]):
            dato = dato_de(resultado, campo)
            if not dato:
                continue
            valor = abs(dato[0])
            # como se ve en el indicador: los montos en millones con un decimal, los % y pp con un decimal
            vistos = {round(valor / 1e6, 1) * 1e6, round(valor, 1)} if valor >= 1e6 else {round(valor, 1)}
            if any(abs(n - v) <= tol + 1e-9 for n, tol, escrito in numeros
                   if not (n.is_integer() and n <= MAX_SIN_CONTROL and "," not in escrito) for v in vistos):
                repetidos.append(f"«{ind.nombre}»")
                break
    return repetidos


def textos_de(redaccion):
    return [redaccion.titulo, redaccion.bajada, *(p.texto for p in redaccion.puntos)]


def revisar_redaccion(redaccion, consultas):
    """Lo que controla el código antes de armar el PDF: la forma de la página, consultas y campos que existen,
    grupos a resaltar que están en su gráfico y cada número con respaldo."""
    por_id = {c["id"]: c for c in consultas}
    problemas = []
    if len(redaccion.titulo.split()) > 25:  # se piden hasta 22; el control deja un margen para no corregir por una palabra
        problemas.append(f"el título tiene {len(redaccion.titulo.split())} palabras: tiene que ser el mensaje en una "
                         f"oración de hasta 22")
    if not 1 <= len(redaccion.indicadores) <= 2:
        problemas.append(f"tiene {len(redaccion.indicadores)} indicadores: van 1 o 2 (el número del mensaje y, si "
                         f"existe, el mismo dato en la otra escala)")
    con_grafico = [p for p in redaccion.puntos if p.grafico]
    repetidas = [c for c, n in Counter(p.grafico.consulta for p in con_grafico).items() if n > 1]
    if repetidas:
        problemas.append(f"dos puntos grafican la misma consulta ({', '.join(repetidas)}): el mismo gráfico saldría dos "
                         f"veces. Dejá el gráfico en el punto que más lo necesita")
    if not 1 <= len(con_grafico) <= 2:
        problemas.append(f"tiene {len(con_grafico)} puntos con gráfico: van 1 o 2")
    for ind in redaccion.indicadores:
        if ind.consulta not in por_id:
            problemas.append(Grave(f"el indicador «{ind.nombre}» cita {ind.consulta}, que no existe"))
            continue
        resultado = por_id[ind.consulta]["resultado"]
        if ind.dato == "diferencia" and dato_de(resultado, "actual"):
            # El número grande es el nivel y debajo va el cambio (IBCS, decisión 71): «$ 186,7 M, −0,2 %», no
            # «−$ 438.508». En el desvío contra presupuesto no hay «actual»: ahí el desvío es el nivel
            problemas.append(f"el indicador «{ind.nombre}» muestra el cambio como número principal: poné actual en "
                             f"dato, el cambio en variacion, y un nombre que diga qué se mide (no «crecimiento»)")
        for campo in filter(None, [ind.dato, ind.variacion]):
            if dato_de(resultado, campo) is None:
                problemas.append(Grave(f"el indicador «{ind.nombre}» pide «{campo}» de {ind.consulta}, y ese total no lo tiene"))
    for punto in con_grafico:
        filas = por_id.get(punto.grafico.consulta, {}).get("resultado", {}).get("filas")
        if not filas:
            problemas.append(Grave(f"el gráfico de «{punto.texto[:50]}…» usa {punto.grafico.consulta}, que no es una "
                                   f"consulta agrupada"))
            continue
        dimensiones = [d for d in filas[0] if d not in CALCULADOS]
        for grupo in punto.grafico.destacar:
            if not any(es_destacado(f, dimensiones, [grupo]) for f in filas):
                problemas.append(f"el gráfico de «{punto.texto[:50]}…» resalta «{grupo}», que no está en {punto.grafico.consulta}")
        # El punto y su gráfico hablan de lo mismo (decisión 105): si el punto da números, alguno se ve en el gráfico
        if not se_ve_en_el_grafico(punto.texto, por_id[punto.grafico.consulta]["resultado"]):
            problemas.append(f"el punto «{punto.texto[:50]}…» da números que no se ven en su gráfico: el gráfico muestra "
                             f"{que_muestra(por_id[punto.grafico.consulta]['resultado'])} y sus etiquetas dicen "
                             f"{etiquetas_del_grafico(por_id[punto.grafico.consulta]['resultado'])}. Usá esos números tal "
                             f"como se ven (redondeados igual), o elegí la consulta que muestra lo que dice el punto")
        # Lo que dice el titular y lo que se ve en color, lo mismo (decisión 104): «cinco proveedores» son cinco
        nombrados = cuantos_nombra(punto.texto)
        if nombrados and nombrados != len(punto.grafico.destacar):
            problemas.append(f"el punto «{punto.texto[:50]}…» nombra {nombrados} grupos y su gráfico resalta "
                             f"{len(punto.grafico.destacar)}: resaltá exactamente los que nombra")
    if not 2 <= len(redaccion.puntos) <= 3:
        problemas.append(f"tiene {len(redaccion.puntos)} puntos: van 2 o 3")
    if cifras(redaccion.bajada) > 2:
        problemas.append(f"la bajada tiene {cifras(redaccion.bajada)} cifras: van como máximo 2")
    # Oraciones cortas (decisión 105; las guías de lenguaje claro piden 15 a 20 palabras de promedio)
    for texto in [redaccion.bajada, *(p.texto for p in redaccion.puntos)]:
        for oracion in re.split(r"(?<=[.;:])\s+", re.sub(r"\s?\[C\d+\]", "", texto)):
            if len(oracion.split()) > MAX_PALABRAS:
                problemas.append(f"«{oracion[:60]}…» tiene {len(oracion.split())} palabras: partila (van hasta {MAX_PALABRAS})")
    for numero, punto in enumerate(redaccion.puntos, 1):
        if cifras(punto.texto) > 2:
            problemas.append(f"el punto {numero} tiene {cifras(punto.texto)} cifras: van como máximo 2")
    # (Hasta la decisión 105 se controlaba que un punto no repitiera un indicador; desde que los indicadores no se
    # muestran, no hay qué repetir, y el control daba falsas alarmas por coincidencias: «Lácteos bajó 0,2 pp» contra
    # el «−0,2 pp» de la cadena. Lo que se repite entre la bajada y los puntos lo marca el editor)
    return problemas + revisar_citas(textos_de(redaccion), consultas)


class Arreglo(BaseModel):
    problema: str = Field(description="Qué no se entiende o suena raro, y dónde (el título, la bajada, el punto 2…)")
    propuesta: str = Field(description="La frase corregida, lista para usar, con las mismas cifras y sus [Cn]: no "
                                       "agregues números que no estén en la página")


class Edicion(BaseModel):
    arreglos: List[Arreglo] = Field(description="Como máximo 4, los más importantes. Vacía si la página se entiende")


INSTRUCCIONES_EDITOR = (
    f"Sos el editor de los informes de Almacenes del Sur. Leés la página como la va a leer {LECTOR}, y marcás solo lo "
    "que hace que no se entienda o se lea raro. Para cada cosa, proponé la frase corregida, lista para usar: una "
    "crítica específica sirve más que una general.\n"
    "1. El título: ¿dice qué pasó y por qué? Si dos números del mismo tema se mueven al revés, ¿dice los dos?\n"
    "2. Cada número: ¿se entiende qué es y contra qué se compara? El gerente sabe de números: % y pp se usan como en "
    "cualquier empresa, no los marques ni pidas traducirlos («centavos por peso» es peor). Sí marcá los nombres "
    "internos del sistema (campos, tablas).\n"
    "3. ¿Algo se dice dos veces (el título, la bajada, los puntos)?\n"
    "4. ¿Alguna oración es larga (más de 30 palabras), técnica o suena rara? ¿Se lee de corrido, como lo diría una "
    "persona?\n"
    "5. ¿Cada razón sostiene el título? Si una dice que no se sabe si tiene que ver, sobra.\n"
    "No corrijas el estilo por gusto ni pidas datos que no están: si la página se entiende, devolvé la lista vacía. "
    "Las referencias [Cn] son citas de las consultas: dejalas.")


def pagina_en_texto(redaccion):
    """La página como la lee el gerente, para el editor: sin gráficos (su titular es el punto)."""
    lineas = [f"Título: {redaccion.titulo}", f"Bajada: {redaccion.bajada}", "Por qué:"]
    lineas += [f"{i}. {p.texto}" for i, p in enumerate(redaccion.puntos, 1)]
    return "\n".join(lineas)


async def editar(pedido, redaccion, claude):
    """El editor (decisión 105, el patrón evaluador-optimizador del módulo 4): lee la página como un gerente y dice
    qué no se entiende. Lo que encuentra vuelve al coordinador como una corrección más, una sola vez."""
    inicio = time.monotonic()
    respuesta = await claude.messages.parse(model=MODELO, max_tokens=4000, system=INSTRUCCIONES_EDITOR,
                                            messages=[{"role": "user", "content": pagina_en_texto(redaccion)}],
                                            output_format=Edicion)
    edicion = respuesta.parsed_output
    arreglos = (edicion.arreglos if edicion else [])[:4]
    registro.anotar("editor", f"editar: {pedido}", 1, respuesta, time.monotonic() - inicio,
                    errores=["edicion"] if arreglos else [])
    return [f"{a.problema} Propuesta: «{a.propuesta}»" for a in arreglos]


async def redactar(pedido, plan, hallazgos, claude, sistema):
    """Paso 3 del coordinador: el informe (o la respuesta del diagnóstico), con la estructura garantizada. Si el
    código encuentra problemas, se los devuelve una vez para que corrija."""
    consultas = [c for h in hallazgos for c in h["consultas"]]
    material = {"pedido": pedido, "titulo_del_plan": plan.titulo, "supuestos": plan.supuestos,
                "hallazgos": [{"objetivo": h["objetivo"], "hallazgo": h["hallazgo"],
                               "consultas": [c["id"] for c in h["consultas"]]} for h in hallazgos],
                "consultas": [para_redactar(c) for c in consultas]}
    if plan.tipo == "diagnostico":
        instrucciones, formato_salida, revisar_salida = INSTRUCCIONES_DIAGNOSTICO, Diagnostico, revisar_diagnostico
    else:
        instrucciones, formato_salida, revisar_salida = INSTRUCCIONES_REDACCION, Redaccion, revisar_redaccion
    # Marca de caché explícita en el material: si hay que corregir, la segunda redacción lo lee del caché (parse no
    # acepta la marca automática de la llamada)
    mensajes = [{"role": "user", "content": [{"type": "text", "text": instrucciones + json.dumps(material, ensure_ascii=False),
                                              "cache_control": CACHE}]}]
    revisiones = []  # lo que encontró el control en cada intento, para la traza
    for intento in (1, 2):
        inicio = time.monotonic()
        respuesta = await claude.messages.parse(model=MODELO, max_tokens=16000, system=sistema,
                                                messages=mensajes, output_format=formato_salida)
        redaccion = respuesta.parsed_output
        problemas = revisar_salida(redaccion, consultas)
        revisiones.append([("grave: " if isinstance(p, Grave) else "forma: ") + p for p in problemas])
        registro.anotar("coordinador", f"redactar: {pedido}", intento, respuesta, time.monotonic() - inicio,
                        errores=["redaccion"] if problemas else [])
        # El editor lee la primera redacción como un gerente (decisión 105): lo que marque va junto con lo que encontró
        # el código, en la misma corrección. Una llamada más y ninguna vuelta más
        del_editor = []
        if intento == 1 and plan.tipo == "informe":
            del_editor = await editar(pedido, redaccion, claude)
            revisiones[-1] += [f"editor: {p}" for p in del_editor]
        if intento == 2 or (not problemas and not del_editor):
            break
        correccion = ("Corregí estos problemas y devolvé el informe completo:\n- " + "\n- ".join(problemas)) if problemas else ""
        if del_editor:
            correccion += ("\n\nAdemás, un" if problemas else "Un") + (" editor leyó la página como un gerente y encontró "
                           "esto. Corregilo y devolvé el informe completo:\n- ") + "\n- ".join(del_editor)
        mensajes += [{"role": "assistant", "content": respuesta.content[-1].text},
                     {"role": "user", "content": correccion}]
    return redaccion, problemas, consultas, revisiones


def complemento_de(indicadores):
    """El mismo dato que el principal en la otra escala (el margen % y el margen bruto en pesos), si está entre los
    indicadores: se nombran igual salvo el «%» y «en pesos»."""
    base = lambda n: re.sub(r"\s*(%|en pesos)$", "", n.strip().lower())
    principal = indicadores[0]
    return next((i for i in indicadores[1:] if base(i["nombre"]) == base(principal["nombre"])
                 and i["unidad"] != principal["unidad"]), None)


def series_de(consulta):
    """El nombre de cada línea de un gráfico de dos períodos: («AF2026», «AF2025»); sin nombre corto, actual y anterior."""
    from sugerir import corto
    a = consulta["argumentos"]
    filtros = a.get("filtros") or {}
    actual, anterior = corto(filtros), corto({**filtros, **(a.get("comparar_con") or {})})
    if not (actual and anterior):
        return ("actual", "anterior")
    return tuple(n.removeprefix("el ") for n in (actual, anterior))


def rotulo_grafico(consulta, dibujo):
    """Qué muestra un gráfico, en palabras y sin repetir la conclusión (eso lo dice su razón): «El cambio del margen %
    por proveedor, en pp: el T2 del AF2026 contra el T2 del AF2025»."""
    from sugerir import corto
    a = consulta["argumentos"]
    agrupar = a.get("agrupar_por") or []  # el nombre solo cuenta como su código; con el código, sobra
    por = [DIMENSIONES.get(d.removeprefix("nombre_"), d) for d in agrupar
           if not (d.startswith("nombre_") and d.removeprefix("nombre_") in agrupar)]
    filtros = a.get("filtros") or {}
    cuando = corto(filtros) or periodo(filtros)
    que, unidad = (que_muestra(consulta["resultado"]).split(", en ") + [""])[:2]
    que = que.removeprefix("el ")
    que = que[0].upper() + que[1:]
    # de qué grupo, si la consulta está filtrada por uno: «Margen bruto % de Almacén por mes fiscal»
    proveedor = filtros.get("nombre_proveedor") or NOMBRES.get(filtros.get("proveedor"))
    grupos = [str(filtros[d]) for d in ("categoria", "subcategoria", "marca") if isinstance(filtros.get(d), str)]
    if isinstance(proveedor, str):
        grupos.append(proveedor.removesuffix(" S.A."))
    if isinstance(filtros.get("es_marca_propia"), bool):
        grupos.append("marca propia" if filtros["es_marca_propia"] else "otras marcas")
    if grupos:
        que += " de " + " y ".join(grupos)
    if isinstance(filtros.get("region"), str):  # «… de Lácteos en el Norte», no «de Lácteos y Norte»
        que += f" en el {filtros['region']}"
    if a.get("comparables"):  # si no, las líneas de una región parecen de toda la región
        que += " (sucursales comparables)"
    if a.get("comparar_con"):
        contra = corto({**filtros, **a["comparar_con"]}) or periodo({**filtros, **a["comparar_con"]})
        if contra.startswith("del "):  # «contra del 01-08-2024 al…» → «contra el período del 01-08-2024 al…»
            contra = "el período " + contra
        elif contra.startswith("de "):  # «contra de diciembre a abril del AF2025» → «contra los mismos meses del AF2025»
            contra = "los mismos meses del " + contra.split(" del ")[-1]
        return f"{que} por {' y '.join(por)}{', en ' + unidad if unidad else ''}: {cuando} contra {contra}"
    return f"{que} por {' y '.join(por)}: {cuando}"


def descripcion(consulta):
    """Qué calcula una consulta, para el anexo: en castellano (explicar.py, decisión 83), no los filtros en código."""
    return " ".join(l.rstrip(".") + "." for l in explicar(consulta).splitlines()).replace("Qué se midió: ", "")


def citadas(redaccion):
    """Las consultas que el informe usa: las de los indicadores, los gráficos y las [Cn] del texto."""
    return ({i.consulta for i in redaccion.indicadores} | {p.grafico.consulta for p in redaccion.puntos if p.grafico}
            | set(re.findall(r"\[(C\d+)\]", " ".join(textos_de(redaccion)))))


def periodo_del_informe(consultas, principal=None):
    """El período del informe: el de la consulta del primer indicador (el actual, en una comparación). Si no lo trae,
    el que más se repite. No alcanza con el que más se repite: en el mensual ganaba el acumulado del año (decisión 67)."""
    def periodo(c):
        r = c["resultado"]
        p = r.get("periodo") or (r.get("actual") or {}).get("periodo") if isinstance(r, dict) else None
        return (p["desde"], p["hasta"]) if p and p.get("desde") and p.get("hasta") else None
    for c in consultas:
        if c["id"] == principal and periodo(c):
            desde, hasta = periodo(c)
            return {"desde": desde, "hasta": hasta}
    vistos = Counter(periodo(c) for c in consultas if periodo(c))
    if not vistos:
        raise ValueError("Ninguna consulta trae su período: no se puede fechar el informe")
    desde, hasta = vistos.most_common(1)[0][0]
    return {"desde": desde, "hasta": hasta}


def armar(pedido, plan, redaccion, consultas, carpeta, nombre="Informe"):
    """Paso 4, todo código: valores y colores de los indicadores, gráficos con el grupo resaltado y PDF."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    por_id = {c["id"]: c for c in consultas}
    indicadores = []
    for ind in redaccion.indicadores:
        resultado = por_id[ind.consulta]["resultado"]
        valor, unidad, con_signo = dato_de(resultado, ind.dato)
        indicador = {"nombre": ind.nombre, "valor": valor, "unidad": unidad, "con_signo": con_signo,
                     "consulta": ind.consulta, "contra": ind.contra}
        if ind.variacion:
            variacion, unidad_variacion, _ = dato_de(resultado, ind.variacion)
            anterior = dato_de(resultado, "anterior") if ind.dato == "actual" else None
            indicador["anterior"] = anterior[0] if anterior else None
            medida = resultado.get("medida") or por_id[ind.consulta]["argumentos"].get("medida")
            if ind.variacion.startswith("variacion_costo"):  # dentro de efectos_margen: una suba de costo es mala
                medida = "costo_unitario"
            indicador.update(variacion=variacion, unidad_variacion=unidad_variacion, color=color_de(medida, variacion))
        indicadores.append(indicador)
    puntos, numero, ya_graficadas = [], 0, {}
    for punto in redaccion.puntos:
        armado = {"texto": punto.texto}
        if punto.grafico and punto.grafico.consulta in ya_graficadas:  # el mismo gráfico no se dibuja dos veces
            armado["mismo_grafico"] = ya_graficadas[punto.grafico.consulta]
        elif punto.grafico:
            numero += 1
            ya_graficadas[punto.grafico.consulta] = numero
            consulta = por_id[punto.grafico.consulta]
            dibujo = graficar(consulta["resultado"], carpeta / f"grafico_{numero}.png", "",
                              destacar=punto.grafico.destacar, series=series_de(consulta),
                              filtros=consulta["argumentos"].get("filtros"))
            nota = (f"se muestran {dibujo['mostrados']} de {dibujo['mostrados'] + dibujo['omitidos']}"
                    if dibujo["omitidos"] else dibujo.get("nota", ""))
            armado["grafico"] = {"ruta": dibujo["ruta"], "consulta": punto.grafico.consulta, "nota": nota,
                                 "rotulo": rotulo_grafico(por_id[punto.grafico.consulta], dibujo)}
        puntos.append(armado)
    periodo = periodo_del_informe(consultas, redaccion.indicadores[0].consulta if redaccion.indicadores else None)
    # El pedido va al anexo, con los supuestos: en la página del mensaje ocupaba cuatro líneas (decisión 67)
    # Arriba, chico, qué informe es y de cuándo (IBCS separa la identificación del mensaje, decisión 70)
    informe = {"titulo": redaccion.titulo, "bajada": redaccion.bajada, "puntos": puntos,
               "principal": indicadores[0],
               "complemento": indicadores[1] if len(indicadores) == 2 else complemento_de(indicadores),
               "identificacion": f"{nombre} · del {fecha(periodo['desde'])} al {fecha(periodo['hasta'])}", "pedido": pedido,
               "indicadores": indicadores, "supuestos": plan.supuestos,
               "consultas": [{"id": c["id"], "descripcion": descripcion(c), "resultado": c["resultado"]}
                             for c in consultas if c["tool"] in ("calcular", "consultar_sql") and c["id"] in citadas(redaccion)]}
    return armar_pdf(informe, carpeta / "informe.pdf")


def armar_diagnostico(pedido, plan, diagnostico, consultas, carpeta):
    """El diagnóstico es texto, no PDF: la respuesta, la evidencia, el siguiente paso y las consultas citadas."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    textos = [diagnostico.respuesta, *diagnostico.evidencia, diagnostico.siguiente_paso]
    usadas = set(re.findall(r"\[(C\d+)\]", " ".join(textos)))
    del_anexo = [{"id": c["id"], "descripcion": descripcion(c), "resultado": c["resultado"]}
                 for c in consultas if c["tool"] == "calcular" and c["id"] in usadas]
    escribir_sql(del_anexo, carpeta / "consultas.sql")
    lineas = [f"# {pedido}", "", f"**{diagnostico.respuesta}**", "", *[f"- {e}" for e in diagnostico.evidencia], "",
              f"**Siguiente paso:** {diagnostico.siguiente_paso}", "", "## Supuestos", "",
              *[f"- {s}" for s in plan.supuestos], "", "## Consultas citadas (SQL en consultas.sql)", "",
              *[f"- [{c['id']}] {c['descripcion']}" for c in del_anexo]]
    ruta = carpeta / "diagnostico.md"
    ruta.write_text("\n".join(lineas) + "\n")
    return ruta


class NoSeEntrega(Exception):
    """El plan o la redacción siguen con problemas después de corregirlos: no hay informe."""


async def atender(pedido, carpeta, nombre="Informe", contexto="", tipo=None):
    """Un pedido de informe o diagnóstico, de punta a punta. Devuelve {texto, consultas, salida}; si no se puede
    entregar, NoSeEntrega. Lo llaman este script y la puerta (puerta.py, decisión 78)."""
    async with anthropic.AsyncAnthropic() as claude:
        sistema = con_cache(INSTRUCCIONES_COORDINADOR + await glosario_del_servidor())  # planificar y redactar lo comparten
        plan, problemas = await planificar(pedido, claude, sistema, contexto, tipo)
        print(json.dumps(plan.model_dump(), ensure_ascii=False, indent=2))
        for problema in problemas:
            print("⚠ " + problema)
        if problemas:
            raise NoSeEntrega("El plan sigue sin cumplir los límites después de corregirlo: no se manda a los analistas")
        hallazgos = await investigar(plan)
        if plan.tipo == "informe":  # decisión 113: desde cuándo y quién, sin depender de que alguien lo pida
            todas = [c for h in hallazgos for c in h["consultas"]]
            nuevas, notas = profundizar(todas, pedido)
            if nuevas:
                hallazgos.append({"objetivo": "Profundización del código: la medida principal por mes y un nivel más "
                                              "abajo en el grupo que más bajó", "pregunta": "",
                                  "hallazgo": notas, "consultas": [{"id": f"C{len(todas) + i}", **c}
                                                                   for i, c in enumerate(nuevas, 1)]})
        for h in hallazgos:
            print(f"\n## {h['objetivo']}\n{h['hallazgo']}\nConsultas: "
                  + (", ".join(c["id"] + " " + c["argumentos"].get("medida", "sql") for c in h["consultas"]) or "ninguna"))
        redaccion, problemas, consultas, revisiones = await redactar(pedido, plan, hallazgos, claude, sistema)
    print("\n" + json.dumps(redaccion.model_dump(), ensure_ascii=False, indent=2))
    for problema in problemas:
        print(("✗ " if isinstance(problema, Grave) else "⚠ ") + problema)
    if any(isinstance(p, Grave) for p in problemas):
        raise NoSeEntrega("La redacción sigue con problemas graves después de corregirla: no se entrega")
    if problemas:
        print("Se entrega igual: lo que queda es de forma.")
    # Todo lo que produjo el modelo, para rearmar el PDF sin volver a llamarlo (y para la traza)
    Path(carpeta).mkdir(parents=True, exist_ok=True)
    Path(carpeta, "informe.json").write_text(json.dumps(
        {"pedido": pedido, "nombre": nombre, "corrida": registro.CORRIDA, "version": registro.VERSION, "plan": plan.model_dump(),
         "hallazgos": [{**h, "consultas": [c["id"] for c in h["consultas"]]} for h in hallazgos],
         "redaccion": redaccion.model_dump(), "revisiones": revisiones, "consultas": consultas},
        ensure_ascii=False, indent=1, default=str))
    if plan.tipo == "diagnostico":
        ruta = armar_diagnostico(pedido, plan, redaccion, consultas, carpeta)
        texto = ruta.read_text().split("## Supuestos")[0].split("\n", 1)[1].strip() + f"\n\nDiagnóstico: {ruta}"
        print("\n" + texto + "\n")
    else:
        ruta = armar(pedido, plan, redaccion, consultas, carpeta, nombre)
        texto = "\n".join([redaccion.titulo, *(f"- {p.texto}" for p in redaccion.puntos), "", f"PDF: {ruta}"])
        print(f"\nPDF: {ruta}\n")
    print(f"Traza: {escribir_traza(carpeta)}\n")
    # Como cada respuesta del agente (decisión 73): el registro con la forma del enunciado, más dónde quedó la salida.
    # Valor y cuentas van vacíos: los números del texto ya los controló revisar_citas, y las cuentas las hace el código
    final = salida.RespuestaFinal(texto=texto, valor=None, unidad=None, supuestos=plan.supuestos, cuentas=[])
    datos, problemas_registro = salida.validar(final, pedido, consultas, tipo=plan.tipo)
    if datos:
        datos.salida = str(ruta)
        salida.guardar(datos)
    else:
        print("⚠ registro no guardado: " + "; ".join(problemas_registro))
    registro.resumen_corrida(registro.leer(registro.LLAMADAS), registro.CORRIDA)
    return {"texto": texto, "consultas": consultas, "salida": str(ruta), "registro": datos,
            "problemas_registro": problemas_registro}


async def main(pedido, carpeta, nombre="Informe"):
    try:
        await atender(pedido, carpeta, nombre)
    except NoSeEntrega as motivo:
        sys.exit(str(motivo))


def escribir_traza(carpeta):
    """La traza de un informe o diagnóstico (semana 3): el pedido, el plan, qué hizo cada analista (vueltas, errores,
    correcciones, consultas con su SQL), qué encontró el control en la redacción, el resultado y el costo de cada paso.
    Sale de informe.json y del registro de esa corrida."""
    g = json.loads(Path(carpeta, "informe.json").read_text())
    plan, por_id = g["plan"], {c["id"]: c for c in g["consultas"]}
    llamadas = [l for l in registro.leer(registro.LLAMADAS) if l["corrida"] == g["corrida"]]
    usd = lambda ls: sum(l["costo_usd"] for l in ls)
    segundos = lambda ls: sum(l["segundos_modelo"] + l["segundos_tools"] for l in ls)
    fila = lambda paso, ls: f"| {paso} | {len(ls)} | {sum(l['tokens_entrada'] for l in ls):,} | " \
                            f"{sum(l['tokens_salida'] for l in ls):,} | {usd(ls):.4f} | {segundos(ls):.1f} |"
    archivo_salida = "diagnostico.md" if plan["tipo"] == "diagnostico" else "informe.pdf"
    lineas = [f"# Traza: {g['pedido']}", "",
              f"Corrida `{g['corrida']}` · versión del diseño `{g['version']}` · `{MODELO}`. Para volver a correrla:", "",
              "```", f'.venv/bin/python analista/informes.py {json.dumps(g["pedido"], ensure_ascii=False)} {carpeta}', "```", "",
              f"Resultado: `{Path(carpeta, archivo_salida)}` · SQL de las consultas citadas: `{Path(carpeta, 'consultas.sql')}`", "",
              "## 1. Coordinador: el plan", "", f"Tipo: **{plan['tipo']}** · {plan['titulo']}", "", "Supuestos:",
              *[f"- {s}" for s in plan["supuestos"]], ""]
    for numero, encargo in enumerate(plan["encargos"], 1):
        lineas += [f"**Pregunta {numero}.** {encargo['pregunta']}", "", f"- Para qué: {encargo['objetivo']}",
                   *[f"- Consulta sugerida: {c}" for c in encargo["consultas"]], f"- No mirar: {encargo['limites']}", ""]
    lineas += ["## 2. Analistas: una llamada por pregunta, cada una desde cero", ""]
    for numero, (encargo, h) in enumerate(zip(plan["encargos"], g["hallazgos"]), 1):
        suyas = [l for l in llamadas if l["agente"] == "analista" and l["pregunta"].startswith(encargo["pregunta"])]
        lineas += [f"### Analista {numero}", "", f"{len(suyas)} vueltas del modelo · US$ {usd(suyas):.4f} · "
                   f"{segundos(suyas):.1f} s", ""]
        for l in suyas:
            detalle = ", ".join(l["tools"]) or "respuesta final"
            lineas.append(f"- Vuelta {l['vuelta']}: {detalle}")
            lineas += [f"  - ✗ error de tool, que Haiku recibe para corregir: {e}" for e in l["errores"]
                       if e != "numeros_sin_respaldo"]
            if l.get("sin_respaldo"):
                lineas.append(f"  - ✗ el control devolvió la respuesta: números sin respaldo {', '.join(l['sin_respaldo'])}")
        lineas += ["", "**Hallazgo:**", "", *[f"> {r}" for r in h["hallazgo"].splitlines()], "", "**Consultas:**", ""]
        for id_ in h["consultas"]:
            c = por_id[id_]
            lineas.append(f"- **[{id_}] `{c['tool']}`** `{json.dumps(c['argumentos'], ensure_ascii=False)}`")
            if resumen(c["resultado"]):
                lineas.append(f"  - Resultado: {resumen(c['resultado'])}")
            for parte, sql, parametros in sqls(c["resultado"]):
                lineas += ["", "  ```sql", f"  -- {parte}parámetros {json.dumps(parametros, ensure_ascii=False, default=str)}",
                           *[f"  {s}" for s in sql.splitlines()], "  ```"]
        lineas.append("")
    redaccion = [l for l in llamadas if l["agente"] == "coordinador" and l["pregunta"].startswith("redactar:")]
    lineas += ["## 3. Coordinador: la redacción", "",
               f"{len(redaccion)} intento(s) · US$ {usd(redaccion):.4f} · {segundos(redaccion):.1f} s", ""]
    for intento, encontrado in enumerate(g.get("revisiones", []), 1):
        lineas.append(f"- Intento {intento}: " + ("el control no encontró problemas" if not encontrado else
                                                  "el control encontró: " + "; ".join(encontrado)))
    lineas += ["", "Lo que escribió (el código pone los valores de los indicadores y dibuja los gráficos):", "",
               "```json", json.dumps(g["redaccion"], ensure_ascii=False, indent=1), "```", "",
               "## 4. Costo y tiempo", "", "Los segundos son la suma de las llamadas: los analistas trabajan en paralelo "
               "(decisión 74), así que el tiempo de reloj es menor.", "",
               "| Paso | Llamadas | Tokens de entrada | Tokens de salida | US$ | Segundos (suma) |",
               "|---|---|---|---|---|---|",
               fila("Plan", [l for l in llamadas if l["agente"] == "coordinador" and l not in redaccion]),
               fila("Analistas", [l for l in llamadas if l["agente"] == "analista"]),
               fila("Redacción", redaccion), fila("**Total**", llamadas), ""]
    ruta = Path(carpeta, "traza.md")
    ruta.write_text("\n".join(lineas) + "\n")
    return ruta


def rearmar(carpeta):
    """Vuelve a armar gráficos y PDF desde informe.json, sin llamar al modelo (para ajustar el diseño)."""
    guardado = json.loads(Path(carpeta, "informe.json").read_text())
    plan = Plan(**guardado["plan"])
    if plan.tipo == "diagnostico":
        return armar_diagnostico(guardado["pedido"], plan, Diagnostico(**guardado["redaccion"]), guardado["consultas"], carpeta)
    redaccion = guardado["redaccion"]
    if "puntos" not in redaccion:  # los informes de antes de la decisión 70 tenían un párrafo en lugar de puntos
        redaccion["puntos"] = [redaccion.pop("bajada")]
    redaccion.setdefault("bajada", "")  # antes de la decisión 105 la línea del número la armaba el código
    if "pruebas" in redaccion:  # antes de la decisión 104: puntos sueltos y, aparte, pruebas con su texto
        redaccion["puntos"] = ([{"texto": p, "grafico": None} for p in redaccion["puntos"]]
                               + [{"texto": f"{p['titulo']}. {p['texto']}", "grafico": {"consulta": p["consulta"],
                                   "destacar": p["destacar"]}} for p in redaccion.pop("pruebas")])
    return armar(guardado["pedido"], plan, Redaccion(**redaccion), guardado["consultas"], carpeta,
                 guardado.get("nombre", "Informe"))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--traza"]:
        sys.exit(print(escribir_traza(sys.argv[2])))
    if sys.argv[1:2] == ["--rearmar"]:
        sys.exit(print(rearmar(sys.argv[2])))
    if len(sys.argv) < 2:
        sys.exit('Uso: .venv/bin/python analista/informes.py "pedido" [carpeta de salida]  ·  --rearmar carpeta')
    argumentos = sys.argv[1:]
    nombre = "Informe"
    if "--nombre" in argumentos:  # «Informe semanal»…: lo pasa informe_programado.py
        i = argumentos.index("--nombre")
        nombre = argumentos[i + 1]
        del argumentos[i:i + 2]
    asyncio.run(main(argumentos[0], argumentos[1] if len(argumentos) > 1 else f"salidas/{registro.CORRIDA}", nombre))
