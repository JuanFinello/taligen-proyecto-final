# El agente sobre el año simulado (decisión 90)

Comando: `.venv/bin/python pruebas/agente_anio.py` · base: el AF2027 simulado (decisión 88) · US$ 0.067

**9 de 10** pasan los chequeos por código.

| Caso | Qué prueba | Tipo → camino | Chequeo |
|---|---|---|---|
| total | el AF2027 completo | puntual → agente | ✓  |
| comparables | comparables con una sucursal que cerró | comparativa → agente | ✓  |
| mascotas | la categoría nueva | puntual → agente | ✓  |
| precio | el aumento de precios (y el efecto mix) | comparativa → agente | ✓  |
| marca_propia | el cambio de mix | comparativa → agente | ✓  |
| caida | una caída de −30 % (segundo oráculo) | diagnostico → coordinador | ✓ variación en [-25.5, -17.4]: sí, -20.36 |
| corte | una región sin ventas tres días | diagnostico → coordinador | ✗ encuentra los días sin ventas · no dice lo esperado |
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

**total.** ¿Cuánto vendimos en el AF2027? (9 s)

> En el AF2027 (mayo de 2026 a abril de 2027), las ventas netas de Almacenes del Sur fueron de $10.298.309.220,5 (ARS). Es el período completo, ya que la base llega hasta el 30 de abril de 2027.

**comparables.** ¿Cómo vinieron las ventas del AF2027 contra el AF2026 en sucursales comparables? (13 s)

> En sucursales comparables, las ventas netas del AF2027 (mayo 2026 a abril 2027) crecieron un 0,35 % frente al AF2026: $9.983.041.834 contra $9.948.072.093, una diferencia de $34.969.741. La variación total de la cadena fue de +1,30 % ($10.298.309.221 contra $10.166.198.308, diferencia de $132.110.913). La diferencia entre ambas cifras se explica por las sucursales que se sumaron después del inicio del AF2026: crecieron en total, pero en comparables la suba es muy baja. El cálculo comparable incluye solo sucursales abiertas antes del 1 de mayo de 2025. No desglosé la variación por región, formato ni sucursal.

**mascotas.** ¿Cuánto vendió la categoría Mascotas en el AF2027? (11 s)

> La categoría Mascotas vendió 59.544.500 ARS en ventas netas en el AF2027 (mayo de 2026 a abril de 2027), que es el año completo disponible en la base.

**precio.** ¿Cómo cambió el precio promedio de Almacén en el T3 del AF2027 contra el T3 del AF2026? (16 s)

> El precio promedio de Almacén subió un 13,85 % en el T3 del AF2027 frente al T3 del AF2026, pasando de $2.181,18 por unidad (nov-2025 a ene-2026) a $2.483,27 por unidad (nov-2026 a ene-2027). Con el criterio comparable (solo sucursales abiertas antes del 1 de noviembre de 2025), la variación es de 13,89 %, con un precio de $2.484,16 por unidad en el AF2027 frente a los mismos $2.181,18 del AF2026. Ambas variaciones son casi iguales, así que la apertura de sucursales no explica la suba. El precio promedio mezcla productos, así que parte del movimiento puede venir de cambios en el mix de ventas y no solo de precios.

**marca_propia.** ¿Cómo vinieron las ventas de marca propia en el T4 del AF2027 contra el T4 del AF2026? (12 s)

> Las ventas netas de marca propia (Del Sur) en el T4 del AF2027 (feb a abr 2027) fueron de $74.463.508, contra $56.100.050 en el T4 del AF2026 (feb a abr 2026). Eso es una suba de $18.363.458, o +32,7 %. En comparables (solo sucursales abiertas antes del inicio del período anterior, feb 2026), las ventas fueron $73.604.068 contra $56.100.050: +31,2 %, es decir $17.504.018 más. La suba total es un poco mayor que la comparable, así que las sucursales nuevas explican una parte del crecimiento, pero la mayor parte viene de las sucursales que ya existían. El desglose por sucursal, región o proveedor no lo incluí porque no lo pediste.

**caida.** ¿Por qué cayeron las ventas de Bebidas en la región Oeste en el T3 del AF2027? (54 s)

> **Las ventas de Bebidas en el Oeste cayeron 20,36 % en el T3 del AF2027 [C1], y la caída fue sobre todo de volumen y de Vinos, que explica el 56,6 % de la caída [C2].**
> 
> - Se vendieron menos unidades y no se cobró distinto: las unidades bajaron 20,79 % [C5] mientras el precio promedio subió 0,55 % [C6].
> - Dentro de Bebidas, la marca Valle Alto explica el 33,9 % de la caída [C3] y la sucursal Sierra Chica el 32,1 % [C4].
> - El quiebre casi no cambió, de 1,25 % a 1,33 % [C8], y en Vinos bajó, así que los faltantes de stock no alcanzan para explicar la caída.
> 
> **Siguiente paso:** La caída es más fuerte en las sucursales que estaban abiertas en los dos períodos, porque la sucursal nueva compensa parte del total, así que conviene tomar esa comparación como la lectura principal. Los datos muestran dónde se concentró la caída, pero no por qué: la base no tiene clientes ni tickets, así que no se puede saber si bajó la cantidad de compradores o el tamaño de cada compra. Lo que sigue es revisar con Valle Alto y con el equipo de Sierra Chica qué pasó con la demanda de vinos en el trimestre, y mirar si las promociones de vinos de ese período alcanzan a explicar la caída.
> 
> Diagnóstico: salidas/anio_agente/caida/diagnostico.md

**corte.** ¿Por qué cayeron las ventas de la región Norte en agosto de 2026? (58 s)

> **La caída de ventas del Norte en agosto de 2026 fue de volumen, no de precio ni de altas de sucursales, pero los datos no alcanzan para explicar por qué se vendieron menos unidades [C2][C6].**
> 
> - Las ventas netas bajaron 8,15 % frente a agosto de 2025 [C2], y la caída es igual en sucursales comparables, así que no viene de locales nuevos.
> - Las unidades vendidas bajaron 7,77 % [C5] mientras el precio promedio apenas cambió 0,41 % [C6], por lo que se vendió menos cantidad y no a otro precio.
> - La caída se concentró en hiper y super, y en Frescos, Perfumería, Limpieza y Lácteos [C3][C4], y el quiebre de stock no parece la causa: subió apenas 0,20 pp [C7].
> 
> **Siguiente paso:** Conviene revisar con comercial y compras qué cambió en el Norte en agosto de 2026 frente al año anterior: promociones y precios de la competencia en las subcategorías de Frescos, Perfumería, Limpieza y Lácteos, y la disponibilidad de los proveedores con más quiebre, cuyo stock también bajó. Como la base no tiene datos de clientes ni de tickets, la causa de fondo hay que buscarla con otras fuentes.
> 
> Diagnóstico: salidas/anio_agente/corte/diagnostico.md

**discontinuado.** ¿Por qué dejó de venderse Detergente concentrado Espuma Clara 500 ml (P0168) desde enero de 2027? (66 s)

> **Los datos no alcanzan para explicar la causa: P0168 no tiene ventas desde enero de 2027 [C3], y ni el quiebre ni las promociones lo explican [C2] [C9].**
> 
> - Las ventas no se cortaron de golpe: entre agosto y diciembre se mantuvieron entre 838.440 y 991.880 ARS por mes [C1], con una baja en septiembre que se recuperó en octubre.
> - La tasa de quiebre fue de 0 % desde octubre [C2], y no hubo promociones sobre la subcategoría entre diciembre y abril [C9], así que ni el stock ni los descuentos explican el corte.
> - La subcategoría Detergentes cayó 9,84 % en comparables [C14] y el proveedor Química Hogar S.A. 7,31 % [C15], por lo que el fin de P0168 se da dentro de una baja más general del rubro.
> 
> **Siguiente paso:** Confirmar con compras o abastecimiento si el producto fue descontinuado, reemplazado por otro código o si se dejó de pedir al proveedor, porque eso no está en la base. Revisar también el stock del producto en el último tramo del período, que no fue consultado.
> 
> Diagnóstico: salidas/anio_agente/discontinuado/diagnostico.md

**quiebre.** ¿Por qué cayeron las ventas de Jabón para ropa en la sucursal Almacenes del Sur Villa Marina en marzo de 2027? (50 s)

> **Las ventas cayeron 55,5 % por vender menos unidades, no por precio, y el dato apunta a un quiebre de stock en marzo como causa probable, aunque los datos no lo prueban del todo [C1][C2].**
> 
> - El precio casi no se movió: el precio promedio varió −0,13 % [C4].
> - En marzo la tasa de quiebre de la subcategoría llegó a 60 % [C6], contra 0 % en el mismo mes del año anterior [C7].
> - Febrero estuvo en 0 % y abril en 3,6 % [C9], y la única promoción de la subcategoría empezó recién a fin de marzo, así que no alcanza para explicar el quiebre [C8].
> 
> **Siguiente paso:** Confirmar con abastecimiento y con quien carga el stock de Villa Marina si hubo faltantes reales en marzo o un error de registro. La base no permite ver si cambiaron los compradores o su gasto por compra, así que conviene revisarlo aparte antes de concluir.
> 
> Diagnóstico: salidas/anio_agente/quiebre/diagnostico.md

**cierre.** ¿Qué pasó con las ventas de la sucursal Almacenes del Sur Monte Chico en 2027? (45 s)

> **No se puede medir qué pasó con las ventas de Monte Chico en 2027 porque su última venta fue a fines de 2026 [C3].**
> 
> - La cadena tiene ventas hasta abril de 2027, pero Monte Chico solo hasta fines de 2026 [C8].
> - En el mismo tramo del año anterior vendió ARS 64.503.356 [C1], y sin ventas en el período la variación y el desvío contra presupuesto quedan sin valor [C1][C4].
> - Con estos datos no se puede afirmar si la caída se debe a un cierre, a un problema de carga o a otra causa; eso sería una interpretación que hay que verificar.
> 
> **Siguiente paso:** Confirmar con Sucursales si Monte Chico cerró o si faltan cargar sus ventas de 2027, y solo después analizar la demanda, el stock o las categorías.
> 
> Diagnóstico: salidas/anio_agente/cierre/diagnostico.md


## Lectura (escrita después de correr)

- **Números: 5 de 5 exactos.** El de precio aclara solo que el precio promedio mezcla productos (efecto mix): +13,85 %, con +15 % de precio de lista.
- **Comparables con una sucursal cerrada:** el agente da +0,35 %, que es lo que el sistema calcula; sin S07, que cerró, sería +1,04 %. Lo explica mal («sucursales que se sumaron»), porque la base no sabe del cierre. El límite del diseño de la decisión 88 tiene un costo concreto: subestima el crecimiento comparable en 0,7 pp.
- **El corte del Norte no lo encontró** (el único ✗): atribuye la caída (−8,15 %, casi exactamente 3 días de 31) a menos volumen, sin mirar los días. La guía del diagnóstico manda mirar stock y promociones ante una caída, pero no si faltan días.
- **Discontinuado, quiebre y cierre, bien:** no confunde el discontinuado con un quiebre y pide confirmar con compras; encuentra el quiebre (60 % del mes); y del cierre dice que no puede saber si cerró o faltan cargas, y pide confirmarlo con Sucursales. No inventa.
- **El segundo oráculo destapó un límite del generador:** la caída plantada se mide en −30,9 % contra el AF2025 × crecimiento, pero en −20,4 % contra el AF2026 real. El AF2026 tuvo una caída real del Oeste (−5,7 % en el año, −7,2 % en Bebidas del T3) que el generador no repite, porque copia el AF2025 con un solo crecimiento para toda la cadena. La concentración que describe el agente (Vinos, Valle Alto, Sierra Chica) sale de comparar contra esa caída real, no del evento plantado, que fue parejo.

## Costo

US$ 0,067 · 88 llamadas · 408 s (`registro.py --todas`, corrida «fase 4 agente año simulado»).
