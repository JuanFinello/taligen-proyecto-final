# Test 7: conversación (decisión 118)

Comando: `.venv/bin/python evaluacion/robustez/conversacion.py --veces 3` · 8 conversaciones de 3 turnos × 3 · US$ 0.075 · 149 s

**Turnos correctos: 69 de 72** · conversaciones enteras: 21 de 24

## Por grupo

| Grupo | Turnos 2 y 3 (los que dependen de la conversación) |
|---|---|
| reemplazar | 6 de 6 |
| sumar | 6 de 6 |
| quitar | 6 de 6 |
| referencia | 9 de 12 |
| corregir | 6 de 6 |
| cambio de tema con aviso | 6 de 6 |
| cambio de tema sin aviso | 6 de 6 |

## Cada conversación

| Conv. | Grupo | Turno | Pregunta | Esperado | Corridas |
|---|---|---|---|---|---|
| V1 | reemplazar | 1 | ¿Cuánto vendió Perfumería en el AF2026? | ventas_netas 1.309.106.714,00 | ✓✓✓ |
|  |  | 2 | ¿Y Bebidas? | ventas_netas 2.204.512.773,00 | ✓✓✓ |
|  |  | 3 | ¿Y en unidades? | unidades 599.124,00 | ✓✓✓ |
| V2 | sumar | 1 | ¿Cuánto vendió Bebidas en el AF2025? | ventas_netas 2.116.705.185,50 | ✓✓✓ |
|  |  | 2 | ¿Y solo en la región Norte? | ventas_netas 618.938.405,50 | ✓✓✓ |
|  |  | 3 | ¿Y de eso, solo Gaseosas? | ventas_netas 105.810.449,00 | ✓✓✓ |
| V3 | quitar | 1 | ¿Cuánto vendió Lácteos en la región Sur en abril de 2026? | ventas_netas 24.318.340,00 | ✓✓✓ |
|  |  | 2 | ¿Y en todas las regiones? | ventas_netas 113.746.490,00 | ✓✓✓ |
|  |  | 3 | ¿Y sumando todas las categorías? | ventas_netas 820.168.520,00 | ✓✓✓ |
| V4 | referencia | 1 | ¿Qué sucursal vendió más en el AF2026? | ventas_netas S02 | ✓✓✓ |
|  |  | 2 | ¿Y cuánto vendió esa sucursal en el AF2025? | ventas_netas 926.787.929,50 | ✓✓✓ |
|  |  | 3 | ¿Qué margen tuvo en el AF2026? | margen_pct 26,77 | ✓✓✓ |
| V5 | referencia | 1 | ¿Cuánto vendió Almacén en marzo de 2026? | ventas_netas 122.322.260,00 | ✓✓✓ |
|  |  | 2 | ¿Y en el mes anterior? | ventas_netas 100.386.170,00 | ✓✓✓ |
|  |  | 3 | ¿Y un año antes? | ventas_netas 96.964.860,00 | ✗✗✗ |
| V6 | corregir | 1 | ¿Cuántas unidades vendió la región Centro en enero de 2026? | unidades 75.061,00 | ✓✓✓ |
|  |  | 2 | Perdón, quise decir la región Sur. | unidades 61.120,00 | ✓✓✓ |
|  |  | 3 | ¿Y en pesos? | ventas_netas 214.140.897,00 | ✓✓✓ |
| V7 | cambio de tema con aviso | 1 | ¿Qué margen tuvo Frescos en la región Centro en el AF2025? | margen_pct 28,10 | ✓✓✓ |
|  |  | 2 | Otra cosa: ¿cuántas sucursales tiene la región Sur? | sucursales_abiertas 10,00 | ✓✓✓ |
|  |  | 3 | ¿Cuánto vendió la cadena en diciembre de 2025? | ventas_netas 980.316.128,50 | ✓✓✓ |
| V8 | cambio de tema sin aviso | 1 | ¿Qué margen bruto en pesos tuvo Almacén en el T3 del AF2026? | margen_bruto 81.601.891,95 | ✓✓✓ |
|  |  | 2 | ¿Cuánto vendió la sucursal S11 en enero de 2026? | ventas_netas 75.414.116,00 | ✓✓✓ |
|  |  | 3 | ¿Y en febrero? | ventas_netas 64.943.653,00 | ✓✓✓ |

## Los turnos que fallaron: por qué y qué respondió

**V5, corrida 1, turno 3**: usó ventas_netas, pero no dio 96964860.0

> En marzo de 2025, la categoría Almacén vendió $118.887.750 en ventas netas. Frente a marzo de 2026 ($122.322.260), la variación total es de +2,89 % (diferencia de $3.434.510). En comparables, es decir, solo con las sucursales abiertas desde antes de marzo de 2025, marzo de 2026 vendió $119.115.830 y la variación es de +0,19 % (diferencia de $228.080). Casi todo el crecimiento total viene de sucursales que no estaban abiertas un año antes.

**V5, corrida 2, turno 3**: usó ventas_netas, pero no dio 96964860.0

> En marzo de 2025, la categoría Almacén vendió $118.887.750 en ventas netas. Frente a ese mes, marzo de 2026 ($122.322.260) tuvo una variación total de +2,89 % (diferencia de $3.434.510). Esta es la variación total, no la comparable por mismas sucursales.

**V5, corrida 3, turno 3**: usó ventas_netas, pero no dio 96964860.0

> En marzo de 2025, la categoría Almacén vendió ARS 118.887.750 en ventas netas. Contra esa cifra, marzo de 2026 (ARS 122.322.260) subió ARS 3.434.510, una variación total de +2,89 %. En comparables (solo las sucursales abiertas antes del 1 de marzo de 2025), la variación es de +0,19 % (ARS 228.080 más: ARS 119.115.830 frente a ARS 118.887.750). Es decir, casi todo el crecimiento total viene de sucursales abiertas después de marzo de 2025.


## Nota sobre esta medición

- **Corrección del chequeo después de la primera corrida.** La primera corrida dio 66 de 72 (`salidas/conversacion/resultado_1_sin_fila.md`). Tres de esas fallas eran del test, no del agente: en V2 t3 y V4 t3 el agente agrupó (por subcategoría o por sucursal) en vez de filtrar y dio el número correcto, pero los chequeos no tenían `fila` (decisión 37), que el evaluador usa justamente para aceptar la fila que corresponde de una consulta agrupada. Se agregó `fila` (la del filtro más específico) y se volvió a correr. La fila sola no alcanza: tiene que dar además el valor esperado, así que un filtro arrastrado o perdido sigue fallando.
- **V5 t3 («¿Y un año antes?») falla las 3 veces, siempre de la misma manera.** El turno 2 habló de febrero de 2026, pero el agente vuelve al período del turno 1 y compara marzo de 2026 con marzo de 2025, sin declararlo como supuesto. Se cuenta como falla: la referencia es lo último que se nombró. Se puede discutir que la frase es ambigua, pero entonces lo correcto habría sido preguntar o declarar el supuesto, y el agente no hizo ninguna de las dos cosas. Es una medición: se reporta, no se ajusta.
