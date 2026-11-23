-- [C4] Tasa de quiebre %. Porcentaje de combinaciones producto-sucursal con stock cero en la foto del lunes. De qué: toda la cadena. Cuándo: la semana del 20-04-2026. Contra: la semana del 21-04-2025, con todas las sucursales. Abierto por región, de mayor a menor.
-- actual
-- parámetros: ['2026-04-20']
SELECT s.region AS region, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.semana_inicio IN (?)
GROUP BY s.region
ORDER BY valor DESC;

-- anterior
-- parámetros: ['2025-04-21']
SELECT s.region AS region, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.semana_inicio IN (?)
GROUP BY s.region
ORDER BY valor DESC;

-- [C6] Tasa de quiebre %. Porcentaje de combinaciones producto-sucursal con stock cero en la foto del lunes. De qué: toda la cadena. Cuándo: la semana del 20-04-2026. Contra: la semana del 23-03-2026, 30-03-2026, 06-04-2026 o 13-04-2026, con todas las sucursales. Abierto por región, de mayor a menor.
-- actual
-- parámetros: ['2026-04-20']
SELECT s.region AS region, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.semana_inicio IN (?)
GROUP BY s.region
ORDER BY valor DESC;

-- anterior
-- parámetros: ['2026-03-23', '2026-03-30', '2026-04-06', '2026-04-13']
SELECT s.region AS region, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.semana_inicio IN (?, ?, ?, ?)
GROUP BY s.region
ORDER BY valor DESC;

-- [C7] Tasa de quiebre %. Porcentaje de combinaciones producto-sucursal con stock cero en la foto del lunes. De qué: toda la cadena. Cuándo: la semana del 20-04-2026. Contra: la semana del 21-04-2025, con todas las sucursales. Abierto por proveedor, de mayor a menor.
-- actual
-- parámetros: ['2026-04-20']
SELECT pr.proveedor_id AS proveedor, pr.nombre AS nombre_proveedor, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.semana_inicio = ?
GROUP BY pr.proveedor_id, pr.nombre
ORDER BY valor DESC;

-- anterior
-- parámetros: ['2025-04-21']
SELECT pr.proveedor_id AS proveedor, pr.nombre AS nombre_proveedor, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.semana_inicio = ?
GROUP BY pr.proveedor_id, pr.nombre
ORDER BY valor DESC;

-- [C10] Ventas netas. Ventas brutas menos descuentos y devoluciones. De qué: toda la cadena. Cuándo: del 20-04-2026 al 26-04-2026. Contra: del 21-04-2025 al 27-04-2025, con todas las sucursales. Abierto por sucursal y región, de mayor a menor.
-- actual
-- parámetros: ['2026-04-20', '2026-04-26']
SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, s.region AS region, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?
GROUP BY s.sucursal_id, s.nombre, s.region
ORDER BY valor DESC;

-- anterior
-- parámetros: ['2025-04-21', '2025-04-27']
SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, s.region AS region, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?
GROUP BY s.sucursal_id, s.nombre, s.region
ORDER BY valor DESC;

-- [C11] Días con ventas. Cuántos días vendió cada sucursal, sumados (una sucursal en un día cuenta 1). De qué: toda la cadena. Cuándo: del 20-04-2026 al 26-04-2026. Contra: del 21-04-2025 al 27-04-2025, con todas las sucursales. Abierto por sucursal, de mayor a menor.
-- actual
-- parámetros: ['2026-04-20', '2026-04-26']
SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, COUNT(DISTINCT v.sucursal_id || '|' || CAST(v.fecha AS VARCHAR)) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?
GROUP BY s.sucursal_id, s.nombre
ORDER BY valor DESC;

-- anterior
-- parámetros: ['2025-04-21', '2025-04-27']
SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, COUNT(DISTINCT v.sucursal_id || '|' || CAST(v.fecha AS VARCHAR)) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?
GROUP BY s.sucursal_id, s.nombre
ORDER BY valor DESC;

-- [C12] Ventas netas. Ventas brutas menos descuentos y devoluciones. De qué: toda la cadena. Cuándo: del 20-04-2026 al 26-04-2026. Contra: del 21-04-2025 al 27-04-2025, con todas las sucursales.
-- actual
-- parámetros: ['2026-04-20', '2026-04-26']
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?;

-- anterior
-- parámetros: ['2025-04-21', '2025-04-27']
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?;

-- [C14] Ventas netas. Ventas brutas menos descuentos y devoluciones. De qué: toda la cadena. Cuándo: del 20-04-2026 al 26-04-2026. Contra: del 21-04-2025 al 27-04-2025, solo con las sucursales que estaban abiertas en los dos períodos (comparables).
-- actual
-- parámetros: ['2026-04-20', '2026-04-26', '2025-04-21']
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ? AND s.fecha_apertura <= ?;

-- anterior
-- parámetros: ['2025-04-21', '2025-04-27', '2025-04-21']
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ? AND s.fecha_apertura <= ?;

