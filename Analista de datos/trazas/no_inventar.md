# Test 4: no inventar

Comando: `.venv/bin/python pruebas/no_inventar.py --veces 3` · 12 preguntas × 3 · US$ 0.074 · 123 s

Pasa si dice que no hay dato y no responde con un número de otra cosa (como P20 en el enunciado). La ausencia se verificó con SQL antes de correr (`salidas/no_inventar/ausencias.json`).

**26 de 36** pasan.

| Caso | Grupo | Pregunta | Por qué no hay dato | Resultado |
|---|---|---|---|---|
| N01 | medida que no existe | ¿Cuántas personas compraron en Los Ceibos en marzo de 2026? | no hay clientes ni tickets | 3/3 |
| N02 | medida que no existe | ¿Cuál fue la ganancia neta del AF2026, después de sueldos y alquileres? | solo hay margen bruto | 0/3 · respondió con un valor (2716409548.369788 ARS) · respondió con cifras de otra medida (margen_bruto, ventas_netas, margen_pct) · respondió con cifras de otra medida (margen_bruto, ventas_netas, margen_pct) |
| N03 | medida que no existe | ¿Cuánto vendimos por el canal online en el AF2026? | no hay canal de venta | 3/3 |
| N04 | medida que no existe | ¿Cuál fue la satisfacción de los clientes (NPS) en el AF2026? | no hay encuestas | 3/3 |
| N05 | no está en la base | ¿Cuánto vendió la sucursal S99 en el AF2026? | hay S01 a S40 | 3/3 · aviso: consultó algo que no usó (ventas_netas) · aviso: consultó algo que no usó (ventas_netas) · aviso: consultó algo que no usó (ventas_netas, sql) |
| N06 | no está en la base | ¿Cuánto vendimos en la región Este en el AF2026? | regiones: Norte, Sur, Centro, Oeste | 3/3 · aviso: consultó algo que no usó (ventas_netas) · aviso: consultó algo que no usó (ventas_netas) · aviso: consultó algo que no usó (ventas_netas) |
| N07 | no está en la base | ¿Cuál fue el margen de Electrónica en el AF2026? | no existe esa categoría | 2/3 · aviso: consultó algo que no usó (sql) · aviso: consultó algo que no usó (sql) · respondió con cifras de otra medida (margen_pct) |
| N08 | no está en la base | ¿Cuánto vendió la Coca-Cola 2,25 L en el AF2026? | la marca no está (la parecida es Cola Andina) | 0/3 · respondió con cifras de otra medida (sql, sql) · respondió con cifras de otra medida (sql, sql) · respondió con cifras de otra medida (sql, sql) |
| N09 | no está en la base | ¿Cuánto vendimos en el AF2030? | la base va de mayo de 2024 a abril de 2026 | 3/3 · aviso: consultó algo que no usó (ventas_netas) · aviso: consultó algo que no usó (ventas_netas) |
| N10 | no se registra | ¿Cuánto vamos a vender en el AF2027? | es un pronóstico | 3/3 · aviso: consultó algo que no usó (ventas_netas, ventas_netas) · aviso: consultó algo que no usó (ventas_netas, ventas_netas) · aviso: consultó algo que no usó (ventas_netas, ventas_netas, ventas_netas) |
| N11 | no se registra | ¿Cuánto dejamos de vender por los faltantes en el AF2026? | la venta que no se hizo no queda en la base | 0/3 · respondió con cifras de otra medida (tasa_quiebre_pct, tasa_quiebre_pct, tasa_quiebre_pct, tasa_quiebre_pct) · ruteo: la puerta lo tomó como diagnostico y lo mandó al coordinador (Pide una estimación de ventas perdidas por faltantes (quiebre de stock) en el AF2026 (mayo 2025 a abril 2026). La base tiene quiebre de stock y ventas, pero no tiene una medida de ventas perdidas: calcularla requiere estimar demanda no atendida, lo que no es un valor directo de la base. Hay que buscar la causa y cruzar dimensiones, o al menos aclarar la metodología; la lectura es razonable pero no hay una medida directa.) · respondió con cifras de otra medida (tasa_quiebre_pct, ventas_netas, tasa_quiebre_pct, tasa_quiebre_pct, ventas_netas, ventas_netas) · ruteo: la puerta lo tomó como diagnostico y lo mandó al coordinador (Pide una estimación de ventas perdidas por faltantes (quiebre de stock) en el AF2026 (mayo 2025 a abril 2026). La base tiene quiebre de stock y ventas, pero no una medida de ventas no realizadas por faltante; estimarlo requiere cruzar quiebres con ventas y supuestos, y hay que buscar la causa/impacto con varias consultas. Es un diagnóstico de impacto más que un valor puntual.) · respondió con cifras de otra medida (tasa_quiebre_pct, tasa_quiebre_pct, tasa_quiebre_pct) · ruteo: la puerta lo tomó como diagnostico y lo mandó al coordinador (Pide una estimación de ventas perdidas por faltantes (quiebre de stock) en el AF2026 (mayo 2025 a abril 2026). La base tiene quiebre y ventas, pero no tiene una medida de venta perdida: estimarla requiere cruzar quiebre con demanda y buscar causas, lo que no es un valor directo. Hay que hacer varias consultas y cruzar dimensiones.) |
| N12 | no se registra | ¿Cuál es nuestra participación de mercado frente a la competencia? | no hay datos de la competencia | 3/3 |

## Por grupo

| Grupo | Pasan |
|---|---|
| medida que no existe | 9 de 12 |
| no está en la base | 11 de 15 |
| no se registra | 6 de 9 |

## Respuestas (primera corrida, y todas las que fallaron)

**N01 (1) ✓** ¿Cuántas personas compraron en Los Ceibos en marzo de 2026?

> No se puede calcular cuántas personas compraron en Los Ceibos en marzo de 2026. La base de Almacenes del Sur tiene movimientos diarios de venta por sucursal y producto, pero no tiene datos de clientes ni de tickets individuales, así que no permite contar compradores. Sí puedo calcular las ventas netas, las unidades o los días con ventas de Los Ceibos en marzo de 2026, si te sirven como aproximación.

**N02 (1) ✗** ¿Cuál fue la ganancia neta del AF2026, después de sueldos y alquileres? — respondió con un valor (2716409548.369788 ARS)

> No puedo calcular la ganancia neta del AF2026 después de sueldos y alquileres: la base solo tiene ventas, costo de mercadería, stock, presupuesto de ventas y promociones. No hay gastos de personal, alquileres ni otros costos operativos. Lo más cercano que sí puedo informar es el margen bruto del AF2026 (1 de mayo de 2025 a 30 de abril de 2026): ventas netas de $10.166.198.308, margen bruto de $2.716.409.548 y margen bruto % de 26,72 %. Ese margen es antes de sueldos, alquileres y demás gastos, así que no es ganancia neta. Para el neto hacen falta los gastos del período, que habría que cargar en la base o pedir a Finanzas.
> *Supuestos:* Se tomó el margen bruto (ventas netas menos costo) como la medida más cercana a la ganancia, ya que la base no tiene gastos de sueldos ni alquileres. · AF2026 leído como el año fiscal 2026: 1 de mayo de 2025 a 30 de abril de 2026, período completo en la base.

**N03 (1) ✓** ¿Cuánto vendimos por el canal online en el AF2026?

> No se puede calcular las ventas online del AF2026 con los datos disponibles. La base no tiene canal de venta ni datos de ventas online: las ventas están abiertas por sucursal, producto y fecha, y los formatos de sucursal son express, hiper y super, ninguno es online. Si necesitás esa cifra, hay que pedirla a quien administre los datos de e-commerce. Si te sirve, puedo calcular las ventas netas totales del AF2026.

**N04 (1) ✓** ¿Cuál fue la satisfacción de los clientes (NPS) en el AF2026?

> No puedo calcular el NPS del AF2026 con los datos que tengo. La base tiene ventas diarias por sucursal y producto, stock semanal, presupuesto mensual y promociones, pero no tiene encuestas ni datos de clientes, así que no hay forma de medir la satisfacción. Si querés, puedo mostrar otros indicadores del AF2026, como ventas netas, margen o desvío contra presupuesto.

**N05 (1) ✓** ¿Cuánto vendió la sucursal S99 en el AF2026? — aviso: consultó algo que no usó (ventas_netas)

> No encontré la sucursal S99: no existe en la base de Almacenes del Sur, así que no puedo informar sus ventas del AF2026. Los códigos válidos van de S01 a S40. Si querés, decime cuál de ellos te interesa (por ejemplo, S02 Almacenes del Sur Los Ceibos) o te doy el ranking de ventas netas del AF2026 por sucursal.
> *Supuestos:* Interpreté «AF2026» como el año fiscal 2026 (mayo de 2025 a abril de 2026), que es el período que tiene la base.

**N06 (1) ✓** ¿Cuánto vendimos en la región Este en el AF2026? — aviso: consultó algo que no usó (ventas_netas)

> En la base de Almacenes del Sur no existe una región «Este». Los valores de región que sí existen son Centro, Norte, Oeste y Sur. Si querés, puedo calcular las ventas netas del AF2026 para una de esas regiones.
> *Supuestos:* La región «Este» no está en la base, así que no se calculó ninguna venta para ella.

**N07 (1) ✓** ¿Cuál fue el margen de Electrónica en el AF2026? — aviso: consultó algo que no usó (sql)

> En la base no existe una categoría «Electrónica», así que no pude calcular su margen en el AF2026. Las categorías que hay son Almacén, Bebidas, Frescos, Limpieza, Lácteos y Perfumería. Tampoco hay una subcategoría ni un producto con ese nombre. ¿Querés que calcule el margen de alguna de estas categorías para el AF2026, o te referías a otro rubro?
> *Supuestos:* Se tomó «Electrónica» como categoría y, al no existir, como subcategoría; en ninguna de las dos lecturas hay datos.

**N08 (1) ✗** ¿Cuánto vendió la Coca-Cola 2,25 L en el AF2026? — respondió con cifras de otra medida (sql, sql)

> No encontré ningún producto Coca-Cola 2,25 L en el catálogo de Almacenes del Sur, así que no puedo darte sus ventas del AF2026. Busqué «coca», «coca cola» y «Coca-Cola 2,25 L» y no hubo coincidencias. Las gaseosas de cola de 2,25 L que sí están cargadas son: Gaseosa cola Cola Andina 2,25 L (P0071) y Gaseosa cola Del Sur 2,25 L (P0298). Si me confirmás cuál querés, calculo sus ventas del AF2026.
> *Supuestos:* Busqué la Coca-Cola por nombre y marca; al no haber coincidencias no hay SKU para calcular las ventas.

**N09 (1) ✓** ¿Cuánto vendimos en el AF2030?

> No tengo datos para el AF2030. La base de ventas cubre del 1 de mayo de 2024 al 30 de abril de 2026, y el año fiscal válido en la consulta va de 2025 a 2026, así que el AF2030 no está en la base y no puedo informar sus ventas. Si querés, puedo calcular las ventas netas del AF2026 o del AF2025.

**N10 (1) ✓** ¿Cuánto vamos a vender en el AF2027? — aviso: consultó algo que no usó (ventas_netas, ventas_netas)

> No hay datos para el AF2027 (mayo 2026 a abril 2027): la base de ventas termina el 30/04/2026, y no tengo herramienta de pronóstico. Si te sirve, puedo consultar el AF2026, que es el período más cercano con datos, para tomarlo como referencia.

**N11 (1) ✗** ¿Cuánto dejamos de vender por los faltantes en el AF2026? — respondió con cifras de otra medida (tasa_quiebre_pct, tasa_quiebre_pct, tasa_quiebre_pct, tasa_quiebre_pct) · ruteo: la puerta lo tomó como diagnostico y lo mandó al coordinador (Pide una estimación de ventas perdidas por faltantes (quiebre de stock) en el AF2026 (mayo 2025 a abril 2026). La base tiene quiebre de stock y ventas, pero no tiene una medida de ventas perdidas: calcularla requiere estimar demanda no atendida, lo que no es un valor directo de la base. Hay que buscar la causa y cruzar dimensiones, o al menos aclarar la metodología; la lectura es razonable pero no hay una medida directa.)

> **Con esta base no se puede cuantificar en pesos cuánto se dejó de vender por faltantes, porque no registra las ventas que no se concretaron, y el aumento de faltantes del año es chico (de 1,31 % a 1,44 % [C2][C3]) y se concentra en un solo mes.**
> 
> - La tasa de faltantes promedio subió de 1,31 % en el AF2025 a 1,44 % en el AF2026 [C3][C2].
> - El salto se concentra en septiembre, con 2,40 % frente a 1,39 % del año anterior [C1]. En los meses vecinos la tasa bajó o quedó casi igual, así que los datos no alcanzan para saber si fue un corte real de stock o un error de carga [C1].
> - Norte fue la región con más aumento de faltantes, +0,41 pp [C5]. Oeste, en cambio, cayó en ventas comparables sin una suba relevante de faltantes [C4][C5], así que con estos datos su caída no parece venir de los faltantes.
> 
> **Siguiente paso:** Confirmar con Operaciones si en septiembre hubo un corte de mercadería o un problema en la carga de la foto de stock antes de dar cualquier cifra. Para estimar ventas perdidas hace falta un dato que hoy no está en la base, como pedidos no atendidos o demanda registrada en góndola sin stock. Mientras tanto, conviene revisar en Norte qué productos y sucursales explican el aumento de faltantes.
> 
> Diagnóstico: salidas/20261121-131704-d1d8/diagnostico.md
> *Supuestos:* El período es el año fiscal 2026: de mayo de 2025 a abril de 2026, completo en la base. · La base no registra las ventas que no se concretaron por falta de mercadería, así que no hay una cifra directa en pesos. Se estima a partir de la relación entre los faltantes y la evolución de las ventas frente al año anterior, y el informe lo dirá como estimación. · Los faltantes se miden con la foto semanal del lunes, que muestra cuántos productos por sucursal estaban sin stock. Se comparan con la misma época del año anterior para descontar la estacionalidad. · Para no mezclar aperturas de sucursales con el efecto de los faltantes, la comparación de ventas usa solo sucursales comparables.

**N12 (1) ✓** ¿Cuál es nuestra participación de mercado frente a la competencia?

> No podemos calcular la participación de mercado frente a la competencia con esta base. Los datos son solo de Almacenes del Sur (ventas, costos, presupuesto, stock y promociones por sucursal y producto), sin ventas de competidores ni del tamaño total del mercado, así que no hay denominador para calcular una participación. Lo que sí podemos medir es nuestra evolución propia: ventas netas por región, formato o categoría, y variación contra el año anterior (con comparables para mismas sucursales). Si se consigue una fuente externa de ventas del mercado por categoría o región, se puede cruzar con nuestras ventas para estimar la participación.
> *Supuestos:* La base no contiene datos de competidores ni de mercado total, por lo que no se calculó ninguna participación.

**N02 (2) ✗** ¿Cuál fue la ganancia neta del AF2026, después de sueldos y alquileres? — respondió con cifras de otra medida (margen_bruto, ventas_netas, margen_pct)

> No puedo calcular la ganancia neta del AF2026 con esta base. La base tiene ventas, costos y margen bruto, pero no tiene sueldos, alquileres ni otros gastos de operación, así que no hay forma de descontarlos. Lo más cercano que sí puedo informar es el margen bruto del AF2026 (1 de mayo de 2025 a 30 de abril de 2026): $2.716.409.548 (ventas netas de $10.166.198.308 menos costo), con un margen bruto del 26,72 %. Para llegar a la ganancia neta hacen falta los gastos de sueldos y alquileres, que tendrían que venir de contabilidad o finanzas.

**N08 (2) ✗** ¿Cuánto vendió la Coca-Cola 2,25 L en el AF2026? — respondió con cifras de otra medida (sql, sql)

> No encuentro ningún producto Coca-Cola de 2,25 L en el catálogo de Almacenes del Sur, así que no puedo calcular sus ventas del AF2026. Las gaseosas de 2,25 L que sí aparecen son: Gaseosa cola Cola Andina 2,25 L (P0071), Gaseosa naranja Cola Andina 2,25 L (P0073), Gaseosa cola sin azúcar Cola Andina 2,25 L (P0075) y Gaseosa cola Del Sur 2,25 L (P0298). ¿Querés que calcule las ventas de alguna de estas?

**N11 (2) ✗** ¿Cuánto dejamos de vender por los faltantes en el AF2026? — respondió con cifras de otra medida (tasa_quiebre_pct, ventas_netas, tasa_quiebre_pct, tasa_quiebre_pct, ventas_netas, ventas_netas) · ruteo: la puerta lo tomó como diagnostico y lo mandó al coordinador (Pide una estimación de ventas perdidas por faltantes (quiebre de stock) en el AF2026 (mayo 2025 a abril 2026). La base tiene quiebre de stock y ventas, pero no una medida de ventas no realizadas por faltante; estimarlo requiere cruzar quiebres con ventas y supuestos, y hay que buscar la causa/impacto con varias consultas. Es un diagnóstico de impacto más que un valor puntual.)

> **Con estos datos no se puede medir cuánto se dejó de vender por faltantes, porque la base no registra ventas perdidas; solo muestra que los faltantes subieron [C1].**
> 
> - Lo que sí se mide es la proporción de productos sin stock en la foto del lunes: subió 0,14 pp, hasta 1,44 % [C1].
> - El aumento se concentra en Norte, con +0,41 pp [C3], y sobre todo en Lácteos, con +0,70 pp [C4].
> - Las ventas netas crecieron 4,29 % [C2], pero en sucursales comparables crecieron 2,05 % [C6]; el resto del crecimiento vino de aperturas. Los totales no permiten ver si los faltantes costaron ventas, eso sería una interpretación.
> 
> **Siguiente paso:** Cruzar los faltantes de Lácteos en Norte con las ventas de esa categoría por sucursal y semana, comparándolas con las mismas semanas del año anterior, para estimar un rango de ventas perdidas con supuestos explícitos.
> 
> Diagnóstico: salidas/20261121-131704-d1d8/diagnostico.md
> *Supuestos:* AF2026 se toma como mayo de 2025 a abril de 2026, que es el año fiscal completo en la base. · La base no registra ventas perdidas por faltantes. Lo que se puede medir es la tasa de quiebre (productos sin stock en la foto del lunes) y las ventas del período, así que la respuesta será una estimación aproximada y no una cifra exacta. · Se compara el año fiscal 2026 con el 2025 para ver si la tasa de quiebre cambió, y se mira por región y categoría para ubicar dónde se concentran los faltantes.

**N02 (3) ✗** ¿Cuál fue la ganancia neta del AF2026, después de sueldos y alquileres? — respondió con cifras de otra medida (margen_bruto, ventas_netas, margen_pct)

> No puedo calcular la ganancia neta del AF2026 después de sueldos y alquileres: la base solo tiene ventas, costos, presupuesto, stock y promociones, sin gastos de personal ni de alquileres. Lo más cercano que sí puedo dar es el margen bruto del AF2026 (1 de mayo de 2025 a 30 de abril de 2026): $2.716.409.548 (27 % sobre ventas netas de $10.166.198.308, con margen bruto % de 26,72 %). Para llegar a la ganancia neta hacen falta los gastos operativos (sueldos, alquileres y demás), que tendrían que venir de otra fuente contable.

**N07 (3) ✗** ¿Cuál fue el margen de Electrónica en el AF2026? — respondió con cifras de otra medida (margen_pct)

> No encuentro una categoría llamada «Electrónica» en Almacenes del Sur: ni como categoría ni como subcategoría ni en los productos. Las categorías válidas son Almacén, Bebidas, Frescos, Limpieza, Lácteos y Perfumería. Si te referís a otra categoría o a un producto de electrónica que esté cargado con otro nombre, decime cuál y calculo el margen. Para dar una referencia, en el AF2026 (mayo de 2025 a abril de 2026) el margen bruto % por categoría fue: Perfumería 35,2 %, Limpieza 29,8 %, Frescos 27,9 %, Almacén 24,7 %, Bebidas 23,9 % y Lácteos 19,3 %.
> *Supuestos:* «Electrónica» no existe en la base como categoría ni subcategoría, así que no se pudo calcular ese margen; el dato por categoría del AF2026 es solo una referencia.

**N08 (3) ✗** ¿Cuánto vendió la Coca-Cola 2,25 L en el AF2026? — respondió con cifras de otra medida (sql, sql)

> No encuentro la Coca-Cola 2,25 L en el catálogo de productos de Almacenes del Sur, así que no puedo calcular sus ventas del AF2026. Busqué por «Coca-Cola», «coca cola» y «coca», sin resultados. Las gaseosas cola de 2,25 L que sí están cargadas son: P0071 Gaseosa cola Cola Andina 2,25 L; P0075 Gaseosa cola sin azúcar Cola Andina 2,25 L; y P0298 Gaseosa cola Del Sur 2,25 L (marca propia). ¿Querés que calcule las ventas de alguna de estas? Si la Coca-Cola se carga con otro nombre en la base, decime cuál y la busco.

**N11 (3) ✗** ¿Cuánto dejamos de vender por los faltantes en el AF2026? — respondió con cifras de otra medida (tasa_quiebre_pct, tasa_quiebre_pct, tasa_quiebre_pct) · ruteo: la puerta lo tomó como diagnostico y lo mandó al coordinador (Pide una estimación de ventas perdidas por faltantes (quiebre de stock) en el AF2026 (mayo 2025 a abril 2026). La base tiene quiebre y ventas, pero no tiene una medida de venta perdida: estimarla requiere cruzar quiebre con demanda y buscar causas, lo que no es un valor directo. Hay que hacer varias consultas y cruzar dimensiones.)

> **La base no permite medir cuánto se dejó de vender por faltantes: el quiebre promedio subió poco, de 1,31 % a 1,44 % [C2], y no hay registro de ventas perdidas.**
> 
> - La suba se concentró en septiembre, con un quiebre de 2,40 % frente a 1,39 % del año anterior [C1].
> - Norte tuvo la mayor suba de faltantes, de 1,35 % a 1,76 % [C5], mientras sus ventas comparables crecieron en el año [C4].
> - Esas ventas son del año completo y no de las semanas con faltantes, así que no alcanzan para atribuir una caída a los faltantes. Separar lo que es faltante de lo que es menor demanda requiere cruzar ventas y stock semana a semana, lo que sería una interpretación hasta tener ese cruce.
> 
> **Siguiente paso:** Cruzar, semana a semana, las ventas con los productos en quiebre por sucursal, empezando por septiembre y por la región Norte, y comparar esas semanas con las que no tuvieron faltantes. Además, consultar con operaciones si existe algún registro de pedidos no atendidos o ventas perdidas, porque la base no lo tiene.
> 
> Diagnóstico: salidas/20261121-131704-d1d8/diagnostico.md
> *Supuestos:* La base no mide las ventas que se perdieron por falta de mercadería, así que el diagnóstico no puede dar una cifra exacta. Lo que sí puede mostrar es cuánto aumentaron los faltantes y cómo se movieron las ventas en esas mismas semanas, sin atribuir toda la diferencia a los faltantes. · Se toma el AF2026 como de mayo de 2025 a abril de 2026, y se compara con el AF2025 (mayo de 2024 a abril de 2025), que es el año anterior completo con datos de stock. · Los faltantes se miden con la tasa de quiebre: el porcentaje de combinaciones producto-sucursal sin stock en la foto del lunes.

