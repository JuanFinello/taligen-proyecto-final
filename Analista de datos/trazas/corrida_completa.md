# Traza: la corrida completa con un comando (semana 6)

Corrida 20261117-164745-0a72 del 17-11-2026. Versión del diseño `99c4b2` · `claude-haiku-5-5` · para repetirla: `.venv/bin/python correr_todo.py`

Chequeo: ✓/✗ contra `esperados.yaml` (R = reserva, decisión 80: no se ajusta nada por ellas); – = sin chequeo numérico (diagnósticos e informes: se leen). Segundos: reloj de cada caso.

## Preguntas · US$ 0.0539

| Caso | Tipo → camino | Chequeo | US$ | Segundos | Salida |
|---|---|---|---|---|---|
| P01 | puntual → agente | ✓ | 0.0005 | 7 | – |
| P02 | puntual → agente | ✓ | 0.0009 | 5 | – |
| P03 | puntual → agente | ✓ | 0.0013 | 9 | – |
| P04 | puntual → agente | ✓ | 0.0009 | 5 | – |
| P05 | puntual → agente | ✓ | 0.0011 | 5 | – |
| P06 | comparativa → agente | ✓ | 0.0016 | 9 | – |
| P07 | comparativa → agente | ✓ | 0.0028 | 15 | – |
| P08 | comparativa → agente | ✓ | 0.0015 | 8 | – |
| P09 | puntual → agente | ✓ (R) | 0.0015 | 7 | – |
| P10 | ranking → agente | ✓ | 0.0012 | 6 | – |
| P11 | ranking → agente | ✓ | 0.0012 | 7 | – |
| P12 | ranking → agente | ✓ (R) | 0.0022 | 12 | – |
| P13 | diagnostico → coordinador | – | 0.0063 | 39 | diagnostico.md |
| P14 | diagnostico → coordinador | – | 0.0100 | 49 | diagnostico.md |
| P15 | diagnostico → coordinador | – | 0.0064 | 29 | diagnostico.md |
| P16 | diagnostico → coordinador | – | 0.0104 | 46 | diagnostico.md |
| P17 | ambigua → agente | ✓ | 0.0012 | 7 | – |
| P18 | ambigua → agente | ✓ (R) | 0.0012 | 7 | – |
| P19 | sin_dato → agente | ✓ (R) | 0.0009 | 5 | – |
| P20 | sin_dato → agente | ✓ | 0.0008 | 4 | – |

## Conversaciones · US$ 0.0189

| Caso | Tipo → camino | Chequeo | US$ | Segundos | Salida |
|---|---|---|---|---|---|
| C1 | comparativa → agente · comparativa → agente · ranking → agente | ✓ | 0.0041 | 22 | – |
| C2 | puntual → agente · comparativa → agente · ranking → agente | ✓ | 0.0049 | 28 | – |
| C3 | puntual → agente · comparativa → agente · comparativa → agente | ✓ | 0.0036 | 22 | – |
| C4 | puntual → agente · puntual → agente · puntual → agente | ✓ | 0.0034 | 20 | – |
| C5 | ambigua → agente · puntual → agente · puntual → agente | ✓ | 0.0029 | 18 | – |

## Informes · US$ 0.0319

| Caso | Tipo → camino | Chequeo | US$ | Segundos | Salida |
|---|---|---|---|---|---|
| I1 | informe → coordinador | – | 0.0174 | 56 | informe.pdf |
| I2 | informe → coordinador | – | 0.0065 | 49 | informe.pdf |
| I3 | informe → coordinador | – | 0.0081 | 43 | informe.pdf |

## Total

- **28 casos · US$ 0.1047 · 120 s de reloj** (de a 5 en paralelo)
- Chequeos: 17 de 17 de trabajo · 4 de 4 de la reserva

Las salidas (trazas por caso, diagnósticos y PDF) quedan en `salidas/completa-<corrida>/`, que no se commitea.

Leído a mano: los diagnósticos y P15, P13, P16, I1 e I3 están bien. **I2 tiene un problema**: atribuye al Sur un desvío de −53,71 % en enero, que es el error de carga del presupuesto (Perfumería, Sur, ene-2026, ×10; decisión 6), sin decirlo. P14 encontró el quiebre de stock, pero esta vez no lo atribuyó al proveedor (en la corrida de la decisión 79, sí).
