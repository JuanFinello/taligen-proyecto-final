-- [C1] Desvío contra presupuesto %. Cuánto se vendió por encima (+) o por debajo (-) del presupuesto. De qué: toda la cadena. Cuándo: enero de 2026. Abierto por categoría, de mayor a menor.
-- ventas_netas
-- parámetros: [2026, 1]
SELECT p.categoria AS categoria, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio = ? AND f.mes = ?
GROUP BY p.categoria
ORDER BY valor DESC;

-- presupuesto
-- parámetros: [2026, 1]
SELECT pz.categoria AS categoria, SUM(pz.importe_presupuesto) AS valor
FROM presupuesto pz JOIN fechas f ON pz.mes = f.fecha JOIN sucursales s ON pz.sucursal_id = s.sucursal_id
WHERE f.anio = ? AND f.mes = ?
GROUP BY pz.categoria
ORDER BY valor DESC;

-- [C2] Desvío contra presupuesto %. Cuánto se vendió por encima (+) o por debajo (-) del presupuesto. De qué: toda la cadena. Cuándo: enero de 2026.
-- ventas_netas
-- parámetros: [2026, 1]
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio = ? AND f.mes = ?;

-- presupuesto
-- parámetros: [2026, 1]
SELECT SUM(pz.importe_presupuesto) AS valor
FROM presupuesto pz JOIN fechas f ON pz.mes = f.fecha JOIN sucursales s ON pz.sucursal_id = s.sucursal_id
WHERE f.anio = ? AND f.mes = ?;

-- [C3] Desvío contra presupuesto %. Cuánto se vendió por encima (+) o por debajo (-) del presupuesto. De qué: toda la cadena. Cuándo: enero de 2026. Abierto por región, de mayor a menor.
-- ventas_netas
-- parámetros: [2026, 1]
SELECT s.region AS region, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio = ? AND f.mes = ?
GROUP BY s.region
ORDER BY valor DESC;

-- presupuesto
-- parámetros: [2026, 1]
SELECT s.region AS region, SUM(pz.importe_presupuesto) AS valor
FROM presupuesto pz JOIN fechas f ON pz.mes = f.fecha JOIN sucursales s ON pz.sucursal_id = s.sucursal_id
WHERE f.anio = ? AND f.mes = ?
GROUP BY s.region
ORDER BY valor DESC;

