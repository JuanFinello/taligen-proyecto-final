-- [C1] Tasa de quiebre %. Porcentaje de combinaciones producto-sucursal con stock cero en la foto del lunes. De qué: toda la cadena. Cuándo: la semana del 12-05-2025. Contra: la semana del 13-05-2024, con todas las sucursales.
-- actual
-- parámetros: ['2025-05-12']
SELECT AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.semana_inicio = ?;

-- anterior
-- parámetros: ['2024-05-13']
SELECT AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.semana_inicio = ?;

-- [C2] Tasa de quiebre %. Porcentaje de combinaciones producto-sucursal con stock cero en la foto del lunes. De qué: toda la cadena. Cuándo: la semana del 12-05-2025. Contra: la semana del 13-05-2024, con todas las sucursales. Abierto por región, de mayor a menor.
-- actual
-- parámetros: ['2025-05-12']
SELECT s.region AS region, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.semana_inicio = ?
GROUP BY s.region
ORDER BY valor DESC;

-- anterior
-- parámetros: ['2024-05-13']
SELECT s.region AS region, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.semana_inicio = ?
GROUP BY s.region
ORDER BY valor DESC;

-- [C3] Tasa de quiebre %. Porcentaje de combinaciones producto-sucursal con stock cero en la foto del lunes. De qué: toda la cadena. Cuándo: la semana del 12-05-2025. Contra: la semana del 13-05-2024, con todas las sucursales. Abierto por proveedor, de mayor a menor.
-- actual
-- parámetros: ['2025-05-12']
SELECT pr.proveedor_id AS proveedor, pr.nombre AS nombre_proveedor, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.semana_inicio = ?
GROUP BY pr.proveedor_id, pr.nombre
ORDER BY valor DESC;

-- anterior
-- parámetros: ['2024-05-13']
SELECT pr.proveedor_id AS proveedor, pr.nombre AS nombre_proveedor, AVG(CASE WHEN st.stock_unidades = 0 THEN 1.0 ELSE 0.0 END) * 100 AS valor
FROM stock_semanal st JOIN fechas f ON st.semana = f.fecha JOIN productos p ON st.sku = p.sku JOIN sucursales s ON st.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.semana_inicio = ?
GROUP BY pr.proveedor_id, pr.nombre
ORDER BY valor DESC;

-- [C8] Ventas netas. Ventas brutas menos descuentos y devoluciones. De qué: toda la cadena. Cuándo: del 12-05-2025 al 18-05-2025. Contra: del 13-05-2024 al 19-05-2024, con todas las sucursales. Abierto por sucursal, de menor a mayor.
-- actual
-- parámetros: ['2025-05-12', '2025-05-18']
SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?
GROUP BY s.sucursal_id, s.nombre
ORDER BY valor DESC;

-- anterior
-- parámetros: ['2024-05-13', '2024-05-19']
SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?
GROUP BY s.sucursal_id, s.nombre
ORDER BY valor DESC;

-- [C12] Ventas netas. Ventas brutas menos descuentos y devoluciones. De qué: toda la cadena. Cuándo: del 12-05-2025 al 18-05-2025. Contra: del 13-05-2024 al 19-05-2024, con todas las sucursales. Abierto por producto y marca y subcategoría y marca propia o no, de menor a mayor, los 15 primeros.
-- actual
-- parámetros: ['2025-05-12', '2025-05-18']
SELECT p.sku AS producto, p.marca AS marca, p.subcategoria AS subcategoria, p.es_marca_propia AS es_marca_propia, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?
GROUP BY p.sku, p.marca, p.subcategoria, p.es_marca_propia
ORDER BY valor DESC;

-- anterior
-- parámetros: ['2024-05-13', '2024-05-19']
SELECT p.sku AS producto, p.marca AS marca, p.subcategoria AS subcategoria, p.es_marca_propia AS es_marca_propia, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?
GROUP BY p.sku, p.marca, p.subcategoria, p.es_marca_propia
ORDER BY valor DESC;

-- [C15] Ventas netas. Ventas brutas menos descuentos y devoluciones. De qué: toda la cadena. Cuándo: del 12-05-2025 al 18-05-2025. Contra: del 13-05-2024 al 19-05-2024, con todas las sucursales.
-- actual
-- parámetros: ['2025-05-12', '2025-05-18']
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?;

-- anterior
-- parámetros: ['2024-05-13', '2024-05-19']
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ?;

-- [C18] Ventas netas. Ventas brutas menos descuentos y devoluciones. De qué: sucursal S32 (Valle Hermoso). Cuándo: del 05-05-2025 al 11-05-2025. Contra: del 06-05-2024 al 12-05-2024, con todas las sucursales.
-- actual
-- parámetros: ['2025-05-05', '2025-05-11', 'S32']
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ? AND s.sucursal_id = ?;

-- anterior
-- parámetros: ['2024-05-06', '2024-05-12', 'S32']
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.fecha BETWEEN ? AND ? AND s.sucursal_id = ?;

-- [C19] Los cinco productos que más cayeron en porcentaje en la semana del 12 al 18-05-2025 contra la del 13 al 19-05-2024, con sus ventas netas de cada semana en millones de pesos. Con SQL directo sobre la base: no es una medida de la capa semántica, se usa para lo que la capa no cubre.
