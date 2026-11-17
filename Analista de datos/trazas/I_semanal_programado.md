> **Informe generado solo (semana 4).** Lo lanzó `informe_programado.py`, el mismo que corre el temporizador de systemd
> los lunes a las 8, simulando el lunes 27-04-2026 (`--hoy 2026-04-27`), porque la base termina el 30-04-2026. Le tocó
> el semanal del 20 al 26-04-2026; nadie escribió el pedido: lo arma el código según el calendario (decisiones 65 y 66).
> Línea del historial (`salidas/programado/historial.txt`):
> `2026-11-17 10:16 · lunes 2026-04-27 (fecha simulada) · semana-2026-04-20 · bien · 73 s`
> El PDF y el SQL de las consultas citadas están al lado: `I_semanal_programado.pdf` y `I_semanal_programado.sql`.

# Traza: Preparame un informe ejecutivo de la semana del lunes 20-04-2026 al domingo 26-04-2026, sobre qué requiere la atención de la gerencia esta semana: la tasa de quiebre de stock de la semana, por región y por proveedor; las sucursales con mayor caída de ventas netas; y los productos con caída fuerte. Todo contra la misma semana del año anterior (del lunes 21-04-2025 al domingo 27-04-2025). Las ventas netas y el margen del total, solo como contexto.

Corrida `20261117-101535-15e5` · versión del diseño `d8d5f0` · `claude-haiku-5-5`. Para volver a correrla:

```
.venv/bin/python informes.py "Preparame un informe ejecutivo de la semana del lunes 20-04-2026 al domingo 26-04-2026, sobre qué requiere la atención de la gerencia esta semana: la tasa de quiebre de stock de la semana, por región y por proveedor; las sucursales con mayor caída de ventas netas; y los productos con caída fuerte. Todo contra la misma semana del año anterior (del lunes 21-04-2025 al domingo 27-04-2025). Las ventas netas y el margen del total, solo como contexto." salidas/programado/semana-2026-04-20
```

Resultado: `salidas/programado/semana-2026-04-20/informe.pdf` · SQL de las consultas citadas: `salidas/programado/semana-2026-04-20/consultas.sql`

## 1. Coordinador: el plan

Tipo: **informe** · Informe ejecutivo semanal: semana del 20 al 26 de abril de 2026 contra la misma semana de 2025

Supuestos:
- La semana se toma en calendario comercial, de lunes a domingo, como indican las fechas del pedido. No se usa el calendario fiscal.
- La comparación es contra la semana calendario del año anterior: del 21 al 27 de abril de 2025.
- La tasa de quiebre usa la foto de stock del lunes de cada semana: lunes 20-04-2026 contra lunes 21-04-2025.
- Las caídas de ventas por sucursal y por producto se miden en total, sin filtrar por comparables. Una sucursal que no tenga venta en la semana del año anterior aparecerá sin base de comparación y se informará aparte.
- Ventas netas y margen del total se muestran solo como contexto, sin desglose.
- El pedido no pide umbrales de caída: el informe muestra las mayores caídas en pesos y en porcentaje, y el analista no aplica un corte fijo.

**Pregunta 1.** ¿Cuál fue la tasa de quiebre de stock % en la semana del lunes 20-04-2026 (foto de stock del lunes) comparada con la semana del lunes 21-04-2025, por región y por proveedor (código y nombre)? Todas las sucursales y todas las categorías.

- Para qué: Mostrar dónde se concentra el quiebre de stock de la semana, para que gerencia sepa qué regiones y proveedores requieren atención.
- Consulta sugerida: tasa_quiebre_pct, semana 2026-04-20 comparada con semana 2025-04-21, agrupada por región
- Consulta sugerida: tasa_quiebre_pct, semana 2026-04-20 comparada con semana 2025-04-21, agrupada por proveedor y nombre_proveedor
- No mirar: No abrir por producto ni por sucursal. No comentar ventas ni margen. No evaluar causas: solo medir el quiebre.

**Pregunta 2.** ¿Qué sucursales tuvieron la mayor caída de ventas netas en pesos y en porcentaje en la semana del 20 al 26 de abril de 2026, comparada con la semana del 21 al 27 de abril de 2025? Todas las regiones y formatos, sin filtrar por comparables.

- Para qué: Identificar qué sucursales tuvieron la mayor caída de ventas netas en la semana.
- Consulta sugerida: ventas_netas, semana del 2026-04-20 al 2026-04-26 comparada con 2025-04-21 al 2025-04-27, agrupada por sucursal y nombre_sucursal, con región y formato
- No mirar: No analizar productos ni proveedores de cada sucursal. No calcular quiebre. Las sucursales sin base del año anterior se informan aparte, sin comparar.

**Pregunta 3.** ¿Qué productos tuvieron la mayor caída de ventas netas en pesos y en porcentaje en la semana del 20 al 26 de abril de 2026, comparada con la semana del 21 al 27 de abril de 2025, en todas las sucursales? Además, para los productos con mayor caída, listar las promociones del período de su subcategoría y revisar si hubo promociones en productos parecidos.

- Para qué: Identificar los productos con caída fuerte de ventas netas y verificar si pudieron estar afectados por promociones de su subcategoría.
- Consulta sugerida: ventas_netas, semana del 2026-04-20 al 2026-04-26 comparada con 2025-04-21 al 2025-04-27, agrupada por sku y descripcion, con subcategoría y marca
- Consulta sugerida: ventas_netas, semana del 2026-04-20 al 2026-04-26 comparada con 2025-04-21 al 2025-04-27, agrupada por subcategoría, para ver la caída de la subcategoría de los productos más afectados
- No mirar: No analizar margen ni costo. No abrir por sucursal. No repetir el análisis de quiebre ni de sucursales.

**Pregunta 4.** ¿Cuál fue la variación de ventas netas y del margen bruto % de la cadena total en la semana del 20 al 26 de abril de 2026, comparada con la semana del 21 al 27 de abril de 2025?

- Para qué: Dar el contexto de la semana en ventas netas y margen del total de la cadena, sin desglose.
- Consulta sugerida: ventas_netas del total, semana del 2026-04-20 al 2026-04-26 comparada con 2025-04-21 al 2025-04-27
- Consulta sugerida: efectos_margen del total, semana del 2026-04-20 al 2026-04-26 comparada con 2025-04-21 al 2025-04-27
- No mirar: Solo el total de la cadena, sin desglose por sucursal, región, proveedor ni producto. No repetir lo que ya informan las otras preguntas.

## 2. Analistas: una llamada por pregunta, cada una desde cero

### Analista 1

3 vueltas del modelo · US$ 0.0023 · 11.9 s

- Vuelta 1: ver_modelo
- Vuelta 2: calcular, calcular
- Vuelta 3: respuesta final

**Hallazgo:**

> La tasa de quiebre de la semana del 20-04-2026 fue 1,33 %, contra 1,17 % en la semana del 21-04-2025: +0,16 pp en total. El aumento se concentra en Sur (1,41 %, +0,52 pp) y Centro (1,44 %, +0,24 pp), mientras que Norte y Oeste bajaron. Por proveedor, suben sobre todo Bebidas Andina S.A. (PR05, 2,19 %, +1,27 pp), Frigorífico Las Lomas S.A. (PR15, 1,96 %, +1,14 pp), Aguas de la Sierra S.A. (PR06, 1,92 %, +1,06 pp), Molinos del Plata S.A. (PR01, 2,70 %, +1,05 pp) y Aceitera del Litoral S.A. (PR03, 2,06 %, +0,99 pp), así que el alza es más concentrada que generalizada.

**Consultas:**

- **[C1] `calcular`** `{"medida": "tasa_quiebre_pct", "filtros": {"semana": "2026-04-20"}, "comparar_con": {"semana": "2025-04-21"}, "agrupar_por": ["region"]}`
  - Resultado: actual = 1.332662811164194 · anterior = 1.169975023005127 · variacion = 0.16268778815906715 · unidad_variacion = pp · comparables = False · 4 filas

  ```sql
  -- actual: parámetros ["2026-04-20"]
  SELECT s.region AS region, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
  FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.semana_inicio = ?
  GROUP BY s.region
  ORDER BY valor DESC
  ```

  ```sql
  -- anterior: parámetros ["2025-04-21"]
  SELECT s.region AS region, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
  FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.semana_inicio = ?
  GROUP BY s.region
  ORDER BY valor DESC
  ```
- **[C2] `calcular`** `{"medida": "tasa_quiebre_pct", "filtros": {"semana": "2026-04-20"}, "comparar_con": {"semana": "2025-04-21"}, "agrupar_por": ["proveedor", "nombre_proveedor"]}`
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

### Analista 2

5 vueltas del modelo · US$ 0.0047 · 25.3 s

- Vuelta 1: ver_modelo
- Vuelta 2: calcular
- Vuelta 3: respuesta final
  - ✗ el control devolvió la respuesta: números sin respaldo 2.959.896, 438.508, 0,23, 71,8, 4.123.444, 438.508, 0,23, 2.959.895,5, 4.123.444, 2.959.895,5, 4.123.444, 71,8, 438.508, 438.508, 0,23, 2.959.895,5, 438.508
- Vuelta 4: calcular
- Vuelta 5: respuesta final

**Hallazgo:**

> En la semana del 20 al 26 de abril de 2026 las mayores caídas en pesos fueron Sierra Chica (S31, Oeste, hiper), con ventas de 12.280.560 ARS frente a 13.085.443,5 ARS del año anterior (-6,15 %), y Valle Hermoso (S32, Oeste, super), con 3.756.650 ARS frente a 4.307.800 ARS (-12,79 %). En porcentaje lideraron El Molino (S38, Oeste, express), con 796.150 ARS frente a 1.006.380 ARS (-20,89 %), y Pampa Linda (S37, Oeste, express), con 775.610 ARS frente a 967.690 ARS (-19,85 %), seguidas por La Ribera (S19, Sur, express, -12,49 %) y Bajo Hondo (S10, Norte, express, -12,00 %). La variación total de la cadena fue de +4.440.972 ARS (+2,37 %), pero sin las sucursales sin base del año anterior, Altos del Oeste (S40, Oeste, express, 1.527.290 ARS) y Nuevo Oeste (S39, Oeste, super, 3.352.190 ARS), que se informan aparte sin comparar, la variación comparable fue de -438.508 ARS (-0,23 %).

**Consultas:**

- **[C3] `calcular`** `{"medida": "ventas_netas", "filtros": {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}}, "comparar_con": {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}}, "agrupar_por": ["sucursal", "nombre_sucursal", "region", "formato"], "orden": "asc"}`
  - Resultado: actual = 191589000.0 · anterior = 187148028.0 · variacion = 2.3729729067730276 · unidad_variacion = % · comparables = False · 40 filas

  ```sql
  -- actual: parámetros ["2026-04-20", "2026-04-26"]
  SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, s.region AS region, s.formato AS formato, SUM(v.importe_neto) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  GROUP BY s.sucursal_id, s.nombre, s.region, s.formato
  ORDER BY valor DESC
  ```

  ```sql
  -- anterior: parámetros ["2025-04-21", "2025-04-27"]
  SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, s.region AS region, s.formato AS formato, SUM(v.importe_neto) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  GROUP BY s.sucursal_id, s.nombre, s.region, s.formato
  ORDER BY valor DESC
  ```
- **[C4] `calcular`** `{"medida": "ventas_netas", "filtros": {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}}, "comparar_con": {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}}, "comparables": true}`
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

### Analista 3

8 vueltas del modelo · US$ 0.0130 · 30.9 s

- Vuelta 1: ver_modelo
- Vuelta 2: calcular
  - ✗ error de tool, que Haiku recibe para corregir: calcular: Error executing tool calcular: ValueError: Dimensión desconocida: sku. Para filtrar por sku, usá producto. Dimensiones válidas para ventas_netas: fecha, anio, mes, anio_fiscal, trimestre_fiscal, mes_f
- Vuelta 3: calcular
- Vuelta 4: calcular
- Vuelta 5: calcular
- Vuelta 6: calcular, consultar_sql
- Vuelta 7: consultar_sql
- Vuelta 8: respuesta final

**Hallazgo:**

> Por pesos, la mayor caída fue P0259 (Fiambres, Campo Viejo) con −249.200 ARS (−23,9 %), seguida de P0120 (Vinos, Valle Alto, −233.640 ARS) y P0152 (Quesos, La Pradera, −231.768 ARS, −18,5 %). Por porcentaje lideran P0216 (Shampoo y acondicionador, Total Care, −33,3 %), P0136 (Yogures, La Pradera, −30,5 %) y P0047 (Galletitas, Molinos del Plata, −30,5 %), aunque con bases chicas. La caída no se concentra en una sola subcategoría: Vinos resta −346.470 ARS y Fiambres −143.720 ARS netos, y cuatro de los quince primeros en pesos son Fiambres; mientras tanto las ventas netas totales subieron +2,4 % (+4.440.972 ARS). No hubo promociones vigentes en la semana para ningún producto, así que no aparecen promociones en las subcategorías afectadas, aunque no se puede concluir causalidad.

**Consultas:**

- **[C5] `calcular`** `{"medida": "ventas_netas", "filtros": {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}}, "comparar_con": {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}}, "agrupar_por": ["producto", "subcategoria", "marca"], "orden": "asc", "limite": 10}`
  - Resultado: actual = 191589000.0 · anterior = 187148028.0 · variacion = 2.3729729067730276 · unidad_variacion = % · comparables = False · 10 filas

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
- **[C6] `calcular`** `{"medida": "ventas_netas", "filtros": {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}}, "comparar_con": {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}}, "agrupar_por": ["producto", "subcategoria", "marca"], "orden": "asc", "limite": 100}`
  - Resultado: actual = 191589000.0 · anterior = 187148028.0 · variacion = 2.3729729067730276 · unidad_variacion = % · comparables = False · 100 filas

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
- **[C7] `calcular`** `{"medida": "ventas_netas", "filtros": {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}}, "comparar_con": {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}}, "agrupar_por": ["producto", "subcategoria", "marca"], "orden": "asc", "limite": 400}`
  - Resultado: actual = 191589000.0 · anterior = 187148028.0 · variacion = 2.3729729067730276 · unidad_variacion = % · comparables = False · 308 filas

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
- **[C8] `calcular`** `{"medida": "ventas_netas", "filtros": {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}}, "comparar_con": {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}}, "agrupar_por": ["subcategoria"], "orden": "asc", "limite": 8}`
  - Resultado: actual = 191589000.0 · anterior = 187148028.0 · variacion = 2.3729729067730276 · unidad_variacion = % · comparables = False · 8 filas

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
- **[C9] `consultar_sql`** `{"sql": "SELECT pr.promocion_id, pr.nombre, pr.sku, p.descripcion, p.subcategoria, p.marca, pr.descuento_pct, pr.fecha_desde, pr.fecha_hasta FROM promociones pr JOIN productos p ON pr.sku = p.sku WHERE pr.fecha_desde <= DATE '2026-04-26' AND pr.fecha_hasta >= DATE '2026-04-20' AND p.subcategoria IN ('Fiambres', 'Vinos', 'Quesos', 'Congelados', 'Shampoo y acondicionador', 'Yogures', 'Mantecas y cremas', 'Aguas', 'Galletitas', 'Cuidado dental') ORDER BY p.subcategoria, pr.sku"}`
  - Resultado: 0 filas

  ```sql
  -- parámetros null
  SELECT pr.promocion_id, pr.nombre, pr.sku, p.descripcion, p.subcategoria, p.marca, pr.descuento_pct, pr.fecha_desde, pr.fecha_hasta FROM promociones pr JOIN productos p ON pr.sku = p.sku WHERE pr.fecha_desde <= DATE '2026-04-26' AND pr.fecha_hasta >= DATE '2026-04-20' AND p.subcategoria IN ('Fiambres', 'Vinos', 'Quesos', 'Congelados', 'Shampoo y acondicionador', 'Yogures', 'Mantecas y cremas', 'Aguas', 'Galletitas', 'Cuidado dental') ORDER BY p.subcategoria, pr.sku
  ```
- **[C10] `consultar_sql`** `{"sql": "SELECT pr.promocion_id, pr.nombre, pr.sku, p.subcategoria, pr.descuento_pct, pr.fecha_desde, pr.fecha_hasta FROM promociones pr JOIN productos p ON pr.sku = p.sku WHERE pr.fecha_desde <= DATE '2026-04-26' AND pr.fecha_hasta >= DATE '2026-04-20' ORDER BY p.subcategoria"}`
  - Resultado: 0 filas

  ```sql
  -- parámetros null
  SELECT pr.promocion_id, pr.nombre, pr.sku, p.subcategoria, pr.descuento_pct, pr.fecha_desde, pr.fecha_hasta FROM promociones pr JOIN productos p ON pr.sku = p.sku WHERE pr.fecha_desde <= DATE '2026-04-26' AND pr.fecha_hasta >= DATE '2026-04-20' ORDER BY p.subcategoria
  ```

### Analista 4

4 vueltas del modelo · US$ 0.0021 · 9.9 s

- Vuelta 1: ver_modelo
- Vuelta 2: calcular, calcular, calcular
- Vuelta 3: calcular
- Vuelta 4: respuesta final

**Hallazgo:**

> En la semana del 20 al 26 de abril de 2026, las ventas netas fueron de $191.589.000, un 2,37 % más que la semana del 21 al 27 de abril de 2025; en comparables (mismas sucursales) caen un 0,23 %, así que el crecimiento total viene de sucursales nuevas. El margen bruto % fue de 26,71 %, unos 0,48 pp menos que el 27,19 % de 2025: el efecto precio explica −0,27 pp (el precio promedio bajó un 0,37 %) y el efecto costo −0,20 pp (el costo por unidad subió un 0,28 %).

**Consultas:**

- **[C11] `calcular`** `{"medida": "ventas_netas", "filtros": {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}}, "comparar_con": {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}}}`
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
- **[C12] `calcular`** `{"medida": "efectos_margen", "filtros": {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}}, "comparar_con": {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}}}`
  - Resultado: comparables = False

  ```sql
  -- precio_promedio actual: parámetros ["2026-04-20", "2026-04-26"]
  SELECT SUM(v.importe_neto) / NULLIF(SUM(v.unidades), 0) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  ```

  ```sql
  -- precio_promedio anterior: parámetros ["2025-04-21", "2025-04-27"]
  SELECT SUM(v.importe_neto) / NULLIF(SUM(v.unidades), 0) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  ```

  ```sql
  -- costo_unitario actual: parámetros ["2026-04-20", "2026-04-26"]
  SELECT SUM(v.costo) / NULLIF(SUM(v.unidades), 0) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  ```

  ```sql
  -- costo_unitario anterior: parámetros ["2025-04-21", "2025-04-27"]
  SELECT SUM(v.costo) / NULLIF(SUM(v.unidades), 0) AS valor
  FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
  WHERE f.fecha BETWEEN ? AND ?
  ```
- **[C13] `calcular`** `{"medida": "margen_pct", "filtros": {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}}}`
  - Resultado: valor = 26.71120876459395

  ```sql
  -- parámetros ["2026-04-20", "2026-04-26"]
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

## 3. Coordinador: la redacción

1 intento(s) · US$ 0.0098 · 21.0 s

- Intento 1: el control no encontró problemas

Lo que escribió (el código pone los valores de los indicadores y dibuja los gráficos):

```json
{
 "titulo": "El quiebre sube en Sur y en cinco proveedores, no en toda la red",
 "puntos": [
  "El quiebre subió 0,16 pp, a 1,33 % [C1]: es un aumento chico en total, concentrado en Sur y en unos pocos proveedores.",
  "Las ventas comparables bajan 0,23 % [C4]; la caída se concentra en sucursales de Oeste como Sierra Chica y Valle Hermoso [C3].",
  "Vinos resta 346.470 ARS en la semana [C8] y no hubo promociones vigentes que lo expliquen [C9]."
 ],
 "acciones": [
  "Pedir a compras revisar la reposición de Bebidas Andina y Frigorífico Las Lomas, los proveedores con mayor suba del quiebre.",
  "Pedir al responsable de Oeste revisar Sierra Chica y Valle Hermoso antes de atribuir la caída a la demanda."
 ],
 "indicadores": [
  {
   "nombre": "Quiebre de stock",
   "consulta": "C1",
   "dato": "actual",
   "variacion": "variacion",
   "contra": "vs misma semana 2025"
  },
  {
   "nombre": "Ventas netas comparables",
   "consulta": "C4",
   "dato": "actual",
   "variacion": "variacion",
   "contra": "vs misma semana 2025, mismas sucursales"
  },
  {
   "nombre": "Margen bruto %",
   "consulta": "C12",
   "dato": "margen_pct_actual",
   "variacion": "variacion_pp",
   "contra": "vs misma semana 2025"
  }
 ],
 "pruebas": [
  {
   "titulo": "Sur y Centro concentran la suba del quiebre",
   "consulta": "C1",
   "destacar": [
    "Sur",
    "Centro"
   ],
   "texto": "Sur subió +0,52 pp y Centro +0,24 pp [C1]. Norte y Oeste bajaron."
  },
  {
   "titulo": "Cinco proveedores explican la suba del quiebre",
   "consulta": "C2",
   "destacar": [
    "PR05",
    "PR15"
   ],
   "texto": "Bebidas Andina subió +1,27 pp y Frigorífico Las Lomas +1,14 pp [C2]. También suben Aguas de la Sierra y Molinos del Plata."
  }
 ]
}
```

## 4. Costo y tiempo

| Paso | Llamadas | Tokens de entrada | Tokens de salida | US$ | Segundos |
|---|---|---|---|---|---|
| Plan | 1 | 186 | 3,463 | 0.0025 | 16.5 |
| Analistas | 20 | 50 | 14,149 | 0.0222 | 78.0 |
| Redacción | 1 | 4 | 4,486 | 0.0098 | 21.0 |
| **Total** | 22 | 240 | 22,098 | 0.0345 | 115.5 |

