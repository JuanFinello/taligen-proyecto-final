"""Evaluador: pasa por la puerta (puerta.py, decisión 78) y corre el agente con las preguntas y conversaciones de esperados.yaml y compara sus consultas contra lo esperado.
Uso: .venv/bin/python evaluador.py                    (todas, una vez)
     .venv/bin/python evaluador.py P03 P05 C1         (solo esas; C1–C5 son conversaciones, se evalúa cada turno)
     .venv/bin/python evaluador.py --veces 5 P03      (cada una 5 veces: Haiku varía entre corridas)"""
import asyncio
import json
import sys
import time

import yaml

import procesador_capa_semantica as procesador
import registro
from puerta import atender
from controles import MAX_SIN_CONTROL, numeros_del_texto, sin_respaldo, valores_de

with open("Data/preguntas/esperados.yaml") as f:
    ESPERADOS = yaml.safe_load(f)
RESERVA = set(ESPERADOS.pop("RESERVA"))  # decisión 80: se informan aparte y no se ajusta nada por ellas
ESPERADOS.pop("TIPOS")  # los de la puerta (puerta.py --medir), no son casos
with open("Data/preguntas/preguntas.json") as f:
    PREGUNTAS = {p["id"]: p["texto"] for p in json.load(f)}
with open("Data/preguntas/conversaciones.json") as f:
    CONVERSACIONES = {c["id"]: c["turnos"] for c in json.load(f)}


def equivalente_a_margen_pct(resultado):
    """Un resultado de efectos_margen con los nombres de campo de una comparación de margen_pct."""
    def renombrar(fila):
        return {**fila, "actual": fila.get("margen_pct_actual"), "anterior": fila.get("margen_pct_anterior"),
                "variacion": fila.get("variacion_pp")}
    return {**renombrar(resultado), "filas": [renombrar(f) for f in resultado.get("filas", [])]}


def cumple(chequeo, consulta):
    """¿Esta consulta del agente usó la medida esperada y dio el valor esperado?"""
    argumentos, resultado = consulta["argumentos"], consulta["resultado"]
    if chequeo["medida"] == "margen_pct" and argumentos.get("medida") == "efectos_margen":
        # efectos_margen trae el mismo margen % y su variación con otros nombres: es la misma medida, no otra (decisión 75)
        resultado = equivalente_a_margen_pct(resultado)
    elif argumentos.get("medida") != chequeo["medida"]:  # una consulta SQL no tiene medida: no cumple
        return False
    cerca = lambda v: v is not None and abs(v - chequeo["esperado"]) <= chequeo["tolerancia"] + 1e-9
    # Con `fila` (por ejemplo {categoria: Almacén}), también vale esa fila de una consulta agrupada: Haiku a veces
    # agrupa en vez de filtrar y lee la fila que corresponde. Solo esa fila, no cualquiera (decisión 37)
    filas = [f for f in resultado.get("filas", []) if chequeo.get("fila")
             and all(f.get(dimension) == valor for dimension, valor in chequeo["fila"].items())]
    if chequeo["tipo"] == "valor":  # también vale el de un período de una comparación, o el total de una agrupación
        periodos = [resultado[k] for k in ("actual", "anterior") if isinstance(resultado.get(k), dict)]
        if any(cerca(f.get(k)) for f in filas for k in ("valor", "actual", "anterior")):
            return True
        return any(cerca(r.get("valor")) for r in [resultado, *periodos]) or cerca(resultado.get("total"))
    if chequeo["tipo"] == "variacion":
        if resultado.get("comparables") == chequeo["comparables"] and any(cerca(f.get("variacion")) for f in filas):
            return True
        return ("variacion" in resultado and resultado["comparables"] == chequeo["comparables"]
                and abs(resultado["variacion"] - chequeo["esperado"]) <= chequeo["tolerancia"] + 1e-9)
    if chequeo["tipo"] == "ranking":
        codigos = [fila.get(chequeo["dimension"]) for fila in resultado.get("filas", [])]
        return codigos[:len(chequeo["esperado"])] == chequeo["esperado"]
    if chequeo["tipo"] == "grupo":  # agrupó por esa dimensión y la fila de ese código tiene esa variación
        if chequeo["dimension"] not in (argumentos.get("agrupar_por") or []):
            return False
        return any(fila.get(chequeo["dimension"]) == chequeo["codigo"] and cerca(fila.get("variacion"))
                   for fila in resultado.get("filas", []))
    raise ValueError(f"Tipo de chequeo desconocido: {chequeo['tipo']}")


def diagnostico(chequeo, consultas):
    """Para un chequeo que no pasó: ¿no usó la medida, o la usó y el número no dio?"""
    if not any(c["argumentos"].get("medida") == chequeo["medida"] for c in consultas):
        usadas = sorted({c["argumentos"].get("medida", "sql") for c in consultas}) or ["ninguna"]
        return f"no usó {chequeo['medida']} (usó: {', '.join(usadas)})"
    return f"usó {chequeo['medida']}, pero no dio {chequeo['esperado']}"


def fallos(chequeos, consultas, respuesta=None):
    """Los chequeos que no pasan. `respuesta` (la del turno) hace falta para la ambigua y la sin dato, que miran qué
    dijo y no solo qué consultó (decisión 76). Los avisos van con «aviso:» y no hacen fallar."""
    malos = []
    datos = (respuesta or {}).get("registro")
    for chequeo in chequeos:
        if chequeo["tipo"] == "sin_dato":
            # Como el enunciado: dice que no está y no responde con otro indicador
            usados = [c for c in consultas if numeros_de_consultas_en(respuesta["texto"], [c])]
            if datos is not None and datos.valor is not None:
                malos.append(f"respondió con un valor ({datos.valor} {datos.unidad})")
            elif usados:
                malos.append("respondió con cifras de otra medida (" + ", ".join(c["argumentos"].get("medida", "sql") for c in usados) + ")")
            elif consultas:
                malos.append("aviso: consultó algo que no usó (" + ", ".join(c["argumentos"].get("medida", "sql") for c in consultas) + ")")
        elif chequeo["tipo"] == "lecturas":
            # Como el enunciado: las dos lecturas, o una declarada como supuesto; nunca una elegida en silencio
            dadas = [e for e in chequeo["esperados"]
                     if any(cumple({**chequeo, "tipo": "valor", "esperado": e}, c) for c in consultas)]
            if not dadas:
                malos.append(f"no consultó ninguna de las lecturas ({', '.join(map(str, chequeo['esperados']))})")
            elif len(dadas) < len(chequeo["esperados"]) and not (datos and datos.supuestos):
                malos.append("eligió una lectura sin declararla en supuestos")
        elif not any(cumple(chequeo, c) for c in consultas):
            malos.append(diagnostico(chequeo, consultas))
    return malos


def numeros_de_consultas_en(texto, consultas):
    """¿El texto trae alguna cifra de los resultados de estas consultas? (sin contar los enteros chicos ni el año)"""
    valores = valores_de([c["resultado"] for c in consultas])
    for valor, tolerancia, escrito in numeros_del_texto(texto):
        if (valor.is_integer() and valor <= MAX_SIN_CONTROL and "," not in escrito) or 1900 <= valor <= 2100:
            continue
        if any(abs(valor - abs(v)) <= tolerancia for v in valores):
            return True
    return False


def falla(lineas_malas):
    """Los avisos no hacen fallar."""
    return [m for m in lineas_malas if not m.startswith("aviso:")]


def reproducible(respuesta):
    """Acierto de consulta (enunciado, sección 5): las consultas que la respuesta declara, vueltas a ejecutar con los
    mismos argumentos, generan el mismo SQL y de sus resultados sale el valor reportado (decisión 75). None si la
    respuesta no reporta un valor (una ambigua que pregunta, una sin dato)."""
    datos = respuesta.get("registro")
    if datos is None or datos.valor is None:
        return None
    rehacer = {"calcular": lambda a: procesador.calcular(**a), "consultar_sql": lambda a: procesador.consultar_sql(**a),
               "buscar_producto": lambda a: procesador.buscar_producto(**a)}
    nuevos = []
    for consulta in respuesta["consultas"]:
        nuevo = rehacer[consulta["tool"]](consulta["argumentos"])
        if [sql for _, sql, _ in procesador.sqls(nuevo)] != [sql for _, sql, _ in procesador.sqls(consulta["resultado"])]:
            return f"la consulta {consulta['argumentos']} genera otro SQL al volver a correrla"
        nuevos.append(json.loads(json.dumps(nuevo, default=str)))  # como lo vio el agente (fechas como texto)
    # Igual al valor de una consulta salvo una milmillonésima: DuckDB suma en paralelo y una suma grande puede cambiar
    # en el décimo decimal entre corridas (460.758.207,2699909 y …2699913). O redondeado, como lo acepta el control
    valores = valores_de(nuevos)
    escrito = f"{datos.valor:.10f}".rstrip("0").rstrip(".").replace(".", ",")
    if (not any(abs(abs(datos.valor) - abs(v)) <= 1e-9 * max(1.0, abs(v)) for v in valores)
            and sin_respaldo(escrito, valores)):
        return f"el valor reportado {datos.valor} no sale de sus consultas al volver a correrlas"
    return ""


PARALELO = 5  # casos a la vez (decisión 74). Más no gana mucho: el más largo (una conversación) marca el tiempo


def ruteo(respuesta):
    """Todos los casos del evaluador son del agente: si la puerta los manda al coordinador, falla (decisión 78)."""
    if respuesta["ruta"] != "agente":
        return [f"ruteo: la puerta lo tomó como {respuesta['tipo']} y lo mandó al coordinador ({respuesta['motivo']})"]
    return []


async def correr(id_):
    """Una corrida de una pregunta o de una conversación: devuelve (pasó, líneas para mostrar)."""
    registro.CASO.set(id_)  # cada tarea tiene su copia del contexto: las llamadas quedan anotadas con su caso
    return evaluar(id_, await atender(CONVERSACIONES.get(id_) or [PREGUNTAS[id_]]))


def evaluar(id_, respuestas):
    """(pasó, líneas) de las respuestas de un caso con chequeo. Lo usa también correr_todo.py (decisión 81)."""
    if id_ not in CONVERSACIONES:
        respuesta = respuestas[0]
        malos = fallos(ESPERADOS[id_], respuesta["consultas"], respuesta) + ruteo(respuesta)
        if motivo := reproducible(respuesta):
            malos.append("consulta: " + motivo)
        return not falla(malos), [("✓" if not falla(malos) else "✗") + (" " + " · ".join(malos) if malos else "")]
    # Conversación: se evalúa turno por turno, así se ve si heredó lo anterior (decisión 32)
    paso, lineas, hasta_ahora = True, [], []
    for numero, (respuesta, chequeos) in enumerate(zip(respuestas, ESPERADOS[id_]["turnos"]), 1):
        # Valen sus consultas y las de turnos anteriores (puede reusar un número ya consultado); como el valor
        # esperado depende de los filtros, un turno que pierde un filtro igual falla
        hasta_ahora += respuesta["consultas"]
        if mal_ruteado := ruteo(respuesta):
            paso = False
            lineas.append(f"turno {numero}: ✗ {mal_ruteado[0]}")
            continue
        motivo = reproducible(respuesta)
        if motivo:  # la respuesta del turno declara consultas que no dan su valor: falla aunque el número esperado esté
            paso = False
            lineas.append(f"turno {numero}: ✗ consulta: {motivo}")
            continue
        if not chequeos:
            lineas.append(f"turno {numero}: – sin chequeo numérico")
            continue
        malos = fallos(chequeos, hasta_ahora, respuesta)
        paso = paso and not falla(malos)
        lineas.append(f"turno {numero}: " + ("✓" if not falla(malos) else "✗") + (" " + " · ".join(malos) if malos else ""))
    return paso, lineas


async def main(ids, veces=1):
    """Corre los casos en paralelo, de a PARALELO. El primero va solo: escribe el caché del prefijo (tools, sistema y
    glosario) y los demás lo leen; si arrancaran todos juntos, cada uno pagaría la escritura (decisión 72)."""
    trabajos = [(id_, vez) for id_ in ids for vez in range(1, veces + 1)]
    semaforo = asyncio.Semaphore(PARALELO)
    inicio = time.monotonic()

    async def uno(id_, vez):
        async with semaforo:
            paso, lineas = await correr(id_)
            registro.anotar_evaluacion(id_, paso)
            print(f"· {id_}{f' (corrida {vez})' if veces > 1 else ''}: {'✓' if paso else '✗'}", flush=True)
            return paso, lineas

    resultados = [await uno(*trabajos[0])] if trabajos else []
    resultados += await asyncio.gather(*(uno(*t) for t in trabajos[1:]))

    # El detalle, en el orden de los casos y no en el que terminaron
    aprobadas = {True: 0, False: 0}  # True: reserva
    for id_ in ids:
        print(f"\n===== {id_}: {PREGUNTAS.get(id_) or ' → '.join(CONVERSACIONES[id_])}")
        suyos = [r for (caso, _), r in zip(trabajos, resultados) if caso == id_]
        for vez, (paso, lineas) in enumerate(suyos, 1):
            for linea in lineas:
                print(linea if veces == 1 else f"  corrida {vez}: {linea}")
        pasadas = sum(paso for paso, _ in suyos)
        if veces > 1:
            print(f"{'✓' if pasadas == veces else '✗'} {id_}: {pasadas} de {veces}")
        aprobadas[id_ in RESERVA] += pasadas == veces  # aprueba solo si pasa todas las veces (conversación: todos sus turnos)
    trabajo, reserva = [i for i in ids if i not in RESERVA], [i for i in ids if i in RESERVA]
    partes = [f"{aprobadas[False]} de {len(trabajo)} de trabajo"] if trabajo else []
    partes += [f"{aprobadas[True]} de {len(reserva)} de la reserva (no se ajusta nada por ellas)"] if reserva else []
    print(f"\nResultado: {' · '.join(partes)} pasan" + (f" (las {veces} veces)" if veces > 1 else "")
          + f" · {time.monotonic() - inicio:.0f} s de reloj")


if __name__ == "__main__":
    argumentos = sys.argv[1:]
    veces = 1
    if "--veces" in argumentos:
        i = argumentos.index("--veces")
        veces = int(argumentos[i + 1])
        del argumentos[i:i + 2]
    asyncio.run(main(argumentos or list(ESPERADOS), veces))
