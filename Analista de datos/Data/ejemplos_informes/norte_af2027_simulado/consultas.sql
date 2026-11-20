-- [C1] Ventas netas. Ventas brutas menos descuentos y devoluciones. De qué: región Norte. Cuándo: el año fiscal 2027 (mayo de 2026 a abril de 2027). Contra: el año fiscal 2026 (mayo de 2025 a abril de 2026), con todas las sucursales.
-- actual
-- parámetros: ['Norte', 2027]
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?;

-- anterior
-- parámetros: ['Norte', 2026]
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?;

-- [C2] Ventas netas. Ventas brutas menos descuentos y devoluciones. De qué: región Norte. Cuándo: el año fiscal 2027 (mayo de 2026 a abril de 2027). Contra: el año fiscal 2026 (mayo de 2025 a abril de 2026), con todas las sucursales. Abierto por sucursal, de mayor a menor.
-- actual
-- parámetros: ['Norte', 2027]
SELECT s.nombre AS nombre_sucursal, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY s.nombre
ORDER BY valor DESC;

-- anterior
-- parámetros: ['Norte', 2026]
SELECT s.nombre AS nombre_sucursal, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY s.nombre
ORDER BY valor DESC;

-- [C3] Último día con ventas de cada sucursal del Norte en el AF2027 (del 01-05-2026 al 30-04-2027). Con SQL directo sobre la base: no es una medida de la capa semántica, se usa para lo que la capa no cubre.
-- [C4] Ventas netas. Ventas brutas menos descuentos y devoluciones. De qué: región Norte. Cuándo: el año fiscal 2027 (mayo de 2026 a abril de 2027). Contra: el año fiscal 2026 (mayo de 2025 a abril de 2026), con todas las sucursales. Abierto por mes fiscal, en orden de fechas.
-- actual
-- parámetros: ['Norte', 2027]
SELECT f.mes_fiscal AS mes_fiscal, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY f.mes_fiscal
ORDER BY valor DESC;

-- anterior
-- parámetros: ['Norte', 2026]
SELECT f.mes_fiscal AS mes_fiscal, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY f.mes_fiscal
ORDER BY valor DESC;

-- [C5] Días del AF2027 en que ninguna sucursal del Norte registró ventas. Con SQL directo sobre la base: no es una medida de la capa semántica, se usa para lo que la capa no cubre.
-- [C6] Ventas netas. Ventas brutas menos descuentos y devoluciones. De qué: sucursal Villa Arenal, Los Ceibos, Puerto Norte, Alto Verde, San Isidro Labrador, La Calera, Las Acacias, Río Claro o Bajo Hondo. Cuándo: el año fiscal 2027 (mayo de 2026 a abril de 2027). Contra: el año fiscal 2026 (mayo de 2025 a abril de 2026), con todas las sucursales.
-- actual
-- parámetros: [2027, 'S01', 'S02', 'S03', 'S04', 'S05', 'S06', 'S08', 'S09', 'S10']
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND s.sucursal_id IN (?, ?, ?, ?, ?, ?, ?, ?, ?);

-- anterior
-- parámetros: [2026, 'S01', 'S02', 'S03', 'S04', 'S05', 'S06', 'S08', 'S09', 'S10']
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND s.sucursal_id IN (?, ?, ?, ?, ?, ?, ?, ?, ?);

-- [C7] Unidades. Unidades vendidas, netas de devoluciones. De qué: sucursal Villa Arenal, Los Ceibos, Puerto Norte, Alto Verde, San Isidro Labrador, La Calera, Las Acacias, Río Claro o Bajo Hondo. Cuándo: de enero de 2027 a abril de 2027 (año fiscal 2027). Contra: de enero de 2026 a abril de 2026 (año fiscal 2026), con todas las sucursales.
-- actual
-- parámetros: [2027, 'S01', 'S02', 'S03', 'S04', 'S05', 'S06', 'S08', 'S09', 'S10', 1, 2, 3, 4]
SELECT SUM(v.unidades) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND s.sucursal_id IN (?, ?, ?, ?, ?, ?, ?, ?, ?) AND f.mes IN (?, ?, ?, ?);

-- anterior
-- parámetros: [2026, 'S01', 'S02', 'S03', 'S04', 'S05', 'S06', 'S08', 'S09', 'S10', 1, 2, 3, 4]
SELECT SUM(v.unidades) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND s.sucursal_id IN (?, ?, ?, ?, ?, ?, ?, ?, ?) AND f.mes IN (?, ?, ?, ?);

-- [C8] Ventas netas. Ventas brutas menos descuentos y devoluciones. De qué: sucursal Villa Arenal, Los Ceibos, Puerto Norte, Alto Verde, San Isidro Labrador, La Calera, Las Acacias, Río Claro o Bajo Hondo. Cuándo: de enero de 2027 a abril de 2027 (año fiscal 2027). Contra: de enero de 2026 a abril de 2026 (año fiscal 2026), con todas las sucursales.
-- actual
-- parámetros: [2027, 'S01', 'S02', 'S03', 'S04', 'S05', 'S06', 'S08', 'S09', 'S10', 1, 2, 3, 4]
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND s.sucursal_id IN (?, ?, ?, ?, ?, ?, ?, ?, ?) AND f.mes IN (?, ?, ?, ?);

-- anterior
-- parámetros: [2026, 'S01', 'S02', 'S03', 'S04', 'S05', 'S06', 'S08', 'S09', 'S10', 1, 2, 3, 4]
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND s.sucursal_id IN (?, ?, ?, ?, ?, ?, ?, ?, ?) AND f.mes IN (?, ?, ?, ?);

