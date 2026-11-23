-- [C1] tasa_quiebre_pct · {"semana": "2026-04-20"} · contra {"semana": "2025-04-21"} · por region
-- actual
-- parámetros: ['2026-04-20']
SELECT s.region AS region, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.semana_inicio = ?
GROUP BY s.region
ORDER BY valor DESC;

-- anterior
-- parámetros: ['2025-04-21']
SELECT s.region AS region, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.semana_inicio = ?
GROUP BY s.region
ORDER BY valor DESC;

-- [C2] tasa_quiebre_pct · {"semana": "2026-04-20"} · contra {"semana": "2025-04-21"} · por proveedor, nombre_proveedor
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

-- [C3] ventas_netas · {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}} · contra {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}} · por sucursal, nombre_sucursal, region, formato
-- actual
-- parámetros: ['2026-04-20', '2026-04-26']
SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, s.region AS region, s.formato AS formato, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?
GROUP BY s.sucursal_id, s.nombre, s.region, s.formato
ORDER BY valor DESC;

-- anterior
-- parámetros: ['2025-04-21', '2025-04-27']
SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, s.region AS region, s.formato AS formato, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?
GROUP BY s.sucursal_id, s.nombre, s.region, s.formato
ORDER BY valor DESC;

-- [C4] ventas_netas · {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}} · contra {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}} (comparables)
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

-- [C8] ventas_netas · {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}} · contra {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}} · por subcategoria
-- actual
-- parámetros: ['2026-04-20', '2026-04-26']
SELECT p.subcategoria AS subcategoria, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?
GROUP BY p.subcategoria
ORDER BY valor DESC;

-- anterior
-- parámetros: ['2025-04-21', '2025-04-27']
SELECT p.subcategoria AS subcategoria, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?
GROUP BY p.subcategoria
ORDER BY valor DESC;

-- [C12] efectos_margen · {"fecha": {"desde": "2026-04-20", "hasta": "2026-04-26"}} · contra {"fecha": {"desde": "2025-04-21", "hasta": "2025-04-27"}}
-- precio_promedio actual
-- parámetros: ['2026-04-20', '2026-04-26']
SELECT SUM(v.importe_neto) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?;

-- precio_promedio anterior
-- parámetros: ['2025-04-21', '2025-04-27']
SELECT SUM(v.importe_neto) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?;

-- costo_unitario actual
-- parámetros: ['2026-04-20', '2026-04-26']
SELECT SUM(v.costo) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?;

-- costo_unitario anterior
-- parámetros: ['2025-04-21', '2025-04-27']
SELECT SUM(v.costo) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?;

