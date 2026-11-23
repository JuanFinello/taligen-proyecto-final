-- [C1] Margen bruto %. Margen bruto sobre ventas netas. De qué: toda la cadena. Cuándo: el T2 del año fiscal 2026 (agosto a octubre de 2025). Contra: el T2 del año fiscal 2025 (agosto a octubre de 2024), con todas las sucursales.
-- actual
-- parámetros: [2026, 2]
SELECT (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?;

-- anterior
-- parámetros: [2025, 2]
SELECT (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?;

-- [C2] Margen bruto. Ventas netas menos costo. De qué: toda la cadena. Cuándo: el T2 del año fiscal 2026 (agosto a octubre de 2025). Contra: el T2 del año fiscal 2025 (agosto a octubre de 2024), con todas las sucursales.
-- actual
-- parámetros: [2026, 2]
SELECT SUM(v.importe_neto) - SUM(v.costo) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?;

-- anterior
-- parámetros: [2025, 2]
SELECT SUM(v.importe_neto) - SUM(v.costo) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?;

-- [C4] Margen bruto %. Margen bruto sobre ventas netas. De qué: toda la cadena. Cuándo: el T2 del año fiscal 2026 (agosto a octubre de 2025). Contra: el T2 del año fiscal 2025 (agosto a octubre de 2024), con todas las sucursales. Abierto por categoría, de mayor a menor.
-- actual
-- parámetros: [2026, 2]
SELECT p.categoria AS categoria, (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC;

-- anterior
-- parámetros: [2025, 2]
SELECT p.categoria AS categoria, (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC;

-- [C9] Efecto precio y efecto costo del margen %. Separa la variación del margen % entre dos períodos en efecto precio y efecto costo, en pp (suman la variación). De qué: toda la cadena. Cuándo: el T2 del año fiscal 2026 (agosto a octubre de 2025). Contra: el T2 del año fiscal 2025 (agosto a octubre de 2024), con todas las sucursales. Abierto por categoría, de mayor a menor.
-- precio_promedio actual
-- parámetros: [2026, 2]
SELECT p.categoria AS categoria, SUM(v.importe_neto) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC;

-- precio_promedio anterior
-- parámetros: [2025, 2]
SELECT p.categoria AS categoria, SUM(v.importe_neto) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC;

-- costo_unitario actual
-- parámetros: [2026, 2]
SELECT p.categoria AS categoria, SUM(v.costo) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC;

-- costo_unitario anterior
-- parámetros: [2025, 2]
SELECT p.categoria AS categoria, SUM(v.costo) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC;

-- [C18] Margen bruto %. Margen bruto sobre ventas netas. De qué: categoría Almacén. Cuándo: el T2 del año fiscal 2026 (agosto a octubre de 2025). Contra: el T2 del año fiscal 2025 (agosto a octubre de 2024), con todas las sucursales. Abierto por proveedor, de mayor a menor.
-- actual
-- parámetros: [2026, 2, 'Almacén']
SELECT pr.nombre AS nombre_proveedor, (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ? AND p.categoria = ?
GROUP BY pr.nombre
ORDER BY valor DESC;

-- anterior
-- parámetros: [2025, 2, 'Almacén']
SELECT pr.nombre AS nombre_proveedor, (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ? AND p.categoria = ?
GROUP BY pr.nombre
ORDER BY valor DESC;

