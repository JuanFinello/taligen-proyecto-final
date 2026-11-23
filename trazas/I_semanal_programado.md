> **Informe generado solo (semana 4).** Lo lanzó `informe_programado.py`, el mismo que corre el temporizador de systemd
> los lunes a las 8, simulando el lunes 27-04-2026 (`--hoy 2026-04-27`), porque la base termina el 30-04-2026. Le tocó
> el semanal del 20 al 26-04-2026; nadie escribió el pedido: lo arma el código según el calendario (decisiones 65 y 66).
> Línea del historial (`salidas/programado/historial.txt`):
> `2026-11-23 15:01 · lunes 2026-04-27 (fecha simulada) · semana-2026-04-20 · bien · 121 s`
> El PDF y el SQL de las consultas citadas están al lado: `I_semanal_programado.pdf` y `I_semanal_programado.sql`.

# Traza: Preparame un informe ejecutivo de la semana del lunes 20-04-2026 al domingo 26-04-2026, sobre qué requiere la atención de la gerencia esta semana: la tasa de quiebre de stock de la semana, por región y por proveedor; las sucursales con mayor caída de ventas netas; y los productos con caída fuerte. Todo contra la misma semana del año anterior (del lunes 21-04-2025 al domingo 27-04-2025). Las ventas netas y el margen del total, solo como contexto.

Corrida `20261123-145921-d01b` · versión del diseño `274510` · `claude-haiku-5-5`. Para volver a correrla:

```
.venv/bin/python analista/informes.py "Preparame un informe ejecutivo de la semana del lunes 20-04-2026 al domingo 26-04-2026, sobre qué requiere la atención de la gerencia esta semana: la tasa de quiebre de stock de la semana, por región y por proveedor; las sucursales con mayor caída de ventas netas; y los productos con caída fuerte. Todo contra la misma semana del año anterior (del lunes 21-04-2025 al domingo 27-04-2025). Las ventas netas y el margen del total, solo como contexto." salidas/programado/semana-2026-04-20
```

Resultado: [I_semanal_programado.pdf](I_semanal_programado.pdf) · SQL de las consultas citadas: [I_semanal_programado.sql](I_semanal_programado.sql)

## 1. Coordinador: el plan

Tipo: **informe** · Semana del 20 al 26 de abril de 2026: qué requiere la atención de la gerencia

Supuestos:
- La semana va de lunes a domingo en calendario: del 20 al 26 de abril de 2026, comparada con la misma semana del año anterior (del 21 al 27 de abril de 2025). No se usa el año fiscal.
- Las variaciones son sobre el total de sucursales, no sobre sucursales comparables. Una sucursal que abrió o cerró dentro de esas semanas puede distorsionar la comparación, y eso se dirá en el informe si pasa.
- Lo que es una caída fuerte no está fijado en el pedido. El informe presenta las mayores caídas en pesos y en porcentaje, sin un umbral predeterminado.
- La tasa de quiebre de la semana se toma de la foto de stock del lunes 20 de abril de 2026. Para saber si es alta, se compara con la misma semana del año anterior y con las cuatro semanas anteriores.
- Ventas netas y margen del total van solo como contexto, sin explicación de causas. El presupuesto no entra en el pedido y no se incluye.

**Pregunta 1.** Tasa de quiebre de stock de la semana del lunes 20 al domingo 26 de abril de 2026, por región, en todas las sucursales y categorías. Compararla con la misma semana del año anterior (lunes 21 al domingo 27 de abril de 2025) y con las cuatro semanas anteriores a la del 20 de abril de 2026 (semanas del 23 de marzo, 30 de marzo, 6 de abril y 13 de abril de 2026).

- Para qué: Dar la tasa de quiebre de stock de la semana por región, comparada con el año anterior y con las semanas cercanas, para ver qué regiones están por encima de lo habitual.
- Consulta sugerida: tasa_quiebre_pct de la semana del 20 al 26 de abril de 2026, por región, contra la semana del 21 al 27 de abril de 2025
- Consulta sugerida: tasa_quiebre_pct por región de las cuatro semanas anteriores al 20 de abril de 2026, para ver si el valor de la semana es normal
- No mirar: No abrir por proveedor ni por sucursal, eso va en otros encargos. No analizar ventas.

**Pregunta 2.** Tasa de quiebre de stock de la semana del lunes 20 al domingo 26 de abril de 2026, por proveedor (código y nombre), en todas las sucursales y categorías. Compararla con la misma semana del año anterior (lunes 21 al domingo 27 de abril de 2025) y con las cuatro semanas anteriores a la del 20 de abril de 2026.

- Para qué: Identificar qué proveedores tienen más quiebre de stock esta semana y si el quiebre es nuevo frente al año anterior.
- Consulta sugerida: tasa_quiebre_pct de la semana del 20 al 26 de abril de 2026, por proveedor (código y nombre), contra la semana del 21 al 27 de abril de 2025, ordenado por valor de la semana
- Consulta sugerida: tasa_quiebre_pct por proveedor (código y nombre) de las cuatro semanas anteriores al 20 de abril de 2026, para ver si el valor de la semana es normal
- No mirar: No abrir por región ni por sucursal. No analizar ventas ni explicar causas.

**Pregunta 3.** Ventas netas por sucursal (código, nombre y región) de la semana del lunes 20 al domingo 26 de abril de 2026, contra la misma semana del año anterior (lunes 21 al domingo 27 de abril de 2025). Ordenar por caída en pesos y en porcentaje. Incluir los días con ventas de cada sucursal en las dos semanas. Como contexto, las ventas netas y el margen % del total de la cadena en las dos semanas.

- Para qué: Identificar qué sucursales tuvieron la mayor caída de ventas netas esta semana frente al año anterior y si la caída se debe a días sin ventas o a menos demanda.
- Consulta sugerida: ventas_netas de la semana del 20 al 26 de abril de 2026 contra la semana del 21 al 27 de abril de 2025, por sucursal (código, nombre y región), ordenado por caída en pesos
- Consulta sugerida: dias_con_ventas de las mismas dos semanas, por sucursal (código y nombre)
- Consulta sugerida: ventas_netas y margen_pct del total de la cadena en las dos semanas, sin apertura, solo como contexto
- No mirar: No abrir por producto, proveedor ni subcategoría. No analizar quiebre de stock. No explicar el margen por efecto precio o costo.

**Pregunta 4.** Ventas netas por producto (sku, descripción, marca y subcategoría) de la semana del lunes 20 al domingo 26 de abril de 2026, contra la misma semana del año anterior (lunes 21 al domingo 27 de abril de 2025), en todas las sucursales. Ordenar por caída en pesos y en porcentaje. Listar las promociones de esas dos semanas para los productos con mayor caída.

- Para qué: Identificar los productos con caída fuerte de ventas netas esta semana y si la caída es del producto o de toda su subcategoría, con las promociones de ambas semanas como posible explicación.
- Consulta sugerida: ventas_netas por producto (sku y descripción) de la semana del 20 al 26 de abril de 2026 contra la semana del 21 al 27 de abril de 2025, ordenado por caída en pesos
- Consulta sugerida: ventas_netas por subcategoría de las mismas dos semanas, para ver si la caída es del producto o de toda la subcategoría
- Consulta sugerida: listar las promociones vigentes entre el 20 y el 26 de abril de 2026 y entre el 21 y el 27 de abril de 2025 de los productos con mayor caída, con su descuento y fechas
- No mirar: No analizar quiebre de stock ni sucursales, eso va en otros encargos. No explicar el margen.

## 2. Analistas: una llamada por pregunta, cada una desde cero

### Analista 1

5 vueltas del modelo · US$ 0.0048 · 26.8 s

- Vuelta 1: ver_modelo
- Vuelta 2: calcular, calcular, calcular
- Vuelta 3: respuesta final
  - ✗ el control devolvió la respuesta: números sin respaldo 0,18, 0,16, 0,52, 0,26, 1,36, 0,12, 1,2572, 1,2572, 0,18, 1,3571, 1,3571, 0,26, 1,4054, 1,4054, 0,01, 1,2507, 1,2507, 0,16, 0,52, 0,12, 0,24, 0,05
- Vuelta 4: calcular, calcular, calcular
- Vuelta 5: respuesta final

**Hallazgo:**

> La tasa de quiebre de la semana del 20 al 26 de abril de 2026 fue 1,33 % en total, prácticamente igual a las cuatro semanas anteriores (1,32 %) y 0,16 pp por encima de la misma semana de 2025 (1,17 %). Por región, Centro (1,44 %) y Sur (1,41 %) están por encima de lo habitual, con +0,18 pp y +0,16 pp frente a sus cuatro semanas previas, y Sur sube +0,52 pp contra la semana de 2025 (0,89 %). Norte (1,10 %) queda 0,26 pp por debajo de su promedio reciente (1,36 %) y Oeste (1,39 %) está en línea con el suyo.

**Consultas:**

- **[C1] `calcular`** `{"medida": "tasa_quiebre_pct", "filtros": {"semana": ["2026-04-20"]}, "agrupar_por": ["region"]}`
  - Resultado: 4 filas

  ```sql
  -- parámetros ["2026-04-20"]
  SELECT s.region AS region, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
  FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.semana_inicio IN (?)
  GROUP BY s.region
  ORDER BY valor DESC
  ```
- **[C2] `calcular`** `{"medida": "tasa_quiebre_pct", "filtros": {"semana": ["2025-04-21"]}, "agrupar_por": ["region"]}`
  - Resultado: 4 filas

  ```sql
  -- parámetros ["2025-04-21"]
  SELECT s.region AS region, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
  FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.semana_inicio IN (?)
  GROUP BY s.region
  ORDER BY valor DESC
  ```
- **[C3] `calcular`** `{"medida": "tasa_quiebre_pct", "filtros": {"semana": ["2026-03-23", "2026-03-30", "2026-04-06", "2026-04-13"]}, "agrupar_por": ["region", "semana"]}`
  - Resultado: 16 filas

  ```sql
  -- parámetros ["2026-03-23", "2026-03-30", "2026-04-06", "2026-04-13"]
  SELECT s.region AS region, f.semana_inicio AS semana, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
  FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.semana_inicio IN (?, ?, ?, ?)
  GROUP BY s.region, f.semana_inicio
  ORDER BY valor DESC
  ```
- **[C4] `calcular`** `{"medida": "tasa_quiebre_pct", "filtros": {"semana": ["2026-04-20"]}, "agrupar_por": ["region"], "comparar_con": {"semana": ["2025-04-21"]}}`
  - Resultado: actual = 1.332662811164194 · anterior = 1.169975023005127 · variacion = 0.16268778815906715 · unidad_variacion = pp · comparables = False · 4 filas

  ```sql
  -- actual: parámetros ["2026-04-20"]
  SELECT s.region AS region, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
  FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.semana_inicio IN (?)
  GROUP BY s.region
  ORDER BY valor DESC
  ```

  ```sql
  -- anterior: parámetros ["2025-04-21"]
  SELECT s.region AS region, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
  FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.semana_inicio IN (?)
  GROUP BY s.region
  ORDER BY valor DESC
  ```
- **[C5] `calcular`** `{"medida": "tasa_quiebre_pct", "filtros": {"semana": ["2026-03-23", "2026-03-30", "2026-04-06", "2026-04-13"]}, "agrupar_por": ["region"]}`
  - Resultado: 4 filas

  ```sql
  -- parámetros ["2026-03-23", "2026-03-30", "2026-04-06", "2026-04-13"]
  SELECT s.region AS region, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
  FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.semana_inicio IN (?, ?, ?, ?)
  GROUP BY s.region
  ORDER BY valor DESC
  ```
- **[C6] `calcular`** `{"medida": "tasa_quiebre_pct", "filtros": {"semana": ["2026-04-20"]}, "agrupar_por": ["region"], "comparar_con": {"semana": ["2026-03-23", "2026-03-30", "2026-04-06", "2026-04-13"]}}`
  - Resultado: actual = 1.332662811164194 · anterior = 1.3169474478249936 · variacion = 0.015715363339200428 · unidad_variacion = pp · comparables = False · 4 filas

  ```sql
  -- actual: parámetros ["2026-04-20"]
  SELECT s.region AS region, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
  FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.semana_inicio IN (?)
  GROUP BY s.region
  ORDER BY valor DESC
  ```

  ```sql
  -- anterior: parámetros ["2026-03-23", "2026-03-30", "2026-04-06", "2026-04-13"]
  SELECT s.region AS region, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
  FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.semana_inicio IN (?, ?, ?, ?)
  GROUP BY s.region
  ORDER BY valor DESC
  ```

### Analista 2

5 vueltas del modelo · US$ 0.0060 · 30.3 s

- Vuelta 1: ver_modelo
- Vuelta 2: calcular, calcular
- Vuelta 3: respuesta final
  - ✗ el control devolvió la respuesta: números sin respaldo 0,93, 0,9332, 0,9615, 1,0309, 1,4803
- Vuelta 4: calcular
- Vuelta 5: respuesta final

**Hallazgo:**

> La tasa de quiebre de la semana del 20 al 26 de abril de 2026 fue 1,3327 %, contra 1,1700 % en la misma semana de 2025 (variación de 0,1627 pp). Subieron con claridad frente a lo habitual: Frigorífico Las Lomas S.A. (PR15) llegó a 1,9646 % contra 0,8214 % el año anterior y 0,9332 % de promedio en las cuatro semanas previas; Aguas de la Sierra S.A. (PR06) a 1,9231 % contra 0,8671 % y 0,9615 %; Aceitera del Litoral S.A. (PR03) a 2,0619 % contra 1,0753 % y 1,0309 %; y Bebidas Andina S.A. (PR05) a 2,1930 % contra 0,9217 % y 1,4803 %. Molinos del Plata S.A. (PR01) tiene el valor más alto, 2,6966 % contra 1,6509 % el año anterior, pero es igual a su promedio de las cuatro semanas previas (2,6966 %), así que venía alto desde marzo y no es un salto de esta semana. Conviene verificar PR05, porque su valor de la semana del 13 de abril es idéntico al de esta semana, y varios proveedores repiten exactamente el mismo valor en semanas distintas, lo que sugiere fotos de stock arrastradas.

**Consultas:**

- **[C7] `calcular`** `{"medida": "tasa_quiebre_pct", "filtros": {"semana": "2026-04-20"}, "agrupar_por": ["proveedor", "nombre_proveedor"], "comparar_con": {"semana": "2025-04-21"}}`
  - Resultado: actual = 1.332662811164194 · anterior = 1.169975023005127 · variacion = 0.16268778815906715 · unidad_variacion = pp · comparables = False · 16 filas

  ```sql
  -- actual: parámetros ["2026-04-20"]
  SELECT pr.proveedor_id AS proveedor, pr.nombre AS nombre_proveedor, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
  FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.semana_inicio = ?
  GROUP BY pr.proveedor_id, pr.nombre
  ORDER BY valor DESC
  ```

  ```sql
  -- anterior: parámetros ["2025-04-21"]
  SELECT pr.proveedor_id AS proveedor, pr.nombre AS nombre_proveedor, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
  FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.semana_inicio = ?
  GROUP BY pr.proveedor_id, pr.nombre
  ORDER BY valor DESC
  ```
- **[C8] `calcular`** `{"medida": "tasa_quiebre_pct", "filtros": {"semana": ["2026-03-23", "2026-03-30", "2026-04-06", "2026-04-13"]}, "agrupar_por": ["semana", "proveedor", "nombre_proveedor"]}`
  - Resultado: 64 filas

  ```sql
  -- parámetros ["2026-03-23", "2026-03-30", "2026-04-06", "2026-04-13"]
  SELECT f.semana_inicio AS semana, pr.proveedor_id AS proveedor, pr.nombre AS nombre_proveedor, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
  FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.semana_inicio IN (?, ?, ?, ?)
  GROUP BY f.semana_inicio, pr.proveedor_id, pr.nombre
  ORDER BY valor DESC
  ```
- **[C9] `calcular`** `{"medida": "tasa_quiebre_pct", "filtros": {"semana": ["2026-03-23", "2026-03-30", "2026-04-06", "2026-04-13"]}, "agrupar_por": ["proveedor", "nombre_proveedor"]}`
  - Resultado: 16 filas

  ```sql
  -- parámetros ["2026-03-23", "2026-03-30", "2026-04-06", "2026-04-13"]
  SELECT pr.proveedor_id AS proveedor, pr.nombre AS nombre_proveedor, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
  FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.semana_inicio IN (?, ?, ?, ?)
  GROUP BY pr.proveedor_id, pr.nombre
  ORDER BY valor DESC
  ```

### Analista 3

5 vueltas del modelo · US$ 0.0061 · 24.4 s

- Vuelta 1: ver_modelo
- Vuelta 2: calcular, calcular, calcular, calcular
- Vuelta 3: calcular
- Vuelta 4: respuesta final
  - ✗ el control devolvió la respuesta: números sin respaldo 38, 38, 40
- Vuelta 5: respuesta final

**Hallazgo:**

> Las ventas netas de la semana del 20 al 26 de abril de 2026 fueron $191.589.000, +2,37 % (+$4.440.972) contra la misma semana de 2025; en comparables (solo sucursales abiertas antes del período anterior) bajaron 0,23 % (−$438.508), porque S39 Nuevo Oeste y S40 Altos del Oeste no tenían semana anterior. Las mayores caídas en pesos fueron S31 Sierra Chica (Oeste, −$804.884, −6,15 %), S32 Valle Hermoso (Oeste, −$551.150, −12,79 %), S35 La Quebrada (Oeste, −$327.238, −8,63 %), S03 Puerto Norte (Norte, −$327.067, −7,42 %) y S36 Las Lomas (Oeste, −$312.267, −10,05 %); en porcentaje, S38 El Molino (Oeste, −20,89 %), S37 Pampa Linda (Oeste, −19,85 %), S32 Valle Hermoso (Oeste, −12,79 %), S19 La Ribera (Sur, −12,49 %) y S10 Bajo Hondo (Norte, −12,00 %), y ninguna de ellas perdió días con ventas (7 días en cada semana), así que la caída es de venta y no de días faltantes. El margen bruto % de la cadena pasó de 27,19 % a 26,71 % (variación de −0,48 pp).

**Consultas:**

- **[C10] `calcular`** `{"medida": "ventas_netas", "filtros": {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}}, "agrupar_por": ["sucursal", "nombre_sucursal", "region"], "comparar_con": {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}}}`
  - Resultado: actual = 191589000.0 · anterior = 187148028.0 · variacion = 2.3729729067730276 · unidad_variacion = % · comparables = False · 40 filas

  ```sql
  -- actual: parámetros ["2026-04-20", "2026-04-26"]
  SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, s.region AS region, SUM(v.importe_neto) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  GROUP BY s.sucursal_id, s.nombre, s.region
  ORDER BY valor DESC
  ```

  ```sql
  -- anterior: parámetros ["2025-04-21", "2025-04-27"]
  SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, s.region AS region, SUM(v.importe_neto) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  GROUP BY s.sucursal_id, s.nombre, s.region
  ORDER BY valor DESC
  ```
- **[C11] `calcular`** `{"medida": "dias_con_ventas", "filtros": {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}}, "agrupar_por": ["sucursal", "nombre_sucursal"], "comparar_con": {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}}}`
  - Resultado: actual = 280 · anterior = 266 · variacion = 5.263157894736842 · unidad_variacion = % · comparables = False · 40 filas

  ```sql
  -- actual: parámetros ["2026-04-20", "2026-04-26"]
  SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, COUNT(DISTINCT v.sucursal_id || '|' || CAST(v.fecha AS VARCHAR)) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  GROUP BY s.sucursal_id, s.nombre
  ORDER BY valor DESC
  ```

  ```sql
  -- anterior: parámetros ["2025-04-21", "2025-04-27"]
  SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, COUNT(DISTINCT v.sucursal_id || '|' || CAST(v.fecha AS VARCHAR)) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  GROUP BY s.sucursal_id, s.nombre
  ORDER BY valor DESC
  ```
- **[C12] `calcular`** `{"medida": "ventas_netas", "filtros": {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}}, "comparar_con": {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}}}`
  - Resultado: actual = 191589000.0 · anterior = 187148028.0 · variacion = 2.3729729067730276 · unidad_variacion = % · comparables = False

  ```sql
  -- actual: parámetros ["2026-04-20", "2026-04-26"]
  SELECT SUM(v.importe_neto) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  ```

  ```sql
  -- anterior: parámetros ["2025-04-21", "2025-04-27"]
  SELECT SUM(v.importe_neto) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  ```
- **[C13] `calcular`** `{"medida": "margen_pct", "filtros": {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}}, "comparar_con": {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}}}`
  - Resultado: actual = 26.71120876459395 · anterior = 27.186503568181035 · variacion = -0.475294803587083 · unidad_variacion = pp · comparables = False

  ```sql
  -- actual: parámetros ["2026-04-20", "2026-04-26"]
  SELECT (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  ```

  ```sql
  -- anterior: parámetros ["2025-04-21", "2025-04-27"]
  SELECT (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  ```
- **[C14] `calcular`** `{"medida": "ventas_netas", "filtros": {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}}, "comparar_con": {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}}, "comparables": true}`
  - Resultado: actual = 186709520.0 · anterior = 187148028.0 · variacion = -0.23431077777640275 · unidad_variacion = % · comparables = True

  ```sql
  -- actual: parámetros ["2026-04-20", "2026-04-26", "2025-04-21"]
  SELECT SUM(v.importe_neto) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ? AND s.fecha_apertura <= ?
  ```

  ```sql
  -- anterior: parámetros ["2025-04-21", "2025-04-27", "2025-04-21"]
  SELECT SUM(v.importe_neto) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ? AND s.fecha_apertura <= ?
  ```

### Analista 4

4 vueltas del modelo · US$ 0.0042 · 21.7 s

- Vuelta 1: ver_modelo
- Vuelta 2: calcular, calcular
- Vuelta 3: consultar_sql, calcular
- Vuelta 4: respuesta final

**Hallazgo:**

> Las ventas netas de la cadena subieron 2,37 % (+4.440.972 ARS) entre las dos semanas, pero los productos con mayor caída bajaron de forma propia y no por su subcategoría: el mayor retroceso en pesos fue el sku P0259 (Campo Viejo, Fiambres) con −249.200 ARS (−23,9 %), seguido por P0120 (Valle Alto, Vinos) con −233.640 ARS (−11,1 %) y P0152 (La Pradera, Quesos) con −231.768 ARS (−18,5 %). En porcentaje, la caída más fuerte fue P0216 (Total Care, Shampoo y acondicionador) con −33,3 % pero sobre una base chica (−90.480 ARS), y después P0194 (Lava Fácil, Jabón para ropa) con −19,1 % y P0064 (Hoja Verde, Yerba e infusiones) con −18,4 %, mientras sus subcategorías crecieron o quedaron casi planas. Solo P0152 y P0288 (Las Lomas, Congelados, −13,7 %) tuvieron promociones en alguna de las dos semanas, y ambas en la semana anterior de 2025 (P0152 al 20 % hasta el 24/4/2025; P0288 al 10 % desde el 25/4/2025); los demás productos no tuvieron promociones en ninguna de las dos semanas y los días con venta subieron (280 frente a 266), así que no faltan días.

**Consultas:**

- **[C15] `calcular`** `{"medida": "ventas_netas", "filtros": {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}}, "comparar_con": {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}}, "agrupar_por": ["producto", "subcategoria", "marca"], "orden": "asc", "limite": 15}`
  - Resultado: actual = 191589000.0 · anterior = 187148028.0 · variacion = 2.3729729067730276 · unidad_variacion = % · comparables = False · 15 filas

  ```sql
  -- actual: parámetros ["2026-04-20", "2026-04-26"]
  SELECT p.sku AS producto, p.subcategoria AS subcategoria, p.marca AS marca, SUM(v.importe_neto) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  GROUP BY p.sku, p.subcategoria, p.marca
  ORDER BY valor DESC
  ```

  ```sql
  -- anterior: parámetros ["2025-04-21", "2025-04-27"]
  SELECT p.sku AS producto, p.subcategoria AS subcategoria, p.marca AS marca, SUM(v.importe_neto) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  GROUP BY p.sku, p.subcategoria, p.marca
  ORDER BY valor DESC
  ```
- **[C16] `calcular`** `{"medida": "ventas_netas", "filtros": {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}}, "comparar_con": {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}}, "agrupar_por": ["subcategoria"], "orden": "asc"}`
  - Resultado: actual = 191589000.0 · anterior = 187148028.0 · variacion = 2.3729729067730276 · unidad_variacion = % · comparables = False · 27 filas

  ```sql
  -- actual: parámetros ["2026-04-20", "2026-04-26"]
  SELECT p.subcategoria AS subcategoria, SUM(v.importe_neto) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  GROUP BY p.subcategoria
  ORDER BY valor DESC
  ```

  ```sql
  -- anterior: parámetros ["2025-04-21", "2025-04-27"]
  SELECT p.subcategoria AS subcategoria, SUM(v.importe_neto) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  GROUP BY p.subcategoria
  ORDER BY valor DESC
  ```
- **[C17] `consultar_sql`** `{"sql": "SELECT sku, promocion_id, nombre, descuento_pct, fecha_desde, fecha_hasta FROM promociones WHERE sku IN ('P0259','P0120','P0152','P0265','P0284','P0288','P0064','P0189','P0216','P0194') AND fecha_desde <= '2026-04-26' AND fecha_hasta >= '2026-04-20' OR (sku IN ('P0259','P0120','P0152','P0265','P0284','P0288','P0064','P0189','P0216','P0194') AND fecha_desde <= '2025-04-27' AND fecha_hasta >= '2025-04-21') ORDER BY sku, fecha_desde"}`
  - Resultado: 2 filas

  ```sql
  -- parámetros null
  SELECT sku, promocion_id, nombre, descuento_pct, fecha_desde, fecha_hasta FROM promociones WHERE sku IN ('P0259','P0120','P0152','P0265','P0284','P0288','P0064','P0189','P0216','P0194') AND fecha_desde <= '2026-04-26' AND fecha_hasta >= '2026-04-20' OR (sku IN ('P0259','P0120','P0152','P0265','P0284','P0288','P0064','P0189','P0216','P0194') AND fecha_desde <= '2025-04-27' AND fecha_hasta >= '2025-04-21') ORDER BY sku, fecha_desde
  ```
- **[C18] `calcular`** `{"medida": "dias_con_ventas", "filtros": {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}}, "comparar_con": {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}}}`
  - Resultado: actual = 280 · anterior = 266 · variacion = 5.263157894736842 · unidad_variacion = % · comparables = False

  ```sql
  -- actual: parámetros ["2026-04-20", "2026-04-26"]
  SELECT COUNT(DISTINCT v.sucursal_id || '|' || CAST(v.fecha AS VARCHAR)) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  ```

  ```sql
  -- anterior: parámetros ["2025-04-21", "2025-04-27"]
  SELECT COUNT(DISTINCT v.sucursal_id || '|' || CAST(v.fecha AS VARCHAR)) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  ```

## 3. Coordinador: la redacción

2 intento(s) · US$ 0.0090 · 44.8 s

- Intento 1: el control encontró: forma: el punto «Las mayores caídas en pesos son de Oeste, como Sie…» da números que no se ven en su gráfico: el gráfico muestra el cambio de ventas netas, en pesos y sus etiquetas dicen Nuevo Oeste · Oeste +$ 3.352.190, Altos del Oeste · Oeste +$ 1.527.290, Barrio Jardín · Centro +$ 598.944, Los Ceibos · Norte +$ 512.248, Villa Arenal · Norte +$ 381.434, Monte Chico · Norte +$ 285.556. Usá esos números tal como se ven (redondeados igual), o elegí la consulta que muestra lo que dice el punto; editor: El título dice "sin faltar días", pero no se entiende qué días: el punto 3 habla de días con ventas. Además, el título no aclara que la caída es en pesos. Propuesta: «Y las ventas en pesos caen en Oeste, aunque ninguna sucursal dejó de vender días.»; editor: En la bajada, el "porque" no explica la diferencia entre ventas netas y comparables. Lo que hace es decir qué sucursales quedan afuera de comparables. Propuesta: «Las ventas netas subieron 2,4 % [C12], pero en comparables, que excluyen dos sucursales nuevas sin semana anterior, bajaron 0,2 % [C14].»; editor: En el punto 2 no se dice que la métrica es el quiebre, así que no se conecta con el título, que habla del quiebre de esos proveedores. Propuesta: «El quiebre de cuatro proveedores subió entre 1,0 y 1,3 pp contra el año pasado: Bebidas Andina, Las Lomas, Aguas de la Sierra y Aceitera [C7].»; editor: En el punto 3, "como Sierra Chica..." suena raro: no queda claro que esos dos ejemplos son las mayores caídas. Propuesta: «Las mayores caídas en pesos son de Oeste: Sierra Chica (−6,2 %) y Valle Hermoso (−12,8 %) [C10]; ninguna perdió días con ventas [C11].»
- Intento 2: el control no encontró problemas

Lo que escribió (el código pone los valores de los indicadores y dibuja los gráficos):

```json
{
 "titulo": "El quiebre sube en Sur y Centro, y las ventas en pesos caen en Oeste, aunque ninguna sucursal dejó de vender días",
 "bajada": "Las ventas netas subieron 2,4 % [C12], pero en comparables, que excluyen dos sucursales nuevas sin semana anterior, bajaron 0,2 % [C14].",
 "indicadores": [
  {
   "nombre": "Quiebre de stock %",
   "consulta": "C4",
   "dato": "actual",
   "variacion": "variacion",
   "contra": "vs misma semana de 2025"
  },
  {
   "nombre": "Ventas netas comparables",
   "consulta": "C14",
   "dato": "actual",
   "variacion": "variacion",
   "contra": "vs año anterior"
  }
 ],
 "puntos": [
  {
   "texto": "Centro y Sur están por encima de sus cuatro semanas previas, con +0,18 pp y +0,16 pp [C6].",
   "grafico": {
    "consulta": "C6",
    "destacar": [
     "Centro",
     "Sur"
    ]
   }
  },
  {
   "texto": "El quiebre de cinco proveedores subió entre 1,0 y 1,3 pp contra el año pasado: Bebidas Andina, Las Lomas, Aguas de la Sierra, Aceitera y Molinos del Plata [C7].",
   "grafico": null
  },
  {
   "texto": "Las dos mayores caídas en pesos son de Oeste: Sierra Chica (−6,2 %) y Valle Hermoso (−12,8 %) [C10]; ninguna perdió días con ventas [C11].",
   "grafico": null
  }
 ]
}
```

## 4. Costo y tiempo

Los segundos son la suma de las llamadas: los analistas trabajan en paralelo (decisión 74), así que el tiempo de reloj es menor.

| Paso | Llamadas | Tokens de entrada | Tokens de salida | US$ | Segundos (suma) |
|---|---|---|---|---|---|
| Plan | 1 | 186 | 6,797 | 0.0035 | 30.2 |
| Analistas | 19 | 52 | 20,833 | 0.0211 | 103.2 |
| Redacción | 2 | 1,341 | 10,113 | 0.0090 | 44.8 |
| **Total** | 23 | 2,987 | 40,157 | 0.0349 | 189.0 |

