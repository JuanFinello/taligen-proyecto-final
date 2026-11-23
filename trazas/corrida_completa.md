# Traza: la corrida completa con un comando (semana 6)

Corrida 20261123-145542-6877 del 23-11-2026. Versión del diseño `274510` · `claude-haiku-5-5` · para repetirla: `.venv/bin/python evaluacion/correr_todo.py`

Chequeo: ✓/✗ contra `esperados.yaml` (R = reserva, decisión 80: no se ajusta nada por ellas); – = sin chequeo numérico (diagnósticos e informes: se leen). Segundos: reloj de cada caso.

## Preguntas · US$ 0.0668

| Caso | Tipo → camino | Chequeo | US$ | Segundos | Traza | Salida |
|---|---|---|---|---|---|---|
| P01 | puntual → agente | ✓ | 0.0010 | 8 | P01.md | – |
| P02 | puntual → agente | ✓ | 0.0010 | 8 | P02.md | – |
| P03 | puntual → agente | ✓ | 0.0015 | 11 | P03.md | – |
| P04 | puntual → agente | ✓ | 0.0005 | 6 | P04.md | – |
| P05 | puntual → agente | ✓ | 0.0009 | 9 | P05.md | – |
| P06 | comparativa → agente | ✓ | 0.0017 | 9 | P06.md | – |
| P07 | comparativa → agente | ✓ | 0.0030 | 18 | P07.md | – |
| P08 | comparativa → agente | ✓ | 0.0016 | 10 | P08.md | – |
| P09 | puntual → agente | ✓ (R) | 0.0015 | 11 | P09.md | – |
| P10 | ranking → agente | ✓ | 0.0017 | 15 | P10.md | – |
| P11 | ranking → agente | ✓ | 0.0014 | 12 | P11.md | – |
| P12 | ranking → agente | ✓ (R) | 0.0019 | 13 | P12.md | – |
| P13 | diagnostico → coordinador | – | 0.0106 | 44 | P13.md | diagnostico.md |
| P14 | diagnostico → coordinador | – | 0.0138 | 64 | P14.md | diagnostico.md |
| P15 | diagnostico → coordinador | – | 0.0092 | 42 | P15.md | diagnostico.md |
| P16 | diagnostico → coordinador | – | 0.0110 | 53 | P16.md | diagnostico.md |
| P17 | ambigua → agente | ✓ | 0.0013 | 8 | P17.md | – |
| P18 | ambigua → agente | ✓ (R) | 0.0016 | 11 | P18.md | – |
| P19 | sin_dato → agente | ✓ (R) | 0.0009 | 7 | P19.md | – |
| P20 | sin_dato → agente | ✓ | 0.0009 | 6 | P20.md | – |

## Conversaciones · US$ 0.0207

| Caso | Tipo → camino | Chequeo | US$ | Segundos | Traza | Salida |
|---|---|---|---|---|---|---|
| C1 | comparativa → agente · comparativa → agente · ranking → agente | ✓ | 0.0040 | 29 | C1.md | – |
| C2 | puntual → agente · comparativa → agente · ranking → agente | ✓ | 0.0082 | 57 | C2.md | – |
| C3 | puntual → agente · comparativa → agente · comparativa → agente | ✓ | 0.0027 | 20 | C3.md | – |
| C4 | puntual → agente · puntual → agente · puntual → agente | ✓ | 0.0033 | 24 | C4.md | – |
| C5 | ambigua → agente · puntual → agente · puntual → agente | ✓ | 0.0025 | 20 | C5.md | – |

## Informes · US$ 0.0520

| Caso | Tipo → camino | Chequeo | US$ | Segundos | Traza | Salida |
|---|---|---|---|---|---|---|
| I1 | informe → coordinador | – | 0.0166 | 72 | I1.md | informe.pdf |
| I2 | informe → coordinador | – | 0.0146 | 89 | I2.md | informe.pdf |
| I3 | informe → coordinador | – | 0.0207 | 94 | I3.md | informe.pdf |

## Total

- **28 casos · US$ 0.1395 · 182 s de reloj** (de a 5 en paralelo)
- Chequeos: 17 de 17 de trabajo · 4 de 4 de la reserva

Los informes, calificados con `evaluacion/chequeos_informes.py` (6 chequeos de contenido cada uno): **14 de 18**. No pasaron: I1 no dice cuánto bajó el margen %, I2 lleva una cita [Cn] en el título, e I3 no dice desde cuándo caen las comparables del Oeste y se va al margen en el título. Varía entre corridas: la del mismo día a las 12:27 pasó 18 de 18 (sus PDF están en [`docs/informes/`](../docs/informes/)), y con este diseño, en 6 corridas, 95 de 108 (88 %, [comparación de versiones](comparacion_informes.md)).

Las salidas de cada caso (trazas, diagnósticos y PDF) quedan en `salidas/completa-<corrida>/`, que no se commitea; los nombres de la tabla son los de esa carpeta.
