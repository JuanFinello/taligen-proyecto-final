# Traza: la corrida completa con un comando (semana 6)

Corrida 20261123-172910-fc27 del 23-11-2026. Versión del diseño `a3747b` (decisión 122) · `claude-haiku-5-5` · para repetirla: `.venv/bin/python evaluacion/correr_todo.py`

Chequeo: ✓/✗ contra `esperados.yaml` (R = reserva, decisión 80: no se ajusta nada por ellas); – = sin chequeo numérico (diagnósticos e informes: se leen). Segundos: reloj de cada caso.

## Preguntas · US$ 0.0667

| Caso | Tipo → camino | Chequeo | US$ | Segundos | Traza | Salida |
|---|---|---|---|---|---|---|
| P01 | puntual → agente | ✓ | 0.0006 | 9 | P01.md | – |
| P02 | puntual → agente | ✓ | 0.0010 | 8 | P02.md | – |
| P03 | puntual → agente | ✓ | 0.0009 | 9 | P03.md | – |
| P04 | puntual → agente | ✓ | 0.0005 | 8 | P04.md | – |
| P05 | puntual → agente | ✓ | 0.0007 | 9 | P05.md | – |
| P06 | comparativa → agente | ✓ | 0.0017 | 14 | P06.md | – |
| P07 | comparativa → agente | ✓ | 0.0033 | 19 | P07.md | – |
| P08 | comparativa → agente | ✓ | 0.0017 | 11 | P08.md | – |
| P09 | puntual → agente | ✓ (R) | 0.0011 | 10 | P09.md | – |
| P10 | ranking → agente | ✓ | 0.0023 | 16 | P10.md | – |
| P11 | ranking → agente | ✓ | 0.0014 | 11 | P11.md | – |
| P12 | ranking → agente | ✓ (R) | 0.0018 | 12 | P12.md | – |
| P13 | diagnostico → coordinador | – | 0.0079 | 41 | P13.md | diagnostico.md |
| P14 | diagnostico → coordinador | – | 0.0109 | 53 | P14.md | diagnostico.md |
| P15 | diagnostico → coordinador | – | 0.0082 | 45 | P15.md | diagnostico.md |
| P16 | diagnostico → coordinador | – | 0.0183 | 72 | P16.md | diagnostico.md |
| P17 | ambigua → agente | ✓ | 0.0014 | 11 | P17.md | – |
| P18 | ambigua → agente | ✓ (R) | 0.0012 | 10 | P18.md | – |
| P19 | sin_dato → agente | ✓ (R) | 0.0010 | 7 | P19.md | – |
| P20 | sin_dato → agente | ✓ | 0.0009 | 9 | P20.md | – |

## Conversaciones · US$ 0.0193

| Caso | Tipo → camino | Chequeo | US$ | Segundos | Traza | Salida |
|---|---|---|---|---|---|---|
| C1 | comparativa → agente · comparativa → agente · ranking → agente | ✓ | 0.0043 | 30 | C1.md | – |
| C2 | puntual → agente · comparativa → agente · ranking → agente | ✓ | 0.0047 | 38 | C2.md | – |
| C3 | puntual → agente · comparativa → agente · comparativa → agente | ✓ | 0.0042 | 32 | C3.md | – |
| C4 | puntual → agente · puntual → agente · puntual → agente | ✓ | 0.0039 | 31 | C4.md | – |
| C5 | ambigua → agente · ambigua → agente · puntual → agente | ✓ | 0.0021 | 23 | C5.md | – |

## Informes · US$ 0.0599

| Caso | Tipo → camino | Chequeo | US$ | Segundos | Traza | Salida |
|---|---|---|---|---|---|---|
| I1 | informe → coordinador | – | 0.0232 | 83 | I1.md | informe.pdf |
| I2 | informe → coordinador | – | 0.0184 | 113 | I2.md | informe.pdf |
| I3 | informe → coordinador | – | 0.0183 | 84 | I3.md | informe.pdf |

## Total

- **28 casos · US$ 0.1460 · 185 s de reloj** (de a 5 en paralelo)
- Chequeos: 17 de 17 de trabajo · 4 de 4 de la reserva

Los informes, calificados con `evaluacion/chequeos_informes.py` (6 chequeos de contenido cada uno): **16 de 18**. No pasaron: I2 no dice el desvío total, e I3 lleva una cita [Cn] en el título. Varía entre corridas: con el diseño anterior, en 6 corridas, 95 de 108 (88 %, [comparación de versiones](comparacion_informes.md)); una corrida de la 18 de 18 (sus PDF están en [`docs/informes/`](../docs/informes/)) y otra 14 de 18.
