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
from agente import CACHE, con_cache, glosario_del_servidor, resumen, responder
from controles import AVISO, MAX_SIN_CONTROL, numeros_del_texto, sin_respaldo, valores_de
from graficos import CALCULADOS, color_de, es_destacado, graficar
from informe_pdf import armar_pdf, escribir_sql, fecha
from procesador_capa_semantica import sqls, ver_modelo

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
    "- Si el pedido se puede leer de dos maneras (período, calendario fiscal o comercial), elegí una y anotala en supuestos.\n\n"
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
    supuestos: List[str] = Field(description="Lecturas elegidas ante ambigüedades y lo que el pedido pide y la base no tiene")
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
    return problemas


async def planificar(pedido, claude, sistema):
    """Paso 1 del coordinador: el plan con su estructura garantizada (salida estructurada)."""
    inicio = time.monotonic()
    # Sin tools: el coordinador no consulta la base (PERMITIDAS["coordinador"] en hooks.py está vacía)
    respuesta = await claude.messages.parse(model=MODELO, max_tokens=16000, system=sistema,
                                            messages=[{"role": "user", "content": pedido}], output_format=Plan)
    registro.anotar("coordinador", pedido, 1, respuesta, time.monotonic() - inicio)
    return respuesta.parsed_output, respuesta.usage


def encargo_para_analista(encargo):
    """El texto que recibe el analista: la pregunta completa, las consultas sugeridas y el formato de la respuesta."""
    return (f"{encargo.pregunta}\n\n"
            "Consultas sugeridas (podés ajustarlas si el modelo de datos lo pide):\n"
            + "\n".join(f"- {c}" for c in encargo.consultas) + "\n\n"
            f"Qué devolver: {encargo.devolver}\n"
            f"No mires: {encargo.limites}\n"
            "Respondé con un hallazgo de 2 o 3 oraciones con los números clave, sin tablas ni listas.")


async def investigar(plan):
    """Paso 2: cada pregunta va a un analista que arranca de cero (decisión 42); uno tras otro.
    Las consultas se numeran C1, C2… en el orden en que salieron, para que el informe las cite."""
    hallazgos, numero = [], 0
    for encargo in plan.encargos:
        respuesta = await responder(encargo_para_analista(encargo))
        consultas = []
        for consulta in respuesta["consultas"]:
            numero += 1
            consultas.append({"id": f"C{numero}", **consulta})
        hallazgos.append({"objetivo": encargo.objetivo, "pregunta": encargo.pregunta,
                          "hallazgo": respuesta["texto"], "consultas": consultas})
    return hallazgos


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


class Prueba(BaseModel):
    titulo: str = Field(description="La conclusión que prueba el gráfico, como afirmación: «Almacén es la única "
                                    "categoría con una caída fuerte», no «Margen por categoría»")
    consulta: str = Field(description="El id de una consulta agrupada: el código la grafica")
    destacar: List[str] = Field(description="1 o 2 grupos a resaltar, por código o nombre («Almacén», «PR01»): "
                                            "van en color y el resto en gris")
    texto: str = Field(description="Una o dos oraciones que lean el gráfico: como máximo 2 cifras, cada una con su "
                                   "consulta [Cn]. El gráfico ya muestra los valores: no los repitas todos")


class Redaccion(BaseModel):
    titulo: str = Field(description="El mensaje del informe en una oración de hasta 15 palabras: la conclusión, "
                                    "no el tema. Ejemplo: «El margen cayó por la suba de costo de un proveedor»")
    puntos: List[str] = Field(description="2 o 3 puntos con lo principal, en orden de importancia: qué pasó y por "
                                          "qué. Cada uno, una oración corta con como máximo 2 cifras, cada una con su "
                                          "consulta [Cn]. Se leen sueltos: no repitas el título")
    acciones: List[str] = Field(description="1 o 2 decisiones o encargos para la gerencia que se desprenden del "
                                            "mensaje y de lo que muestra la página, sin cifras")
    indicadores: List[Indicador] = Field(description="Exactamente 3: los números que sostienen el mensaje")
    pruebas: List[Prueba] = Field(description="1 o 2 gráficos que prueban el mensaje, en orden: cada uno responde "
                                              "la pregunta que deja el anterior (¿qué categoría? → ¿qué proveedor?)")


INSTRUCCIONES_REDACCION = (
    "Ahora redactá el informe con los hallazgos de los analistas y sus consultas (abajo). Es una sola página que se "
    "lee de arriba abajo: el mensaje como título, 2 o 3 puntos con lo principal, qué hacer, tres indicadores y una o "
    "dos pruebas.\n"
    "- Primero decidí el mensaje: la única conclusión que el lector tiene que llevarse. Todo lo demás está para "
    "sostenerlo; lo que no lo sostiene, va afuera aunque sea cierto.\n"
    "- Los títulos son afirmaciones, no temas: «Almacén explica la caída», no «Margen por categoría».\n"
    "- Cada cifra que escribas tiene que estar en el resultado de una consulta, tal cual o redondeada, y lleva su "
    "consulta entre corchetes: «cayó 0,24 pp [C2]». No hagas cuentas propias; si un hallazgo trae una cifra que no "
    "está en ninguna consulta, no la uses.\n"
    "- Los indicadores y los gráficos no llevan números tuyos: elegís la consulta y el campo, y el código pone los "
    "valores y dibuja.\n"
    "- Escribí para la gerencia, que decide con esta página en un minuto: corto, sin nombres de campos ni de medidas "
    "del modelo.\n"
    "- Dale escala a cada cambio, para que se entienda si es grave o menor: contra lo normal (el glosario dice cuánto, "
    "si lo dice), contra el total o en pesos. Si el cambio es chico, decilo así: no lo presentes como alarma.\n"
    "- Cada acción se apoya en algo que está en la página (un punto, un indicador o una prueba). Si no hay en la "
    "página nada que la respalde, no la pongas.\n\n")


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


def textos_de(redaccion):
    return [redaccion.titulo, *redaccion.puntos, *redaccion.acciones, *(f"{p.titulo} {p.texto}" for p in redaccion.pruebas)]


def revisar_redaccion(redaccion, consultas):
    """Lo que controla el código antes de armar el PDF: la forma de la página, consultas y campos que existen,
    grupos a resaltar que están en su gráfico y cada número con respaldo."""
    por_id = {c["id"]: c for c in consultas}
    problemas = []
    if len(redaccion.titulo.split()) > 18:
        problemas.append("el título tiene más de 15 palabras: tiene que ser el mensaje en una oración corta")
    if len(redaccion.indicadores) != 3:
        problemas.append(f"tiene {len(redaccion.indicadores)} indicadores: van exactamente 3")
    if not 1 <= len(redaccion.pruebas) <= 2:
        problemas.append(f"tiene {len(redaccion.pruebas)} pruebas: van 1 o 2")
    if not 1 <= len(redaccion.acciones) <= 2:
        problemas.append(f"tiene {len(redaccion.acciones)} acciones: van 1 o 2")
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
    for prueba in redaccion.pruebas:
        filas = por_id.get(prueba.consulta, {}).get("resultado", {}).get("filas")
        if not filas:
            problemas.append(Grave(f"la prueba «{prueba.titulo}» grafica {prueba.consulta}, que no es una consulta agrupada"))
            continue
        dimensiones = [d for d in filas[0] if d not in CALCULADOS]
        for grupo in prueba.destacar:
            if not any(es_destacado(f, dimensiones, [grupo]) for f in filas):
                problemas.append(f"la prueba «{prueba.titulo}» resalta «{grupo}», que no está en {prueba.consulta}")
    if not 2 <= len(redaccion.puntos) <= 3:
        problemas.append(f"tiene {len(redaccion.puntos)} puntos: van 2 o 3")
    for numero, punto in enumerate(redaccion.puntos, 1):
        if cifras(punto) > 2:
            problemas.append(f"el punto {numero} tiene {cifras(punto)} cifras: van como máximo 2")
    for prueba in redaccion.pruebas:
        if cifras(prueba.texto) > 2:
            problemas.append(f"el texto de «{prueba.titulo}» tiene {cifras(prueba.texto)} cifras: van como máximo 2")
    return problemas + revisar_citas(textos_de(redaccion), consultas)


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
        if not problemas:
            break
        mensajes += [{"role": "assistant", "content": respuesta.content[-1].text},
                     {"role": "user", "content": "Corregí estos problemas y devolvé el informe completo:\n- "
                                                 + "\n- ".join(problemas)}]
    return redaccion, problemas, consultas, revisiones


def descripcion(argumentos):
    """Qué calcula una consulta, en una línea, para el anexo."""
    partes = [argumentos.get("medida", "SQL"), json.dumps(argumentos.get("filtros", {}), ensure_ascii=False)]
    if argumentos.get("comparar_con"):
        partes.append("contra " + json.dumps(argumentos["comparar_con"], ensure_ascii=False)
                      + (" (comparables)" if argumentos.get("comparables") else ""))
    if argumentos.get("agrupar_por"):
        partes.append("por " + ", ".join(argumentos["agrupar_por"]))
    return " · ".join(partes)


def citadas(redaccion):
    """Las consultas que el informe usa: las de los indicadores, los gráficos y las [Cn] del texto."""
    return ({i.consulta for i in redaccion.indicadores} | {p.consulta for p in redaccion.pruebas}
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
            medida = resultado.get("medida") or por_id[ind.consulta]["argumentos"].get("medida")
            if ind.variacion.startswith("variacion_costo"):  # dentro de efectos_margen: una suba de costo es mala
                medida = "costo_unitario"
            indicador.update(variacion=variacion, unidad_variacion=unidad_variacion, color=color_de(medida, variacion))
        indicadores.append(indicador)
    pruebas = []
    for numero, prueba in enumerate(redaccion.pruebas, 1):
        dibujo = graficar(por_id[prueba.consulta]["resultado"], carpeta / f"grafico_{numero}.png", "",
                          destacar=prueba.destacar)
        nota = f"se muestran {dibujo['mostrados']} de {dibujo['mostrados'] + dibujo['omitidos']}" if dibujo["omitidos"] else ""
        pruebas.append({"titulo": prueba.titulo, "grafico": dibujo["ruta"], "texto": prueba.texto,
                        "consulta": prueba.consulta, "nota": nota})
    periodo = periodo_del_informe(consultas, redaccion.indicadores[0].consulta if redaccion.indicadores else None)
    # El pedido va al anexo, con los supuestos: en la página del mensaje ocupaba cuatro líneas (decisión 67)
    # Arriba, chico, qué informe es y de cuándo (IBCS separa la identificación del mensaje, decisión 70)
    informe = {"titulo": redaccion.titulo, "puntos": redaccion.puntos, "acciones": redaccion.acciones,
               "identificacion": f"{nombre} · del {fecha(periodo['desde'])} al {fecha(periodo['hasta'])}", "pedido": pedido,
               "indicadores": indicadores, "pruebas": pruebas, "supuestos": plan.supuestos,
               "consultas": [{"id": c["id"], "descripcion": descripcion(c["argumentos"]), "resultado": c["resultado"]}
                             for c in consultas if c["tool"] == "calcular" and c["id"] in citadas(redaccion)]}
    return armar_pdf(informe, carpeta / "informe.pdf")


def armar_diagnostico(pedido, plan, diagnostico, consultas, carpeta):
    """El diagnóstico es texto, no PDF: la respuesta, la evidencia, el siguiente paso y las consultas citadas."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    textos = [diagnostico.respuesta, *diagnostico.evidencia, diagnostico.siguiente_paso]
    usadas = set(re.findall(r"\[(C\d+)\]", " ".join(textos)))
    del_anexo = [{"id": c["id"], "descripcion": descripcion(c["argumentos"]), "resultado": c["resultado"]}
                 for c in consultas if c["tool"] == "calcular" and c["id"] in usadas]
    escribir_sql(del_anexo, carpeta / "consultas.sql")
    lineas = [f"# {pedido}", "", f"**{diagnostico.respuesta}**", "", *[f"- {e}" for e in diagnostico.evidencia], "",
              f"**Siguiente paso:** {diagnostico.siguiente_paso}", "", "## Supuestos", "",
              *[f"- {s}" for s in plan.supuestos], "", "## Consultas citadas (SQL en consultas.sql)", "",
              *[f"- [{c['id']}] {c['descripcion']}" for c in del_anexo]]
    ruta = carpeta / "diagnostico.md"
    ruta.write_text("\n".join(lineas) + "\n")
    return ruta


async def main(pedido, carpeta, nombre="Informe"):
    async with anthropic.AsyncAnthropic() as claude:
        sistema = con_cache(INSTRUCCIONES_COORDINADOR + await glosario_del_servidor())  # planificar y redactar lo comparten
        plan, _ = await planificar(pedido, claude, sistema)
        print(json.dumps(plan.model_dump(), ensure_ascii=False, indent=2))
        problemas = revisar(plan)
        for problema in problemas:
            print("⚠ " + problema)
        if problemas:
            sys.exit("El plan no cumple los límites: no se manda a los analistas")
        hallazgos = await investigar(plan)
        for h in hallazgos:
            print(f"\n## {h['objetivo']}\n{h['hallazgo']}\nConsultas: "
                  + (", ".join(c["id"] + " " + c["argumentos"].get("medida", "sql") for c in h["consultas"]) or "ninguna"))
        redaccion, problemas, consultas, revisiones = await redactar(pedido, plan, hallazgos, claude, sistema)
    print("\n" + json.dumps(redaccion.model_dump(), ensure_ascii=False, indent=2))
    for problema in problemas:
        print(("✗ " if isinstance(problema, Grave) else "⚠ ") + problema)
    if any(isinstance(p, Grave) for p in problemas):
        sys.exit("La redacción sigue con problemas graves después de corregirla: no se entrega")
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
        print("\n" + ruta.read_text().split("## Supuestos")[0] + f"Diagnóstico: {ruta}\n")
    else:
        print(f"\nPDF: {armar(pedido, plan, redaccion, consultas, carpeta, nombre)}\n")
    print(f"Traza: {escribir_traza(carpeta)}\n")
    registro.resumen_corrida(registro.leer(registro.LLAMADAS), registro.CORRIDA)


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
    salida = "diagnostico.md" if plan["tipo"] == "diagnostico" else "informe.pdf"
    lineas = [f"# Traza: {g['pedido']}", "",
              f"Corrida `{g['corrida']}` · versión del diseño `{g['version']}` · `{MODELO}`. Para volver a correrla:", "",
              "```", f'.venv/bin/python informes.py {json.dumps(g["pedido"], ensure_ascii=False)} {carpeta}', "```", "",
              f"Resultado: `{Path(carpeta, salida)}` · SQL de las consultas citadas: `{Path(carpeta, 'consultas.sql')}`", "",
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
               "## 4. Costo y tiempo", "", "| Paso | Llamadas | Tokens de entrada | Tokens de salida | US$ | Segundos |",
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
    if "bajada" in redaccion:  # los informes de antes de la decisión 70 tenían un párrafo en lugar de puntos
        redaccion["puntos"] = [redaccion.pop("bajada")]
    return armar(guardado["pedido"], plan, Redaccion(**redaccion), guardado["consultas"], carpeta,
                 guardado.get("nombre", "Informe"))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--traza"]:
        sys.exit(print(escribir_traza(sys.argv[2])))
    if sys.argv[1:2] == ["--rearmar"]:
        sys.exit(print(rearmar(sys.argv[2])))
    if len(sys.argv) < 2:
        sys.exit('Uso: .venv/bin/python informes.py "pedido" [carpeta de salida]  ·  --rearmar carpeta')
    argumentos = sys.argv[1:]
    nombre = "Informe"
    if "--nombre" in argumentos:  # «Informe semanal»…: lo pasa informe_programado.py
        i = argumentos.index("--nombre")
        nombre = argumentos[i + 1]
        del argumentos[i:i + 2]
    asyncio.run(main(argumentos[0], argumentos[1] if len(argumentos) > 1 else f"salidas/{registro.CORRIDA}", nombre))
