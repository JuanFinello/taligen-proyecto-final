"""Registro de cada llamada al modelo (decisiones 45 y 46): una línea JSON por llamada en registros/llamadas.jsonl,
con tokens, caché, costo, tiempo y tools, y la versión del diseño que estaba corriendo. El evaluador anota además si
cada caso pasó (registros/evaluaciones.jsonl). Así cada cambio de diseño queda con su efecto en costo, tiempo y aciertos.
Uso: .venv/bin/python registro.py                    (resumen de la última corrida)
     .venv/bin/python registro.py 20261113-1         (resumen de esa corrida)
     .venv/bin/python registro.py --todas            (una línea por corrida, con su versión)
     .venv/bin/python registro.py --comparar A B     (dos versiones caso por caso, promediando sus corridas)
Para nombrar un cambio: CAMBIO="decisión 44" .venv/bin/python evaluador.py"""
import hashlib
import json
import os
import sys
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path

LLAMADAS, EVALUACIONES = Path("registros/llamadas.jsonl"), Path("registros/evaluaciones.jsonl")
# USD por millón de tokens de claude-haiku-5-5. Hasta 100.000 tokens de prompt, (entrada, salida); más largo, la otra
TARIFA_CORTA, TARIFA_LARGA, LIMITE_CORTA = (0.10, 0.50), (0.50, 2.50), 100_000
CACHE_LECTURA, CACHE_ESCRITURA = 0.1, 1.25  # por la entrada: leer del caché cuesta 0,1 veces; escribirlo (5 min), 1,25

# La versión del diseño: una huella de los archivos que deciden qué hace Haiku (prompt, criterio, capa y tools).
# Cambia sola con cualquier cambio en ellos, aunque no haya commit; el resto (evaluador, PDF, gráficos) no cuenta
ARCHIVOS_DEL_DISEÑO = ["agente.py", "informes.py", "servidor_mcp.py", "procesador_capa_semantica.py",
                       "Data/capa_semantica/glosario.md", "Data/capa_semantica/medidas.yaml",
                       "Data/capa_semantica/esquema.yaml"]
VERSION = hashlib.sha1(b"".join(Path(a).read_bytes() for a in ARCHIVOS_DEL_DISEÑO if Path(a).exists())).hexdigest()[:6]
CAMBIO = os.environ.get("CAMBIO", "")  # nombre opcional del cambio, para leer las comparaciones
# Una corrida es un proceso (una pregunta, una conversación, el evaluador entero); se puede fijar con CORRIDA=…
CORRIDA = os.environ.get("CORRIDA") or f"{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:4]}"
caso = None  # el evaluador pone acá el id del caso que está corriendo (P03, C2…)


def costo_usd(uso):
    """USD de un usage de la API, con el caché y la tarifa según el largo del prompt."""
    escrito = uso.cache_creation_input_tokens or 0
    leido = uso.cache_read_input_tokens or 0
    entrada, salida = TARIFA_LARGA if uso.input_tokens + escrito + leido > LIMITE_CORTA else TARIFA_CORTA
    return (uso.input_tokens * entrada + escrito * entrada * CACHE_ESCRITURA + leido * entrada * CACHE_LECTURA
            + uso.output_tokens * salida) / 1e6


def _agregar(archivo, linea):
    archivo.parent.mkdir(exist_ok=True)
    base = {"fecha": f"{datetime.now():%Y-%m-%d %H:%M:%S}", "corrida": CORRIDA, "version": VERSION, "cambio": CAMBIO}
    with archivo.open("a") as f:  # una línea corta por write: varios procesos en paralelo no se pisan
        f.write(json.dumps(base | linea, ensure_ascii=False) + "\n")


def anotar(agente, pregunta, vuelta, respuesta, segundos_modelo, segundos_tools=0.0, tools=(), errores=(), sin_respaldo=()):
    """Agrega la línea de una llamada al modelo. `tools`: las que pidió; `errores`: las que fallaron (o el control
    de números); `sin_respaldo`: los números que el control no encontró en ninguna consulta."""
    uso = respuesta.usage
    _agregar(LLAMADAS, {
        "caso": caso, "agente": agente, "pregunta": pregunta, "vuelta": vuelta, "modelo": respuesta.model,
        "fin": respuesta.stop_reason, "tokens_entrada": uso.input_tokens,
        "cache_escrito": uso.cache_creation_input_tokens or 0, "cache_leido": uso.cache_read_input_tokens or 0,
        "tokens_salida": uso.output_tokens, "costo_usd": round(costo_usd(uso), 6),
        "segundos_modelo": round(segundos_modelo, 2), "segundos_tools": round(segundos_tools, 2),
        "tools": list(tools), "errores": list(errores), "sin_respaldo": list(sin_respaldo)})


def anotar_evaluacion(id_caso, paso):
    """El evaluador anota si el caso pasó (una conversación pasa si pasan todos sus turnos)."""
    _agregar(EVALUACIONES, {"caso": id_caso, "paso": paso})


def leer(archivo):
    if not archivo.exists():
        return []
    return [json.loads(l) for l in archivo.read_text().splitlines() if l.strip()]


def totales(lineas):
    return {"llamadas": len(lineas), "entrada": sum(l["tokens_entrada"] for l in lineas),
            "cache": sum(l["cache_leido"] for l in lineas), "salida": sum(l["tokens_salida"] for l in lineas),
            "usd": sum(l["costo_usd"] for l in lineas),
            "segundos": sum(l["segundos_modelo"] + l["segundos_tools"] for l in lineas),
            "errores": sum(len(l["errores"]) for l in lineas)}


def mostrar(nombre, t):
    print(f"{nombre[:60]:60}  {t['llamadas']:>3} llam.  {t['entrada']:>8,} ent.  {t['cache']:>7,} caché  "
          f"{t['salida']:>6,} sal.  US$ {t['usd']:.4f}  {t['segundos']:>6.1f} s  {t['errores']} err.")


def resumen_corrida(llamadas, corrida):
    suyas = [l for l in llamadas if l["corrida"].startswith(corrida)]
    if not suyas:
        sys.exit(f"No hay llamadas de la corrida {corrida}")
    primera = suyas[0]
    print(f"Corrida {primera['corrida']} · versión {primera.get('version', '?')} {primera.get('cambio') or ''}")
    print("Una fila por pregunta (llamadas = vueltas del modelo):\n")
    por_pregunta = defaultdict(list)
    for l in suyas:
        por_pregunta[(l["agente"], l["pregunta"])].append(l)
    for (agente, pregunta), suyas_p in por_pregunta.items():
        mostrar(f"[{agente}] {pregunta}", totales(suyas_p))
    print()
    mostrar("TOTAL", totales(suyas))
    fallidas = defaultdict(int)
    for l in suyas:
        for tool in l["errores"]:
            fallidas[tool.split(":")[0]] += 1  # «calcular: ValueError…» cuenta como calcular
    if fallidas:
        print("\nTools con error: " + ", ".join(f"{t} ({n})" for t, n in fallidas.items()))


def todas(llamadas, evaluaciones):
    por_corrida = defaultdict(list)
    for l in llamadas:
        por_corrida[l["corrida"]].append(l)
    for corrida, suyas in por_corrida.items():
        evs = [e for e in evaluaciones if e["corrida"] == corrida]
        pasan = f" · pasan {sum(e['paso'] for e in evs)}/{len(evs)}" if evs else ""
        etiqueta = f"{corrida} v{suyas[0].get('version', '?')} {suyas[0].get('cambio') or ''}"
        mostrar(etiqueta, totales(suyas))
        if pasan:
            print(f"{'':60}{pasan}")


def por_caso(llamadas, evaluaciones, version):
    """Promedio por corrida de cada caso evaluado de esa versión: costo, segundos y cuántas veces pasó."""
    evs = [e for e in evaluaciones if e["version"].startswith(version)]
    if not evs:
        sys.exit(f"La versión {version} no tiene corridas del evaluador")
    casos = defaultdict(lambda: {"usd": 0.0, "segundos": 0.0, "corridas": set(), "pasa": 0, "veces": 0})
    for e in evs:
        casos[e["caso"]]["pasa"] += e["paso"]
        casos[e["caso"]]["veces"] += 1
        casos[e["caso"]]["corridas"].add(e["corrida"])
    for l in llamadas:
        if l.get("caso") in casos and l["corrida"] in casos[l["caso"]]["corridas"]:
            casos[l["caso"]]["usd"] += l["costo_usd"]
            casos[l["caso"]]["segundos"] += l["segundos_modelo"] + l["segundos_tools"]
    for c in casos.values():
        c["usd"] /= c["veces"]
        c["segundos"] /= c["veces"]
    return casos, evs[-1].get("cambio") or ""


def comparar(llamadas, evaluaciones, a, b):
    casos_a, cambio_a = por_caso(llamadas, evaluaciones, a)
    casos_b, cambio_b = por_caso(llamadas, evaluaciones, b)
    print(f"A = {a} {cambio_a}\nB = {b} {cambio_b}\n(promedio por corrida; «pasa» = veces que pasó / corridas)\n")
    print(f"{'caso':6} {'US$ A':>8} {'US$ B':>8} {'dif.':>6}   {'s A':>5} {'s B':>5}   {'pasa A':>6} {'pasa B':>6}")
    total = {"a": 0.0, "b": 0.0, "sa": 0.0, "sb": 0.0}
    for id_ in sorted(set(casos_a) & set(casos_b)):
        ca, cb = casos_a[id_], casos_b[id_]
        dif = f"{(cb['usd'] / ca['usd'] - 1) * 100:+.0f} %" if ca["usd"] else ""
        print(f"{id_:6} {ca['usd']:8.4f} {cb['usd']:8.4f} {dif:>6}   {ca['segundos']:5.1f} {cb['segundos']:5.1f}   "
              f"{ca['pasa']:>3}/{ca['veces']:<2} {cb['pasa']:>3}/{cb['veces']:<2}")
        total["a"] += ca["usd"]; total["b"] += cb["usd"]; total["sa"] += ca["segundos"]; total["sb"] += cb["segundos"]
    if total["a"]:
        print(f"{'TOTAL':6} {total['a']:8.4f} {total['b']:8.4f} {(total['b'] / total['a'] - 1) * 100:+5.0f} %   "
              f"{total['sa']:5.1f} {total['sb']:5.1f}")
    solo = sorted(set(casos_a) ^ set(casos_b))
    if solo:
        print(f"\nCasos que no están en las dos versiones (no se comparan): {', '.join(solo)}")


if __name__ == "__main__":
    llamadas, evaluaciones = leer(LLAMADAS), leer(EVALUACIONES)
    if not llamadas:
        sys.exit(f"Todavía no hay nada en {LLAMADAS}")
    argumentos = sys.argv[1:]
    if argumentos[:1] == ["--todas"]:
        todas(llamadas, evaluaciones)
    elif argumentos[:1] == ["--comparar"] and len(argumentos) == 3:
        comparar(llamadas, evaluaciones, argumentos[1], argumentos[2])
    else:
        resumen_corrida(llamadas, argumentos[0] if argumentos else llamadas[-1]["corrida"])
