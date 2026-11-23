# Test 6: consistencia, pass^k (decisión 117)

Comando: `.venv/bin/python pruebas/consistencia.py --veces 10` · 21 casos × 10 · US$ 0.405 · 658 s

**De trabajo: 17 de 17 aciertan las 10 veces** · aciertos totales 170 de 170 (pass^1 = 100%, pass^10 = 100%)

**Reserva (no se ajusta nada por ellas): 3 de 4 aciertan las 10 veces** · aciertos totales 39 de 40 (pass^1 = 98%, pass^10 = 75%)

## Curva pass^k

| k | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Trabajo | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| Reserva | 98% | 95% | 92% | 90% | 88% | 85% | 82% | 80% | 78% | 75% |

## Por caso

| Caso | Pregunta | Aciertos | Corridas |
|---|---|---|---|
| P01 | ¿Cuánto vendió la cadena en el año fiscal 2025? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| P02 | ¿Cuántas unidades de Lácteos se vendieron en marzo de 2026? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| P03 | ¿Qué margen bruto tuvo Perfumería en el AF2026? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| P04 | ¿Cuánto se descontó en promociones en diciembre de 2025? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| P05 | ¿Cuántas sucursales tiene hoy la región Oeste? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| P06 | ¿Cuánto crecieron las ventas de Bebidas en el T3 del AF2026 contra el mismo trimestre del año anterior? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| P07 | ¿Cuánto cambió el margen de Almacén en el T2 del AF2026 contra el T2 del AF2025? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| P08 | ¿Cuánto crecieron las ventas de la cadena en el AF2026 en términos comparables? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| P10 | ¿Cuáles fueron las 5 sucursales que más vendieron en el AF2026? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| P11 | ¿Qué 3 proveedores dejaron más margen bruto en pesos en el AF2026? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| P17 | ¿Cuánto vendimos en el último trimestre? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| P20 | ¿Cuántos clientes nuevos tuvimos en marzo de 2026? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| C1 | ¿Cómo vinieron las ventas de Bebidas en el T3 del AF2026 contra el año anterior? → ¿Y en la región Sur? → ¿Qué subcategoría explica la mayor parte de ese crecimiento? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| C2 | ¿Qué margen tuvo Almacén en el T2 del AF2026? → ¿Y en el mismo trimestre del año anterior? → ¿Qué proveedor explica la diferencia? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| C3 | ¿Cuánto vendió la región Oeste en el AF2026? → ¿Cuánto es eso contra el año anterior? → ¿Y si miro solo las sucursales comparables? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| C4 | ¿Cuántas unidades vendió la gaseosa cola Del Sur de 2,25 L en diciembre de 2025? → ¿Y la de Cola Andina? → ¿Hubo alguna promoción de gaseosas ese mes? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| C5 | ¿Cuánto vendimos el último trimestre? → El fiscal. → ¿Y con qué margen? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| P09 (reserva) | ¿Cuál fue el desvío contra presupuesto de la cadena en el T4 del AF2026? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| P12 (reserva) | ¿Qué subcategoría de Perfumería creció más en unidades en el AF2026? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| P18 (reserva) | ¿Cuánto vendió Limpieza en 2025? | 10 de 10 | ✓✓✓✓✓✓✓✓✓✓ |
| P19 (reserva) | ¿Cuál es el ticket promedio de la cadena? | 9 de 10 | ✓✓✓✓✓✓✓✓✓✗ |

## Las que fallaron: por qué y qué respondió

**P19, corrida 10**: ✗ respondió con cifras de otra medida (ventas_netas)

> No puedo calcular el ticket promedio de la cadena: la base no tiene tickets ni transacciones individuales, así que no hay forma de contar cuántas compras hubo. Lo más cercano que sí puedo calcular es el precio promedio (ventas netas por unidad vendida) o las ventas netas por período, por sucursal o por categoría. Si me decís cuál te sirve, lo calculo. Como referencia, las ventas netas de toda la cobertura (de mayo de 2024 a abril de 2026) suman $19.914.022.177, pero eso no es un ticket.

