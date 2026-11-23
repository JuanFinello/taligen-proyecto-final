# El agente sobre el año simulado (decisión 90)

Comando: `.venv/bin/python evaluacion/robustez/agente_anio.py` · base: el AF2027 simulado (decisión 88) · US$ 0.076

**10 de 10** pasan los chequeos por código.

| Caso | Qué prueba | Tipo → camino | Chequeo |
|---|---|---|---|
| total | el AF2027 completo | puntual → agente | ✓  |
| comparables | comparables con una sucursal que cerró | comparativa → agente | ✓  |
| mascotas | la categoría nueva | puntual → agente | ✓  |
| precio | el aumento de precios (y el efecto mix) | comparativa → agente | ✓  |
| marca_propia | el cambio de mix | comparativa → agente | ✓  |
| caida | una caída de −30 % (segundo oráculo) | diagnostico → coordinador | ✓ variación en [-25.5, -17.4]: sí, -20.36 |
| corte | una región sin ventas tres días | diagnostico → coordinador | ✓ encuentra los días sin ventas |
| discontinuado | un producto discontinuado (no es un quiebre) | diagnostico → coordinador | ✓ no lo atribuye a un quiebre |
| quiebre | un quiebre de stock | diagnostico → coordinador | ✓ encuentra el quiebre |
| cierre | una sucursal que cerró (la base no lo sabe) | diagnostico → coordinador | ✓ ve que no vende desde enero |

## Valores esperados (SQL a mano, guardados antes de correr)

- Ventas AF2027: $ 10.298.309.220,50
- Comparables AF2027 contra AF2026: **0,3515 %** como las define el sistema (incluye a S07, que cerró el 2027-01-01); **1,0361 %** sin ella; todas: 1,2995 %
- Precio promedio de Almacén, T3 contra T3: 13,8497 % (se plantó +15 % de precio de lista)
- Marca propia, T4 contra T4: 32,7334 %
- Caída de Bebidas en el Oeste, T3 contra T3: -20,3578 % (comparables: -22,4915 %)
- **Segundo oráculo**: se plantó −30 %; contra lo que habría sido sin el evento se mide **-30,92 %**

## Respuestas

**total.** ¿Cuánto vendimos en el AF2027? (12 s)

> Las ventas netas del AF2027 (mayo de 2026 a abril de 2027) fueron de $10.298.309.220,50. Frente al AF2026 ($10.166.198.308,00), subieron $132.110.912,50, es decir +1,30 %. Con solo las sucursales comparables (abiertas antes del 1/5/2025), las ventas fueron de $9.983.041.833,50 contra $9.948.072.093,00 del AF2026: +0,35 %. La mayor parte de la suba total viene de las sucursales nuevas; las comparables crecieron muy poco.

**comparables.** ¿Cómo vinieron las ventas del AF2027 contra el AF2026 en sucursales comparables? (16 s)

> En sucursales comparables, las ventas netas del AF2027 (mayo 2026 a abril 2027) fueron de $9.983.041.833,50 contra $9.948.072.093 del AF2026. La diferencia es de $34.969.740,50, una variación de +0,35 %. Si se cuentan todas las sucursales, la variación total fue de +1,30 %: $10.298.309.220,50 contra $10.166.198.308, con una diferencia de $132.110.912,50. Las comparables son las sucursales abiertas antes del 1 de mayo de 2025 y con ventas en todo el período y en su año anterior. Como la diferencia total es mayor que la de las comparables, las sucursales que no entran en esa comparación también contribuyeron a la suba total.

**mascotas.** ¿Cuánto vendió la categoría Mascotas en el AF2027? (7 s)

> La categoría Mascotas vendió $59.544.500 en ventas netas en el AF2027 (mayo de 2026 a abril de 2027, año completo según la cobertura de la base).

**precio.** ¿Cómo cambió el precio promedio de Almacén en el T3 del AF2027 contra el T3 del AF2026? (13 s)

> El precio promedio de la categoría Almacén fue de 2.483,27 ARS por unidad en el T3 del AF2027 (nov 2026 a ene 2027), contra 2.181,18 ARS en el T3 del AF2026 (nov 2025 a ene 2026). La variación total es de 13,85 %. Con comparables (mismas sucursales, abiertas antes del 1 de noviembre de 2025), el precio pasa a 2.484,16 ARS y la variación es de 13,89 %. Las dos lecturas dan prácticamente lo mismo, así que el cambio no se explica por sucursales nuevas. El precio promedio mezcla productos, por lo que parte de la suba puede venir de un cambio en el mix de lo vendido; no lo separé porque no consulté ese efecto.

**marca_propia.** ¿Cómo vinieron las ventas de marca propia en el T4 del AF2027 contra el T4 del AF2026? (12 s)

> Las ventas netas de marca propia (Del Sur) en el T4 del AF2027 (feb a abr 2027) fueron de $74.463.508, contra $56.100.050 en el T4 del AF2026 (feb a abr 2026): +32,7 % total, unos $18.363.458 más. En comparables (solo sucursales abiertas antes del inicio del período anterior, el 1 de feb de 2026) la variación es de +31,2 %, unos $17.504.018 más, con ventas de $73.604.068 contra $56.100.050. La diferencia entre total y comparables es chica, así que el crecimiento no depende de las aperturas. Los días con ventas casi no cambiaron (3.496 contra 3.502 sucursal-días, -0,2 %), por lo que no hay días faltantes que expliquen la suba.

**caida.** ¿Por qué cayeron las ventas de Bebidas en la región Oeste en el T3 del AF2027? (69 s)

> **Los datos no alcanzan para explicar la caída de 20,4 % en Bebidas del Oeste: no se debe a días sin ventas ni a faltantes de stock, y bajó en todas las subcategorías [C1][C7].**
> 
> - En las mismas sucursales, los días con ventas pasaron de 920 a 919, así que no hubo cierres ni cargas incompletas [C4].
> - En sucursales comparables la caída fue de 23,7 % [C3], así que no se explica por aperturas ni cierres.
> - Vinos explica el 56,6 % de la caída [C7] y bajó 20,4 % [C7], mientras que los quiebres subieron apenas 0,09 pp [C5] y Vinos bajó en quiebre [C6], así que los faltantes no alcanzan para explicarla.
> 
> **Siguiente paso:** Antes de atribuir la caída a una causa, conviene revisar con Comercial si hubo cambios de precio, competencia o demanda en Vinos y en la región, y cruzarlo con las promociones de noviembre a enero, que se superponen con la caída pero no se pueden medir por separado con estos datos. La base no tiene datos de clientes ni de tickets, así que no se puede saber si cambió la frecuencia de compra.
> 
> Diagnóstico: salidas/anio_agente/caida/diagnostico.md

**corte.** ¿Por qué cayeron las ventas de la región Norte en agosto de 2026? (54 s)

> **La caída de ventas del Norte podría venir en buena parte de 3 días sin ventas por sucursal [C1], pero con los datos no se puede confirmar cuánto de la baja de 8,15 % [C2] se explica solo por eso.**
> 
> - Las ventas netas de las sucursales comparables cayeron 8,15 % frente a agosto de 2025, unos 20,2 millones de ARS menos [C2].
> - Congelados es la subcategoría que más aporta a la caída, con −14,2 % y 3,2 millones de ARS menos [C3].
> - En Desodorantes la tasa de quiebre subió de 0,3 % a 2,5 % [C5], y esa subcategoría no tuvo promociones ni en agosto de 2026 ni en agosto de 2025 [C6][C7].
> 
> **Siguiente paso:** Confirmar con operaciones qué pasó en los días sin ventas de la región Norte (cierre, corte o carga incompleta); si fueron días sin venta real, recalcular la caída sobre días vendidos. Después revisar el stock de Desodorantes, Jabón para ropa y Quesos en la región, porque el quiebre subió en esos productos.
> 
> Diagnóstico: salidas/anio_agente/corte/diagnostico.md

**discontinuado.** ¿Por qué dejó de venderse Detergente concentrado Espuma Clara 500 ml (P0168) desde enero de 2027? (53 s)

> **El detergente Espuma Clara dejó de venderse por completo a partir de enero, y los datos no permiten saber por qué: su último movimiento de venta es de diciembre pasado [C4].**
> 
> - En enero-abril del año pasado el producto vendió $3.712.700 [C1] en 936 días con ventas [C2]; en el mismo período de este año no registra ventas.
> - Diciembre todavía vendió $991.880 [C6], así que la caída es de golpe en enero y no gradual, mientras el resto de la cadena sigue vendiendo [C5].
> - Antes del corte, la tasa de quiebre era de 0,31 % [C7] y el stock promedio de 8,5 unidades [C9]; pero la base no tiene stock ni ventas del producto desde enero, así que no se puede saber si el faltante empeoró ni si el costo o el margen cambiaron [C10].
> 
> **Siguiente paso:** Consultar con compras y el área comercial si el producto fue dado de baja, si cambió de código o si dejó de cargarse en el sistema de ventas y stock. Si hubo baja, conviene decidir si se reemplaza por otro producto de la misma subcategoría y revisar si ese reemplazo ya tiene ventas.
> 
> Diagnóstico: salidas/anio_agente/discontinuado/diagnostico.md

**quiebre.** ¿Por qué cayeron las ventas de Jabón para ropa en la sucursal Almacenes del Sur Villa Marina en marzo de 2027? (62 s)

> **Lo más probable es que la caída de Jabón para ropa en Villa Marina en marzo de 2027 se deba a faltantes de stock, no a menos demanda ni a promociones, aunque los datos no permiten confirmarlo del todo [C7][C10].**
> 
> - Las ventas de la subcategoría cayeron 55,5 % frente a marzo de 2026, sin días faltantes, y el precio casi no se movió, así que se vendieron menos unidades [C1][C5].
> - La tasa de quiebre del mes llegó a 60 % contra 0 % un año antes, y se concentró en las primeras semanas de marzo [C7].
> - Las semanas de quiebre de 100 % coinciden con la caída, mientras que la única promoción del período arranca el 28 de marzo, es de un suavizante y no explica lo ocurrido en esas semanas [C10][C9].
> 
> **Siguiente paso:** Conviene revisar las ventas semanales de jabón en Villa Marina, porque en las últimas semanas de marzo el quiebre volvió a cero y aun así el mes cerró con caída, lo que no se explica solo con faltantes. También hay que ver los pedidos y la reposición de esa subcategoría en febrero y marzo, y comparar con otras sucursales para saber si el problema es local.
> 
> Diagnóstico: salidas/anio_agente/quiebre/diagnostico.md

**cierre.** ¿Qué pasó con las ventas de la sucursal Almacenes del Sur Monte Chico en 2027? (44 s)

> **No se puede medir cuánto cambiaron las ventas de Monte Chico en 2027, porque la sucursal no tiene ventas registradas en enero a abril de 2027 [C1].**
> 
> - En el primer cuatrimestre de 2026 la sucursal facturó 64.503.356 ARS netos [C11], con venta los 120 días del período [C2].
> - Para el mismo período de 2027 no hay días de venta registrados [C2], y la última venta de la sucursal en toda la base es de fines de 2026 [C5].
> - Otras sucursales de la región Norte sí venden en esos meses, por ejemplo Los Ceibos, con 320.188.854 ARS [C10]. Lo que muestran los datos es un corte en la sucursal; si fue un cierre o una carga pendiente es una interpretación que todavía no se puede confirmar.
> 
> **Siguiente paso:** Consultar con operaciones y con el área de sistemas si Monte Chico cerró a fines de 2026 o si la carga de ventas de 2027 está pendiente. Según la respuesta, se recalcula la comparación: si la carga está pendiente, con los datos completos; si cerró, se informa como baja de la sucursal y no como caída de ventas.
> 
> Diagnóstico: salidas/anio_agente/cierre/diagnostico.md


## Lectura (escrita después de correr)

Esta es la segunda corrida, después de la decisión 93 (la medida `dias_con_ventas` y el criterio del glosario «ante una caída de ventas, primero ver si faltan días»). En la primera corrida, antes del cambio, el resultado fue 9 de 10: el corte del Norte falló, porque el agente vio una caída de −8,15 % y la atribuyó a menos volumen sin mirar los días.

- **10 de 10.** El corte ahora se encuentra: «podría venir en buena parte de 3 días sin ventas por sucursal», y pide confirmar con operaciones si fue un cierre, un corte o una carga incompleta.
- **El cierre mejoró:** usa los días con ventas (120 contra 0) y propone cómo recalcular según la respuesta: con los datos completos si la carga está pendiente, o como baja de la sucursal y no como caída de ventas si cerró.
- **Los números, el discontinuado, el quiebre y la caída:** igual que antes.
- **Comparables con una sucursal cerrada:** el sistema sigue dando +0,35 % en vez de +1,04 % sin S07. El criterio nuevo no lo arregla, porque es un límite de la base (decisión 88), no del criterio.
- **Límite del generador** (decisión 90): la caída plantada se mide en −30,9 % contra el AF2025 por el crecimiento, pero en −20,4 % contra el AF2026 real, que tuvo una caída real del Oeste.
