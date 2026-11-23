"""La corrida completa con un comando (semana 6, decisión 81): las 20 preguntas, las 5 conversaciones y los 3 informes,
todos por la puerta (puerta.py), con su costo y su tiempo. Los que tienen chequeo en esperados.yaml se evalúan con el
mismo código del evaluador; la reserva (decisión 80) se informa aparte.

Uso: .venv/bin/python evaluacion/correr_todo.py [P13 C1 I2 …]     (sin ids, los 28)
Deja en salidas/completa-<corrida>/: resumen.md, una traza por caso (<id>.md), lo que imprimió cada uno (<id>.log) y,
en los diagnósticos e informes, su carpeta (<id>/) con el diagnóstico o el PDF."""
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "analista"))  # los módulos del sistema

import registro
from agente import guardar_traza
from evaluador import CONVERSACIONES, ESPERADOS, PREGUNTAS, RESERVA, evaluar
from puerta import atender

with open("Data/preguntas/pedidos_de_informe.json") as f:
    INFORMES = {p["id"]: p["texto"] for p in json.load(f)}
TURNOS = {**{i: [t] for i, t in PREGUNTAS.items()}, **CONVERSACIONES, **{i: [t] for i, t in INFORMES.items()}}
PARALELO = 5
CARPETA = Path(f"salidas/completa-{registro.CORRIDA}")
# Los largos primero (informes y diagnósticos, ~1 minuto cada uno), para que no queden solos al final
LARGOS = ["I1", "I2", "I3", "P13", "P14", "P15", "P16"]


class PorCaso:
    """Con 5 casos a la vez, lo que imprime cada uno (tools, planes, hallazgos) se mezclaría: cada línea va al .log de
    su caso, según la variable de contexto del registro. Lo que no es de ningún caso sale por pantalla."""
    def __init__(self, pantalla):
        self.pantalla, self.archivos = pantalla, {}

    def write(self, texto):
        caso = registro.CASO.get()
        if caso is None:
            return self.pantalla.write(texto)
        if caso not in self.archivos:
            self.archivos[caso] = open(CARPETA / f"{caso}.log", "a")
        return self.archivos[caso].write(texto)

    def flush(self):
        self.pantalla.flush()
        for archivo in self.archivos.values():
            archivo.flush()


async def correr(id_, semaforo):
    async with semaforo:
        registro.CASO.set(id_)
        inicio = time.monotonic()
        try:
            respuestas = await atender(TURNOS[id_], carpeta=str(CARPETA / id_))
            error = None
        except Exception as e:  # un caso que se cae no frena los demás
            respuestas, error = [], f"{type(e).__name__}: {e}"
        segundos = time.monotonic() - inicio
        registro.CASO.set(None)
        if respuestas:
            guardar_traza(respuestas, CARPETA / f"{id_}.md", "analista/puerta.py")
        if error:
            chequeo = f"✗ error: {error[:120]}"
        elif id_ in ESPERADOS:
            paso, lineas = evaluar(id_, respuestas)
            chequeo = ("✓" if paso else "✗ " + " · ".join(l for l in lineas if "✗" in l)[:200])
        else:
            chequeo = "–"
        print(f"· {id_}: {chequeo.split(' ')[0]} · {segundos:.0f} s", file=sys.__stdout__, flush=True)
        return {"id": id_, "respuestas": respuestas, "chequeo": chequeo, "segundos": segundos}


def costo_por_caso():
    costos = {}
    for linea in registro.leer(registro.LLAMADAS):
        if linea.get("corrida") == registro.CORRIDA:
            costos[linea["caso"]] = costos.get(linea["caso"], 0) + linea["costo_usd"]
    return costos


def salida_de(id_, respuestas):
    rutas = [r["salida"] for r in respuestas if r.get("salida")]
    return " · ".join(f"[{Path(x).name}]({Path(x).relative_to(CARPETA)})" for x in rutas) or "–"


def resumen(resultados, reloj):
    costos = costo_por_caso()
    grupos = {"Preguntas": [i for i in PREGUNTAS], "Conversaciones": list(CONVERSACIONES), "Informes": list(INFORMES)}
    lineas = [f"# Corrida completa {registro.CORRIDA}", "",
              f"Versión del diseño `{registro.VERSION}` · `claude-haiku-5-5` · para repetirla: `.venv/bin/python evaluacion/correr_todo.py`",
              "", "Chequeo: ✓/✗ contra `esperados.yaml` (R = reserva, decisión 80: no se ajusta nada por ellas); "
              "– = sin chequeo numérico (diagnósticos e informes: se leen). Segundos: reloj de cada caso.", ""]
    por_id = {r["id"]: r for r in resultados}
    total_usd = 0
    for grupo, ids in grupos.items():
        ids = [i for i in ids if i in por_id]
        if not ids:
            continue
        usd = sum(costos.get(i, 0) for i in ids)
        total_usd += usd
        lineas += [f"## {grupo} · US$ {usd:.4f}", "", "| Caso | Tipo → camino | Chequeo | US$ | Segundos | Traza | Salida |",
                   "|---|---|---|---|---|---|---|"]
        for i in ids:
            r = por_id[i]
            tipos = " · ".join(f"{x['tipo']} → {x['ruta']}" for x in r["respuestas"]) or "–"
            chequeo = r["chequeo"] + (" (R)" if i in RESERVA and r["chequeo"] != "–" else "")
            lineas.append(f"| {i} | {tipos} | {chequeo} | {costos.get(i, 0):.4f} | {r['segundos']:.0f} | "
                          f"[{i}.md]({i}.md) | {salida_de(i, r['respuestas'])} |")
        lineas.append("")
    con_chequeo = [r for r in resultados if r["chequeo"] != "–"]
    trabajo = [r for r in con_chequeo if r["id"] not in RESERVA]
    reserva = [r for r in con_chequeo if r["id"] in RESERVA]
    lineas += ["## Total", "",
               f"- **{len(resultados)} casos · US$ {total_usd:.4f} · {reloj:.0f} s de reloj** (de a {PARALELO} en paralelo)",
               f"- Chequeos: {sum(r['chequeo'] == '✓' for r in trabajo)} de {len(trabajo)} de trabajo · "
               f"{sum(r['chequeo'] == '✓' for r in reserva)} de {len(reserva)} de la reserva"]
    (CARPETA / "resumen.md").write_text("\n".join(lineas) + "\n")
    return lineas[-2:]


async def main(ids):
    CARPETA.mkdir(parents=True, exist_ok=True)
    sys.stdout = PorCaso(sys.stdout)
    semaforo = asyncio.Semaphore(PARALELO)
    inicio = time.monotonic()
    # El primero va solo y escribe el caché del prefijo (puerta y agente); los demás lo leen (decisión 72)
    orden = sorted(ids, key=lambda i: (i not in LARGOS, ids.index(i)))
    primero = next((i for i in orden if i not in LARGOS), orden[0])
    resultados = [await correr(primero, semaforo)]
    resultados += await asyncio.gather(*(correr(i, semaforo) for i in orden if i != primero))
    reloj = time.monotonic() - inicio
    sys.stdout = sys.__stdout__
    for linea in resumen(resultados, reloj):
        print(linea)
    print(f"Resumen: {CARPETA / 'resumen.md'}")


if __name__ == "__main__":
    pedidos = sys.argv[1:]
    desconocidos = [i for i in pedidos if i not in TURNOS]
    if desconocidos:
        sys.exit(f"No existen: {', '.join(desconocidos)}. Casos: {', '.join(TURNOS)}")
    asyncio.run(main(pedidos or list(TURNOS)))
