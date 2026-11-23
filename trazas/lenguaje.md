# Test 2: robustez del lenguaje (decisión 94)

Comando: `.venv/bin/python evaluacion/robustez/lenguaje.py --veces 3` · 35 preguntas × 3 · US$ 0.146 · 199 s

**Variantes que dan el número correcto: 84 de 84** · originales: 21 de 21

## Por pregunta

| Pregunta | original | coloquial | errores | sinonimos | corta |
|---|---|---|---|---|---|
| P01 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| P02 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| P03 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| P06 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| P07 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| P10 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| P20 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |

## Por estilo

| Estilo | Número correcto | La puerta le dio el tipo de la original |
|---|---|---|
| original | 21 de 21 | 21 de 21 |
| coloquial | 21 de 21 | 21 de 21 |
| errores | 21 de 21 | 21 de 21 |
| sinonimos | 21 de 21 | 21 de 21 |
| corta | 21 de 21 | 21 de 21 |

## Cada variante

| Pregunta | Estilo | Texto | Tipo (esperado) | Chequeo |
|---|---|---|---|---|
| P01 | original | ¿Cuánto vendió la cadena en el año fiscal 2025? | puntual (puntual) | ✓ · ✓ · ✓ |
| P01 | coloquial | che, ¿cuánto facturamos en todo el año fiscal 2025? | puntual (puntual) | ✓ · ✓ · ✓ |
| P01 | errores | cuanto vendio la cadena en el año fsical 2025 | puntual (puntual) | ✓ · ✓ · ✓ |
| P01 | sinonimos | Para el año fiscal 2025, ¿cuál fue el total vendido por toda la cadena? | puntual (puntual) | ✓ · ✓ · ✓ |
| P01 | corta | ventas AF2025? | puntual (puntual) | ✓ · ✓ · ✓ |
| P02 | original | ¿Cuántas unidades de Lácteos se vendieron en marzo de 2026? | puntual (puntual) | ✓ · ✓ · ✓ |
| P02 | coloquial | ¿cuántas unidades de lácteos movimos en marzo del 2026? | puntual (puntual) | ✓ · ✓ · ✓ |
| P02 | errores | cuantas unidades de lacteos se vendieron en marso 2026 | puntual (puntual) | ✓ · ✓ · ✓ |
| P02 | sinonimos | En marzo de 2026, la categoría Lácteos, ¿qué cantidad de unidades vendió? | puntual (puntual) | ✓ · ✓ · ✓ |
| P02 | corta | unidades lacteos mar-26 | puntual (puntual) | ✓ · ✓ · ✓ |
| P03 | original | ¿Qué margen bruto tuvo Perfumería en el AF2026? | puntual (puntual) | ✓ · ✓ · ✓ |
| P03 | coloquial | ¿cuánta guita nos dejó Perfumería en el año fiscal 2026, después de pagar la mercadería? | puntual (puntual) | ✓ · ✓ · ✓ |
| P03 | errores | que margen bruto tubo perfumeria en el af 2026 | puntual (puntual) | ✓ · ✓ · ✓ |
| P03 | sinonimos | Perfumería, año fiscal 2026: ventas netas menos costo, ¿cuánto da en pesos? | puntual (puntual) | ✓ · ✓ · ✓ |
| P03 | corta | margen bruto perfu AF26 | puntual (puntual) | ✓ · ✓ · ✓ |
| P06 | original | ¿Cuánto crecieron las ventas de Bebidas en el T3 del AF2026 contra el mismo trimestre del año anterior? | comparativa (comparativa) | ✓ · ✓ · ✓ |
| P06 | coloquial | ¿cómo nos fue con Bebidas en el tercer trimestre fiscal de 2026 comparado con el del año anterior? | comparativa (comparativa) | ✓ · ✓ · ✓ |
| P06 | errores | cuanto crecieron las ventas de bebidas en el t3 del af2026 contra el mismo trimestre del año anterir | comparativa (comparativa) | ✓ · ✓ · ✓ |
| P06 | sinonimos | Variación interanual de las ventas de Bebidas en el tercer trimestre del año fiscal 2026 | comparativa (comparativa) | ✓ · ✓ · ✓ |
| P06 | corta | bebidas T3 AF26 vs T3 AF25 % | comparativa (comparativa) | ✓ · ✓ · ✓ |
| P07 | original | ¿Cuánto cambió el margen de Almacén en el T2 del AF2026 contra el T2 del AF2025? | comparativa (comparativa) | ✓ · ✓ · ✓ |
| P07 | coloquial | ¿el margen de Almacén subió o bajó en el segundo trimestre fiscal 2026 frente al mismo del año anterior? ¿cuánto? | comparativa (comparativa) | ✓ · ✓ · ✓ |
| P07 | errores | cuanto cambio el margen de almacen en el t2 del af2026 contra el t2 del af2025 | comparativa (comparativa) | ✓ · ✓ · ✓ |
| P07 | sinonimos | Almacén: diferencia de margen % entre el T2 del AF2025 y el T2 del AF2026 | comparativa (comparativa) | ✓ · ✓ · ✓ |
| P07 | corta | margen % almacen T2 AF26 vs AF25 | comparativa (comparativa) | ✓ · ✓ · ✓ |
| P10 | original | ¿Cuáles fueron las 5 sucursales que más vendieron en el AF2026? | ranking (ranking) | ✓ · ✓ · ✓ |
| P10 | coloquial | ¿cuáles fueron nuestras 5 sucursales estrella en ventas en el AF2026? | ranking (ranking) | ✓ · ✓ · ✓ |
| P10 | errores | cuales fueron las 5 sucursales que mas vendieron en el af2026 | ranking (ranking) | ✓ · ✓ · ✓ |
| P10 | sinonimos | Top 5 de locales por ventas netas en el año fiscal 2026 | ranking (ranking) | ✓ · ✓ · ✓ |
| P10 | corta | top 5 sucursales AF26 | ranking (ranking) | ✓ · ✓ · ✓ |
| P20 | original | ¿Cuántos clientes nuevos tuvimos en marzo de 2026? | sin_dato (sin_dato) | ✓ · ✓ · ✓ |
| P20 | coloquial | ¿cuánta gente nueva vino a comprar en marzo de 2026? | sin_dato (sin_dato) | ✓ · ✓ · ✓ |
| P20 | errores | cuantos clientes nuevos tuvimos en marso 2026 | sin_dato (sin_dato) | ✓ · ✓ · ✓ |
| P20 | sinonimos | ¿Cuántas altas de clientes hubo en marzo de 2026? | sin_dato (sin_dato) | ✓ · ✓ · ✓ |
| P20 | corta | clientes nuevos mar-26 | sin_dato (sin_dato) | ✓ · ✓ · ✓ |

## Lectura (escrita después de correr)

**Antes del control** (decisión 94; 3 corridas, en `trazas/` hasta el commit de la decisión 94): 81 de 84 variantes con el número correcto. Las 3 fallas eran la misma: «Almacén: diferencia de margen %…», donde el agente tomaba «Almacén:» como la empresa y calculaba toda la cadena, aunque el glosario ya decía que «Almacén» es la categoría.

**Con el control en código** (decisión 95), esta corrida: **84 de 84**. El control saltó exactamente 3 veces, solo en esa variante (una por corrida), y las 3 veces el agente volvió a consultar con la categoría. No saltó en ninguna otra variante, ni en el evaluador (6 corridas), ni en los 4 diagnósticos y los 3 informes (2 corridas).

En una corrida intermedia, con la primera versión del control, la sin dato coloquial (P20, «¿cuánta gente nueva vino a comprar…?») falló 1 de 3: dijo bien que no hay datos de clientes, pero agregó «vendieron 40 sucursales». Esa pregunta no nombra ningún grupo, así que el control no tuvo que ver: es variación de Haiku.
