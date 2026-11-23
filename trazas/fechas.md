# Test 3: fechas difíciles (decisión 96)

Comando: `.venv/bin/python evaluacion/robustez/fechas.py --veces 3` · 14 preguntas × 3 · US$ 0.049 · 75 s · base hasta el 30-04-2026, hoy noviembre de 2026

**42 de 42** pasan.

| Caso | Grupo | Pregunta | Pasa si… | Esperado (SQL a mano) | Resultado |
|---|---|---|---|---|---|
| F01 | relativa | ¿Cuánto vendimos el último mes? | da ese número | $ 820.168.520 | 3/3 |
| F02 | relativa | ¿Cuánto vendimos el mes pasado? | cuenta desde el último dato y lo dice, o dice que no hay datos | $ 820.168.520 | 3/3 |
| F03 | relativa | ¿Cuánto llevamos vendido en este año fiscal? | cuenta desde el último dato y lo dice, o dice que no hay datos | $ 10.166.198.308 | 3/3 |
| F04 | borde fiscal | ¿Cuánto vendimos en el primer mes del AF2026? | da ese número | $ 819.151.102 | 3/3 |
| F05 | borde fiscal | ¿Cuánto vendimos en el AF2026 hasta octubre inclusive? | da ese número | $ 4.873.510.850 | 3/3 |
| F06 | borde fiscal | ¿Cuánto vendimos en el último mes del AF2025? | da ese número | $ 790.780.507 | 3/3 |
| F07 | ambigua | ¿Cuánto vendimos el año pasado? | da las lecturas o declara la elegida | $ 10.022.848.969 o $ 9.747.823.869 | 3/3 |
| F08 | ambigua | ¿Cuánto vendimos en abril? | da las lecturas o declara la elegida | $ 820.168.520 o $ 790.780.507 | 3/3 |
| F09 | ambigua | ¿Cuánto vendimos en el T2 de 2025? | da las lecturas o declara la elegida | $ 2.384.401.775 o $ 2.475.903.842 o $ 2.361.796.421 | 3/3 |
| F10 | rango | ¿Cuánto vendimos en la primera quincena de marzo de 2026? | da ese número | $ 426.328.121 | 3/3 |
| F11 | rango | ¿Cuánto vendimos entre el 10 y el 20 de enero de 2026? | da ese número | $ 329.754.904 | 3/3 |
| F12 | fuera de la base | ¿Cuánto vendimos ayer? | cuenta desde el último dato y lo dice, o dice que no hay datos | $ 25.904.360 | 3/3 |
| F13 | fuera de la base | ¿Cuánto vendimos en el AF2027? | dice que no hay datos, sin otro número | — | 3/3 |
| F14 | fuera de la base | ¿Cuánto vendimos en marzo de 2024? | dice que no hay datos, sin otro número | — | 3/3 |

## Por grupo

| Grupo | Pasan |
|---|---|
| relativa | 9 de 9 |
| borde fiscal | 9 de 9 |
| ambigua | 9 de 9 |
| rango | 6 de 6 |
| fuera de la base | 9 de 9 |

## Respuestas (primera corrida, y todas las que fallaron)

**F01 (1) ✓** ¿Cuánto vendimos el último mes?

> En el último mes de la base (abril de 2026, del 1 al 30 de abril) vendimos ventas netas por $820.168.520 ARS.
> *Supuestos:* Tomé «el último mes» como abril de 2026, el último mes completo de la base (cobertura hasta el 30/04/2026), en calendario y no en mes fiscal. · «Vendimos» se leyó como ventas netas (brutas menos descuentos y devoluciones).

**F02 (1) ✓** ¿Cuánto vendimos el mes pasado?

> En abril de 2026 (el último mes completo de la base, que llega hasta el 30/04/2026) vendimos ventas netas por $820.168.520 ARS.
> *Supuestos:* «El mes pasado» se tomó como abril de 2026, último mes con datos en la base, y no como el mes calendario anterior a la fecha de hoy. · Ventas se toma como ventas netas (brutas menos descuentos y devoluciones), en calendario mensual.

**F03 (1) ✓** ¿Cuánto llevamos vendido en este año fiscal?

> En el año fiscal 2026 (mayo de 2025 a abril de 2026, que es el último año fiscal completo de la base) llevamos vendidos $10.166.198.308 en ventas netas.
> *Supuestos:* «Este año fiscal» tomado como AF2026, ya que la base llega hasta el 30/04/2026 y ese año está completo. · Ventas en su acepción neta (brutas menos descuentos y devoluciones).

**F04 (1) ✓** ¿Cuánto vendimos en el primer mes del AF2026?

> En el primer mes del AF2026 (mayo de 2025) vendimos ARS 819.151.102,50 en ventas netas.
> *Supuestos:* Tomé el primer mes del AF2026 como mayo de 2025 (mes_fiscal 1, del 1 al 31 de mayo de 2025), ya que el año fiscal empieza el 1 de mayo. · Ventas interpretadas como ventas netas (brutas menos descuentos y devoluciones).

**F05 (1) ✓** ¿Cuánto vendimos en el AF2026 hasta octubre inclusive?

> Las ventas netas del AF2026 hasta octubre inclusive (mayo a octubre de 2025) fueron de $4.873.510.850.
> *Supuestos:* AF2026 hasta octubre inclusive se tomó como mayo a octubre de 2025 (meses fiscales 1 a 6), y «ventas» como ventas netas.

**F06 (1) ✓** ¿Cuánto vendimos en el último mes del AF2025?

> En el último mes del AF2025 (abril de 2025) las ventas netas fueron de $790.780.507. Por región: Norte $238.384.700 (30,1 %), Centro $225.308.296 (28,5 %), Sur $181.279.972 (22,9 %) y Oeste $145.807.539 (18,4 %).
> *Supuestos:* El último mes del AF2025 se tomó como abril de 2025 (mes fiscal 12, del 1 al 30 de abril), ya que el AF2025 va de mayo de 2024 a abril de 2025. · «Vendimos» se leyó como ventas netas (brutas menos descuentos y devoluciones).

**F07 (1) ✓** ¿Cuánto vendimos el año pasado?

> Ventas netas del año pasado: si por «el año pasado» entendés el año calendario 2025 (enero a diciembre de 2025), vendimos $10.022.848.969. Si entendés el año fiscal 2025 (AF2025, de mayo de 2024 a abril de 2025), vendimos $9.747.823.869. Ambos períodos están completos en la base. Decime cuál querés y puedo abrirlo por sucursal, región, categoría o mes.
> *Supuestos:* Tomé «el año pasado» como el año calendario 2025 (enero a diciembre de 2025) como lectura principal, y también informo el año fiscal 2025 (mayo de 2024 a abril de 2025).

**F08 (1) ✓** ¿Cuánto vendimos en abril?

> En abril de 2026 vendimos $820.168.520 en ventas netas (brutas menos descuentos y devoluciones). Tomé abril de 2026 porque es el último abril completo de la base, que cubre hasta el 30 de abril de 2026.
> *Supuestos:* «Abril» se interpretó como abril de 2026 (último mes completo de la base). Si querías abril de 2025, decímelo y lo calculo.

**F09 (1) ✓** ¿Cuánto vendimos en el T2 de 2025?

> Las ventas netas del T2 del año fiscal 2025 (agosto a octubre de 2024) fueron $2.361.796.421. Como «T2 de 2025» admite otras lecturas, también calculé: el T2 del año fiscal 2026 (agosto a octubre de 2025) fue $2.475.903.842,50, y el segundo trimestre calendario de 2025 (abril a junio) fue $2.384.401.775. Si te referías a otro de estos períodos, decime cuál y lo ajusto.
> *Supuestos:* Tomé «T2 de 2025» como T2 del año fiscal 2025 (agosto a octubre de 2024), por la convención fiscal de nombrar el año por el año en que termina. · Informé también el T2 del año fiscal 2026 (agosto a octubre de 2025) y el segundo trimestre calendario de 2025 (abril a junio), por ser lecturas posibles de la misma frase. · Ventas en el sentido de ventas netas (brutas menos descuentos y devoluciones).

**F10 (1) ✓** ¿Cuánto vendimos en la primera quincena de marzo de 2026?

> En la primera quincena de marzo de 2026 (del 1 al 15) las ventas netas de la cadena fueron de $426.328.121.
> *Supuestos:* Se tomaron las ventas netas (brutas menos descuentos y devoluciones), que es la lectura por defecto de «ventas», y se consideró la quincena como los días 1 a 15 de marzo de 2026, inclusive.

**F11 (1) ✓** ¿Cuánto vendimos entre el 10 y el 20 de enero de 2026?

> Entre el 10 y el 20 de enero de 2026 (ambos días incluidos) las ventas netas de la cadena fueron de $329.754.904,50 ARS. Son ventas netas: brutas menos descuentos y devoluciones. El día de mayor venta fue el 10 de enero, con $40.364.610 ARS, y el de menor, el 12 de enero, con $25.065.750 ARS.
> *Supuestos:* Se tomó el período como 10 y 20 de enero de 2026 inclusive, y «ventas» como ventas netas.

**F12 (1) ✓** ¿Cuánto vendimos ayer?

> Ayer (30/04/2026, último día con datos en la base) vendimos $25.904.360 en ventas netas en toda la cadena.
> *Supuestos:* Tomé «ayer» como el 30/04/2026, último día con datos en la base, y no la fecha de hoy. · Ventas = ventas netas (brutas menos descuentos y devoluciones), toda la cadena sin abrir por sucursal.

**F13 (1) ✓** ¿Cuánto vendimos en el AF2027?

> No hay datos para el AF2027: la base de ventas cubre del 1 de mayo de 2024 al 30 de abril de 2026, y el AF2027 empieza en mayo de 2026. Si te sirve, puedo consultar el período más cercano que sí está en la base.

**F14 (1) ✓** ¿Cuánto vendimos en marzo de 2024?

> No tenemos datos de marzo de 2024 para responder. La base de ventas arranca el 1 de mayo de 2024 (cobertura hasta el 30 de abril de 2026), así que ese mes no está cargado. La consulta devolvió vacío, no cero. Si necesitás, puedo calcular las ventas netas de mayo de 2024 en adelante.
> *Supuestos:* Interpreté «marzo de 2024» como el mes calendario de marzo de 2024.


## Lectura (escrita después de correr, con la decisión 102)

Esta corrida es con el criterio nuevo del glosario («un año escrito solo se responde con las dos lecturas, calendario y fiscal»): **42 de 42**. Las ambiguas siguen pasando 9 de 9. La F09, que antes fallaba por el chequeo (dos lecturas sacadas de una consulta agrupada), esta vez pasó las 3. Fuera de la base, 9 de 9, como con la decisión 97.
