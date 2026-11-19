# Test 3: fechas difíciles (decisión 96)

Comando: `.venv/bin/python pruebas/fechas.py --veces 3` · 14 preguntas × 3 · US$ 0.044 · 77 s · base hasta el 30-04-2026, hoy noviembre de 2026

**41 de 42** pasan.

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
| F09 | ambigua | ¿Cuánto vendimos en el T2 de 2025? | da las lecturas o declara la elegida | $ 2.384.401.775 o $ 2.475.903.842 o $ 2.361.796.421 | 2/3 |
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
| ambigua | 8 de 9 |
| rango | 6 de 6 |
| fuera de la base | 9 de 9 |

## Respuestas (primera corrida, y todas las que fallaron)

**F01 (1) ✓** ¿Cuánto vendimos el último mes?

> Las ventas netas del último mes (abril de 2026, último mes con datos de la base) fueron de $820.168.520.
> *Supuestos:* Se tomó como «último mes» abril de 2026, contado desde el último dato de la base (30/04/2026), y no desde la fecha de hoy. · Se informan ventas netas (brutas menos descuentos y devoluciones), que es la lectura por defecto de «ventas».

**F02 (1) ✓** ¿Cuánto vendimos el mes pasado?

> En abril de 2026 (el último mes con datos, que cierra el 30/04/2026) vendimos $820.168.520 en ventas netas (brutas menos descuentos y devoluciones).
> *Supuestos:* «El mes pasado» se tomó como abril de 2026, el último mes completo de la base (cobertura hasta el 30/04/2026), no como el mes calendario de la fecha de hoy. · Se informan ventas netas, que es lo que se entiende por «ventas» sin más calificación.

**F03 (1) ✓** ¿Cuánto llevamos vendido en este año fiscal?

> Las ventas netas del año fiscal 2026 (1 de mayo de 2025 a 30 de abril de 2026, año completo según la cobertura de la base) suman $10.166.198.308 (ARS, pesos constantes y sin impuestos).
> *Supuestos:* «Este año fiscal» tomado como AF2026, que es el último año fiscal completo en la base (la cobertura termina el 30/04/2026). · Se informan ventas netas (brutas menos descuentos y devoluciones).

**F04 (1) ✓** ¿Cuánto vendimos en el primer mes del AF2026?

> En el primer mes del AF2026 (mayo de 2025) vendimos ARS 819.151.102,50 en ventas netas.
> *Supuestos:* Tomé el primer mes del AF2026 como mayo de 2025 (año fiscal que empieza el 1 de mayo), y «ventas» como ventas netas (brutas menos descuentos y devoluciones).

**F05 (1) ✓** ¿Cuánto vendimos en el AF2026 hasta octubre inclusive?

> Las ventas netas del AF2026 entre mayo y octubre de 2025 (inclusive) fueron de $4.873.510.850 (ARS). Ese período corresponde a los meses 1 a 6 del año fiscal, del 1 de mayo al 31 de octubre de 2025.
> *Supuestos:* «AF2026 hasta octubre inclusive» se tomó como mayo a octubre de 2025 (meses fiscales 1 a 6), y «ventas» como ventas netas (brutas menos descuentos y devoluciones).

**F06 (1) ✓** ¿Cuánto vendimos en el último mes del AF2025?

> Las ventas netas del último mes del AF2025 (abril de 2025) fueron de $790.780.507. El AF2025 va de mayo de 2024 a abril de 2025, así que su último mes es abril de 2025. Como referencia, las ventas netas de todo el AF2025 sumaron $9.747.823.869.
> *Supuestos:* «Último mes del AF2025» lo tomé como abril de 2025 (mes fiscal 12 del AF2025), con el calendario fiscal de mayo a abril.

**F07 (1) ✓** ¿Cuánto vendimos el año pasado?

> Las ventas netas del año calendario 2025 (1 de enero a 31 de diciembre de 2025) fueron de $10.022.848.969. Si con «el año pasado» te referís al año fiscal 2025 (1 de mayo de 2024 a 30 de abril de 2025), las ventas netas fueron de $9.747.823.869.
> *Supuestos:* Tomé «el año pasado» como el año calendario 2025. Como alternativa, di también el año fiscal AF2025 (mayo de 2024 a abril de 2025), que es $9.747.823.869. · Ventas = ventas netas (brutas menos descuentos y devoluciones).

**F08 (1) ✓** ¿Cuánto vendimos en abril?

> En abril de 2026 (el último abril de la base, que llega hasta el 30/04/2026) vendimos ventas netas por $820.168.520 ARS.
> *Supuestos:* Tomé «abril» como abril de 2026 (calendario), que es el último abril con datos en la base. · «Ventas» se informa como ventas netas (brutas menos descuentos y devoluciones).

**F09 (1) ✗** ¿Cuánto vendimos en el T2 de 2025? — no consultó ninguna de las lecturas (2384401775.0, 2475903842.5, 2361796421.0)

> Las ventas netas del T2 del año fiscal 2025 (agosto a octubre de 2024) fueron de $2.361.796.421. Como «T2 de 2025» admite más de una lectura, también informo el T2 del AF2026 (agosto a octubre de 2025): $2.475.903.842,5.
> *Supuestos:* Tomé «T2 de 2025» como el trimestre fiscal 2 del año fiscal 2025 (AF2025, agosto a octubre de 2024), según la convención de nombrar el año fiscal por el año en que termina. Si lo querías como el T2 del AF2026 (agosto a octubre de 2025), el valor es $2.475.903.842,5.

**F10 (1) ✓** ¿Cuánto vendimos en la primera quincena de marzo de 2026?

> En la primera quincena de marzo de 2026 (del 1 al 15 de marzo, ambos incluidos) las ventas netas de Almacenes del Sur fueron de $426.328.121.
> *Supuestos:* «Primera quincena» tomada como del 1 al 15 de marzo de 2026, con el calendario corriente (no fiscal). · Se informan ventas netas (brutas menos descuentos y devoluciones), que es lo que significa «ventas» sin más aclaración.

**F11 (1) ✓** ¿Cuánto vendimos entre el 10 y el 20 de enero de 2026?

> Entre el 10 y el 20 de enero de 2026 (ambos días incluidos) vendimos $329.754.904,5 en ventas netas, en todas las sucursales y categorías. El día de mayor venta fue el 10 de enero ($40.364.610) y el de menor, el 20 de enero ($25.237.751).
> *Supuestos:* Tomé «ventas» como ventas netas (brutas menos descuentos y devoluciones) e incluí los días 10 y 20 de enero.

**F12 (1) ✓** ¿Cuánto vendimos ayer?

> Ayer (30 de abril de 2026, último día con datos en la base) vendimos $25.904.360 en ventas netas.
> *Supuestos:* Tomé «ayer» como el 30/04/2026, último día con datos en la base, y no la fecha de hoy. · Ventas = ventas netas (brutas menos descuentos y devoluciones), en pesos constantes y sin impuestos.

**F13 (1) ✓** ¿Cuánto vendimos en el AF2027?

> No podemos informar las ventas del año fiscal que consultaste: la base de ventas termina en la fecha de cobertura indicada por el modelo, que es el 30 de abril de 2026, y el período pedido no tiene datos. Si querés, puedo calcular las ventas netas del último año fiscal disponible en la base.

**F14 (1) ✓** ¿Cuánto vendimos en marzo de 2024?

> No podemos calcular las ventas de marzo de 2024: la base de ventas arranca el 1 de mayo de 2024 y para ese mes no hay movimientos registrados (la consulta devuelve valor nulo y cero días con ventas). El primer mes con datos es mayo de 2024. Si necesitás otro período dentro de la cobertura (mayo 2024 a abril 2026), decime cuál y lo calculo.


## Lectura (escrita después de correr)

**Antes del control** (decisión 96, 3 corridas): 39 de 42. Fuera de la base, 6 de 9: siempre decía que no había datos, pero 3 veces agregaba el número del período más cercano, y una vez el registro lo guardó como el valor de la respuesta.

**Con el control** (decisión 97), esta corrida: **41 de 42**. Fuera de la base, **9 de 9**: «No hay datos para el período pedido (AF2027)… Si sirve, puedo consultar el año fiscal más cercano que sí tiene datos». El control saltó 4 veces, solo en F13 y F14, y las 4 veces el agente se corrigió.

La que falla (F09, 1 de 3) es del chequeo y no del agente: dio bien las dos lecturas del «T2 de 2025» (2.361.796.421 y 2.475.903.842,5), pero las sacó de una consulta abierta por trimestre, y el chequeo de lecturas no busca valores en las filas de una consulta agrupada.

Al medir apareció una falsa alarma que compartían el control y el chequeo de la sin dato del evaluador: el día de una fecha («hasta el 30 de abril de 2026») coincidía con un resultado igual a 30. Ahora las fechas escritas no cuentan como cifras.
