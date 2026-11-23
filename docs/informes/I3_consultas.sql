-- [C1] Ventas netas. Ventas brutas menos descuentos y devoluciones. De qué: región Oeste. Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026). Contra: el año fiscal 2025 (mayo de 2024 a abril de 2025), con todas las sucursales.
-- actual
-- parámetros: ['Oeste', 2026]
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?;

-- anterior
-- parámetros: ['Oeste', 2025]
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?;

-- [C3] Ventas netas. Ventas brutas menos descuentos y devoluciones. De qué: región Oeste. Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026). Contra: el año fiscal 2025 (mayo de 2024 a abril de 2025), solo con las sucursales que estaban abiertas en los dos períodos (comparables).
-- actual
-- parámetros: ['Oeste', 2026, '2024-05-01']
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ? AND s.fecha_apertura <= ?;

-- anterior
-- parámetros: ['Oeste', 2025, '2024-05-01']
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ? AND s.fecha_apertura <= ?;

-- [C6] Desvío contra presupuesto %. Cuánto se vendió por encima (+) o por debajo (-) del presupuesto. De qué: región Oeste. Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026).
-- ventas_netas
-- parámetros: ['Oeste', 2026]
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?;

-- presupuesto
-- parámetros: ['Oeste', 2026]
SELECT SUM(pz.importe_presupuesto) AS valor
FROM presupuesto pz JOIN fechas f ON pz.mes = f.fecha JOIN sucursales s ON pz.sucursal_id = s.sucursal_id
WHERE s.region = ? AND f.anio_fiscal = ?;

-- [C7] Desvío contra presupuesto %. Cuánto se vendió por encima (+) o por debajo (-) del presupuesto. De qué: región Oeste. Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026). Abierto por categoría, de mayor a menor.
-- ventas_netas
-- parámetros: ['Oeste', 2026]
SELECT p.categoria AS categoria, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC;

-- presupuesto
-- parámetros: ['Oeste', 2026]
SELECT pz.categoria AS categoria, SUM(pz.importe_presupuesto) AS valor
FROM presupuesto pz JOIN fechas f ON pz.mes = f.fecha JOIN sucursales s ON pz.sucursal_id = s.sucursal_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY pz.categoria
ORDER BY valor DESC;

-- [C8] Desvío contra presupuesto %. Cuánto se vendió por encima (+) o por debajo (-) del presupuesto. De qué: región Oeste. Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026). Abierto por mes, en orden de fechas.
-- ventas_netas
-- parámetros: ['Oeste', 2026]
SELECT f.mes AS mes, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY f.mes
ORDER BY valor DESC;

-- presupuesto
-- parámetros: ['Oeste', 2026]
SELECT f.mes AS mes, SUM(pz.importe_presupuesto) AS valor
FROM presupuesto pz JOIN fechas f ON pz.mes = f.fecha JOIN sucursales s ON pz.sucursal_id = s.sucursal_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY f.mes
ORDER BY valor DESC;

-- [C9] Días con ventas. Cuántos días vendió cada sucursal, sumados (una sucursal en un día cuenta 1). De qué: región Oeste. Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026). Contra: el año fiscal 2025 (mayo de 2024 a abril de 2025), con todas las sucursales. Abierto por sucursal, de mayor a menor.
-- actual
-- parámetros: ['Oeste', 2026]
SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, COUNT(DISTINCT v.sucursal_id || '|' || CAST(v.fecha AS VARCHAR)) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY s.sucursal_id, s.nombre
ORDER BY valor DESC;

-- anterior
-- parámetros: ['Oeste', 2025]
SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, COUNT(DISTINCT v.sucursal_id || '|' || CAST(v.fecha AS VARCHAR)) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY s.sucursal_id, s.nombre
ORDER BY valor DESC;

-- [C12] Ventas netas. Ventas brutas menos descuentos y devoluciones. De qué: región Oeste. Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026). Contra: el año fiscal 2025 (mayo de 2024 a abril de 2025), solo con las sucursales que estaban abiertas en los dos períodos (comparables). Abierto por mes fiscal, en orden de fechas.
-- actual
-- parámetros: ['Oeste', 2026, '2024-05-01']
SELECT f.mes_fiscal AS mes_fiscal, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ? AND s.fecha_apertura <= ?
GROUP BY f.mes_fiscal
ORDER BY valor DESC;

-- anterior
-- parámetros: ['Oeste', 2025, '2024-05-01']
SELECT f.mes_fiscal AS mes_fiscal, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ? AND s.fecha_apertura <= ?
GROUP BY f.mes_fiscal
ORDER BY valor DESC;

