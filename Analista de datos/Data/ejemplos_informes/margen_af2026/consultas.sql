-- [C1] Margen bruto %. Margen bruto sobre ventas netas. De qué: toda la cadena. Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026). Contra: el año fiscal 2025 (mayo de 2024 a abril de 2025), con todas las sucursales. Abierto por mes fiscal, en orden de fechas.
-- actual
-- parámetros: [2026]
SELECT f.mes_fiscal AS mes_fiscal, (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ?
GROUP BY f.mes_fiscal
ORDER BY valor DESC;

-- anterior
-- parámetros: [2025]
SELECT f.mes_fiscal AS mes_fiscal, (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ?
GROUP BY f.mes_fiscal
ORDER BY valor DESC;

-- [C2] Margen bruto %. Margen bruto sobre ventas netas. De qué: toda la cadena. Cuándo: de mayo de 2025 a julio de 2025 (año fiscal 2026). Contra: de mayo de 2024 a julio de 2024 (año fiscal 2025), con todas las sucursales.
-- actual
-- parámetros: [2026, 5, 6, 7]
SELECT (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.mes IN (?, ?, ?);

-- anterior
-- parámetros: [2025, 5, 6, 7]
SELECT (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.mes IN (?, ?, ?);

-- [C3] Margen bruto %. Margen bruto sobre ventas netas. De qué: toda la cadena. Cuándo: de agosto de 2025 a noviembre de 2025 (año fiscal 2026). Contra: de agosto de 2024 a noviembre de 2024 (año fiscal 2025), con todas las sucursales.
-- actual
-- parámetros: [2026, 8, 9, 10, 11]
SELECT (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.mes IN (?, ?, ?, ?);

-- anterior
-- parámetros: [2025, 8, 9, 10, 11]
SELECT (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.mes IN (?, ?, ?, ?);

-- [C4] Margen bruto %. Margen bruto sobre ventas netas. De qué: toda la cadena. Cuándo: de diciembre de 2025 a abril de 2026 (año fiscal 2026). Contra: de diciembre de 2024 a abril de 2025 (año fiscal 2025), con todas las sucursales.
-- actual
-- parámetros: [2026, 12, 1, 2, 3, 4]
SELECT (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.mes IN (?, ?, ?, ?, ?);

-- anterior
-- parámetros: [2025, 12, 1, 2, 3, 4]
SELECT (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.mes IN (?, ?, ?, ?, ?);

-- [C6] Cuánto movió cada categoría (Almacén, Bebidas y el resto) el margen bruto % total, por mes, AF2026 contra AF2025: su cambio de margen, pesado por cuánto vende. Las categorías suman el cambio total. Con SQL directo sobre la base: no es una medida de la capa semántica, se usa para lo que la capa no cubre.
-- [C7] Cuánto movió cada categoría (Almacén, Bebidas y el resto) el margen bruto % total, de mayo a julio, de agosto a noviembre y de diciembre a abril, AF2026 contra AF2025: su cambio de margen, pesado por cuánto vende. Las categorías suman el cambio total. Con SQL directo sobre la base: no es una medida de la capa semántica, se usa para lo que la capa no cubre.
-- [C8] Descuento sobre la venta bruta de Bebidas, por mitad del año fiscal. Con SQL directo sobre la base: no es una medida de la capa semántica, se usa para lo que la capa no cubre.
-- [C9] Promociones de Bebidas de diciembre de 2025 a abril de 2026, de mayor a menor descuento. Con SQL directo sobre la base: no es una medida de la capa semántica, se usa para lo que la capa no cubre.
-- [C11] Cuánto movió cada una de las seis categorías el margen bruto % total en el año, AF2026 contra AF2025: su cambio de margen, pesado por cuánto vende. Las categorías suman el cambio total. Con SQL directo sobre la base: no es una medida de la capa semántica, se usa para lo que la capa no cubre.
-- [C13] La Cola Andina 2,25 L en diciembre de 2025, con la promoción «Verano Cola Andina» (25 %): precio y costo por unidad. Con SQL directo sobre la base: no es una medida de la capa semántica, se usa para lo que la capa no cubre.
-- [C15] Costo y precio de lista por unidad de cada proveedor de Almacén en el AF2026: de mayo a julio contra de agosto a abril. Con SQL directo sobre la base: no es una medida de la capa semántica, se usa para lo que la capa no cubre.
