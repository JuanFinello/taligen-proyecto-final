"""Test 2 (decisión 94): robustez del lenguaje. La misma pregunta dicha de otras maneras (coloquial, con errores, con
sinónimos, corta) tiene que dar el mismo número. Las variantes están en Data/preguntas/variantes.yaml y cada una se
califica con el chequeo de su pregunta original (evaluador.evaluar: misma medida, mismo valor, consulta reproducible y
que la puerta la mande al agente). La original va también, como control en la misma corrida.

Uso: .venv/bin/python evaluacion/pruebas/lenguaje.py [--veces N]      (~US$ 0,05 por vez, de a 5 en paralelo)
Deja salidas/lenguaje/resultado.md y lo copia a trazas/lenguaje.md."""
import asyncio
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(RAIZ / "analista"), str(RAIZ / "evaluacion")]

import yaml  # noqa: E402

import registro  # noqa: E402
from evaluador import PREGUNTAS, RESERVA, evaluar  # noqa: E402
from puerta import atender  # noqa: E402

CARPETA = Path("salidas/lenguaje")
PARALELO = 5
ESTILOS = ["original", "coloquial", "errores", "sinonimos", "corta"]
with open("Data/preguntas/esperados.yaml") as f:
    TIPOS = yaml.safe_load(f)["TIPOS"]


def casos():
    with open("Data/preguntas/variantes.yaml") as f:
        variantes = yaml.safe_load(f)
    salida = []
    for id_, lista in variantes.items():
        if id_ in RESERVA:
            sys.exit(f"{id_} es de la reserva (decisión 80): no se usa para variantes")
        salida.append({"id": id_, "estilo": "original", "autor": "—", "texto": PREGUNTAS[id_]})
        salida += [{"id": id_, **v} for v in lista]
    return salida


async def correr(caso, vez, semaforo):
    async with semaforo:
        registro.CASO.set(f"{caso['id']}-{caso['estilo']}-{vez}")
        respuestas = await atender([caso["texto"]])
        paso, lineas = evaluar(caso["id"], respuestas)
        r = respuestas[0]
        print(f"· {caso['id']} {caso['estilo']}: {'✓' if paso else '✗'}", flush=True)
        return {**caso, "vez": vez, "paso": paso, "detalle": " ".join(lineas), "tipo": r.get("tipo"),
                "tipo_esperado": TIPOS.get(caso["id"]), "texto_respuesta": r["texto"]}


def costo():
    return sum(l["costo_usd"] for l in registro.leer(registro.LLAMADAS) if l.get("corrida") == registro.CORRIDA)


async def main(veces):
    CARPETA.mkdir(parents=True, exist_ok=True)
    lista = casos()
    semaforo = asyncio.Semaphore(PARALELO)
    inicio = time.monotonic()
    trabajos = [(c, v) for v in range(1, veces + 1) for c in lista]
    resultados = [await correr(*trabajos[0], semaforo)]  # el primero solo: escribe el caché del prefijo
    resultados += await asyncio.gather(*(correr(c, v, semaforo) for c, v in trabajos[1:]))
    reloj = time.monotonic() - inicio

    si = lambda x: "✓" if x else "✗"
    ids = list(dict.fromkeys(c["id"] for c in lista))
    por = {(r["id"], r["estilo"], r["texto"]): [] for r in resultados}
    for r in resultados:
        por[(r["id"], r["estilo"], r["texto"])].append(r)
    variantes = [r for r in resultados if r["estilo"] != "original"]
    lineas = ["# Test 2: robustez del lenguaje (decisión 94)", "",
              f"Comando: `.venv/bin/python evaluacion/pruebas/lenguaje.py{f' --veces {veces}' if veces > 1 else ''}` · "
              f"{len(lista)} preguntas × {veces} · US$ {costo():.3f} · {reloj:.0f} s", "",
              f"**Variantes que dan el número correcto: {sum(r['paso'] for r in variantes)} de {len(variantes)}** · "
              f"originales: {sum(r['paso'] for r in resultados if r['estilo'] == 'original')} de "
              f"{sum(1 for r in resultados if r['estilo'] == 'original')}", "",
              "## Por pregunta", "", "| Pregunta | " + " | ".join(ESTILOS) + " |", "|---|" + "---|" * len(ESTILOS)]
    for id_ in ids:
        celdas = []
        for estilo in ESTILOS:
            rs = [r for r in resultados if r["id"] == id_ and r["estilo"] == estilo]
            celdas.append(" · ".join(f"{sum(r['paso'] for r in rs)}/{len(rs)}" for _ in [0]) if rs else "—")
        lineas.append(f"| {id_} | " + " | ".join(celdas) + " |")
    lineas += ["", "## Por estilo", "", "| Estilo | Número correcto | La puerta le dio el tipo de la original |", "|---|---|---|"]
    for estilo in ESTILOS:
        rs = [r for r in resultados if r["estilo"] == estilo]
        lineas.append(f"| {estilo} | {sum(r['paso'] for r in rs)} de {len(rs)} | "
                      f"{sum(r['tipo'] == r['tipo_esperado'] for r in rs)} de {len(rs)} |")
    lineas += ["", "## Cada variante", "", "| Pregunta | Estilo | Texto | Tipo (esperado) | Chequeo |", "|---|---|---|---|---|"]
    for (id_, estilo, texto), rs in por.items():
        tipos = ", ".join(sorted({str(r["tipo"]) for r in rs}))
        lineas.append(f"| {id_} | {estilo} | {texto} | {tipos} ({rs[0]['tipo_esperado']}) | "
                      + " · ".join(f"{si(r['paso'])}{(' ' + r['detalle'].lstrip('✓✗ ')) if not r['paso'] else ''}" for r in rs) + " |")
    malas = [r for r in resultados if not r["paso"]]
    if malas:
        lineas += ["", "## Las que fallaron: qué respondió", ""]
        for r in malas:
            lineas += [f"**{r['id']} {r['estilo']}** — «{r['texto']}»", "", "> " + r["texto_respuesta"].replace("\n", "\n> "), ""]
    texto = "\n".join(lineas) + "\n"
    (CARPETA / "resultado.md").write_text(texto)
    (CARPETA / "resultados.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2, default=str))
    Path("trazas/lenguaje.md").write_text(texto)
    print(texto)


if __name__ == "__main__":
    args = sys.argv[1:]
    asyncio.run(main(int(args[args.index("--veces") + 1]) if "--veces" in args else 1))
