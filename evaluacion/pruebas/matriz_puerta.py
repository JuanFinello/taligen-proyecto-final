"""Test 8 (decisión 99): la matriz de confusión de la puerta. Junta todas las preguntas sueltas con tipo conocido y
cuenta, para cada tipo real, qué tipo le dio la puerta (puerta.clasificar). Lo que importa más es el camino (agente o
coordinador, decisión 78): un tipo equivocado dentro del mismo camino no cambia quién responde; un camino equivocado sí.

De dónde salen los tipos reales:
- las 20 preguntas y los 3 informes: TIPOS de esperados.yaml (los de las apartadas se declararon en la decisión 5);
- las 28 variantes del test 2: el tipo de su original;
- las preguntas del test 3 (fechas): el tipo lo declaró quien escribió el test (escrito abajo, antes de correr).
Las de los tests 1 y 4 no entran: hablan de las bases simuladas (mayo de 2026, el AF2027), y contra la base real la
puerta tiene razón en decir que son sin dato (en una primera corrida, con ellas, eso pareció un error de la puerta).
Las conversaciones no entran: sus turnos dependen de los anteriores.

Uso: .venv/bin/python evaluacion/pruebas/matriz_puerta.py [--veces N]      (~US$ 0,02 por vez; solo clasifica, no responde)
Deja salidas/matriz_puerta/resultado.md y lo copia a trazas/matriz_puerta.md."""
import asyncio
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(RAIZ / "analista"), str(RAIZ / "evaluacion")]

import anthropic  # noqa: E402
import yaml  # noqa: E402

import registro  # noqa: E402
from puerta import AL_COORDINADOR, TIPOS, clasificar  # noqa: E402

CARPETA = Path("salidas/matriz_puerta")
# Tipos declarados para las preguntas del test 3, antes de correr
DECLARADOS = [
    ("fechas F01", "¿Cuánto vendimos el último mes?", "puntual"),
    ("fechas F02", "¿Cuánto vendimos el mes pasado?", "puntual"),
    ("fechas F03", "¿Cuánto llevamos vendido en este año fiscal?", "puntual"),
    ("fechas F04", "¿Cuánto vendimos en el primer mes del AF2026?", "puntual"),
    ("fechas F05", "¿Cuánto vendimos en el AF2026 hasta octubre inclusive?", "puntual"),
    ("fechas F06", "¿Cuánto vendimos en el último mes del AF2025?", "puntual"),
    ("fechas F07", "¿Cuánto vendimos el año pasado?", "ambigua"),
    ("fechas F08", "¿Cuánto vendimos en abril?", "ambigua"),
    ("fechas F09", "¿Cuánto vendimos en el T2 de 2025?", "ambigua"),
    ("fechas F10", "¿Cuánto vendimos en la primera quincena de marzo de 2026?", "puntual"),
    ("fechas F11", "¿Cuánto vendimos entre el 10 y el 20 de enero de 2026?", "puntual"),
    ("fechas F13", "¿Cuánto vendimos en el AF2027?", "sin_dato"),
    ("fechas F14", "¿Cuánto vendimos en marzo de 2024?", "sin_dato"),
]


def casos():
    with open("Data/preguntas/esperados.yaml") as f:
        tipos = yaml.safe_load(f)["TIPOS"]
    textos = {p["id"]: p["texto"] for archivo in ("preguntas", "pedidos_de_informe")
              for p in json.load(open(f"Data/preguntas/{archivo}.json"))}
    salida = [(id_, textos[id_], t) for id_, t in tipos.items() if id_ in textos]
    with open("Data/preguntas/variantes.yaml") as f:
        variantes = yaml.safe_load(f)
    salida += [(f"{id_} {v['estilo']}", v["texto"], tipos[id_]) for id_, lista in variantes.items() for v in lista]
    salida += [(i, t, tipo) for i, t, tipo in DECLARADOS if tipo]
    return salida


def camino(tipo):
    return "coordinador" if tipo in AL_COORDINADOR else "agente"


async def main(veces):
    CARPETA.mkdir(parents=True, exist_ok=True)
    lista = casos()
    semaforo = asyncio.Semaphore(5)
    async with anthropic.AsyncAnthropic() as claude:
        async def uno(caso, vez):
            async with semaforo:
                registro.CASO.set(f"{caso[0]}-{vez}")
                c = await clasificar(caso[1], [], claude)
                return {"id": caso[0], "texto": caso[1], "real": caso[2], "dio": c.tipo, "motivo": c.motivo, "vez": vez}
        trabajos = [(c, v) for v in range(1, veces + 1) for c in lista]
        resultados = [await uno(*trabajos[0])] + list(await asyncio.gather(*(uno(c, v) for c, v in trabajos[1:])))

    reales = [t for t in TIPOS if any(r["real"] == t for r in resultados)]
    dados = [t for t in TIPOS if any(r["dio"] == t for r in resultados)] + (["(ninguno)"] if any(r["dio"] is None for r in resultados) else [])
    matriz = Counter((r["real"], r["dio"] or "(ninguno)") for r in resultados)
    bien_tipo = sum(r["real"] == r["dio"] for r in resultados)
    bien_camino = sum(camino(r["real"]) == camino(r["dio"]) for r in resultados)
    costo = sum(l["costo_usd"] for l in registro.leer(registro.LLAMADAS) if l.get("corrida") == registro.CORRIDA)
    n = len(resultados)
    lineas = ["# Test 8: matriz de confusión de la puerta (decisión 99)", "",
              f"Comando: `.venv/bin/python evaluacion/pruebas/matriz_puerta.py{f' --veces {veces}' if veces > 1 else ''}` · "
              f"{len(lista)} preguntas × {veces} · US$ {costo:.3f}", "",
              f"**Camino correcto (agente o coordinador): {bien_camino} de {n} ({bien_camino / n * 100:.1f} %)** · "
              f"tipo exacto: {bien_tipo} de {n} ({bien_tipo / n * 100:.1f} %)", "",
              "## La matriz (filas: tipo real · columnas: lo que dio la puerta)", "",
              "| Real \\ Dio | " + " | ".join(dados) + " | Total | Acierto |", "|---|" + "---|" * (len(dados) + 2)]
    for real in reales:
        fila = [matriz[(real, d)] for d in dados]
        total = sum(fila)
        lineas.append(f"| **{real}** | " + " | ".join(f"**{x}**" if d == real else (str(x) if x else "·")
                                                    for x, d in zip(fila, dados))
                      + f" | {total} | {matriz[(real, real)] / total * 100:.0f} % |")
    lineas += ["", "## Precisión y exhaustividad por tipo", "",
               "Precisión: de lo que la puerta llamó X, cuánto era X. Exhaustividad: de lo que era X, cuánto llamó X.", "",
               "| Tipo | Precisión | Exhaustividad | Camino |", "|---|---|---|---|"]
    for t in reales:
        llamados = sum(1 for r in resultados if r["dio"] == t)
        eran = sum(1 for r in resultados if r["real"] == t)
        ok = matriz[(t, t)]
        lineas.append(f"| {t} | {f'{ok / llamados * 100:.0f} %' if llamados else '—'} | {ok / eran * 100:.0f} % | {camino(t)} |")
    errores_camino = [r for r in resultados if camino(r["real"]) != camino(r["dio"])]
    lineas += ["", f"## Camino equivocado ({len(errores_camino)})", ""]
    lineas += [f"- **{r['id']}** ({r['vez']}): real {r['real']}, dio {r['dio']} · «{r['texto']}» · motivo: {r['motivo']}" for r in errores_camino] or ["Ninguno."]
    confundidas = Counter((r["id"], r["texto"], r["real"], r["dio"]) for r in resultados if r["real"] != r["dio"] and camino(r["real"]) == camino(r["dio"]))
    lineas += ["", "## Tipo equivocado dentro del camino correcto", ""]
    lineas += [f"- {i}: real {real}, dio {dio} ({k} de {veces}) · «{t}»" for (i, t, real, dio), k in confundidas.most_common()] or ["Ninguno."]
    texto = "\n".join(lineas) + "\n"
    (CARPETA / "resultado.md").write_text(texto)
    (CARPETA / "resultados.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2))
    Path("trazas/matriz_puerta.md").write_text(texto)
    print(texto)


if __name__ == "__main__":
    args = sys.argv[1:]
    asyncio.run(main(int(args[args.index("--veces") + 1]) if "--veces" in args else 1))
