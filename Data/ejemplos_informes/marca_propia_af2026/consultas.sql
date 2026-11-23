-- [C1] Ventas netas. Ventas brutas menos descuentos y devoluciones. De qué: toda la cadena. Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026). Abierto por marca propia o no, de mayor a menor.

-- parámetros: [2026]
SELECT p.es_marca_propia AS es_marca_propia, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ?
GROUP BY p.es_marca_propia
ORDER BY valor DESC;

-- [C2] Margen bruto %. Margen bruto sobre ventas netas. De qué: toda la cadena. Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026). Abierto por categoría y marca propia o no, de mayor a menor.

-- parámetros: [2026]
SELECT p.categoria AS categoria, p.es_marca_propia AS es_marca_propia, (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ?
GROUP BY p.categoria, p.es_marca_propia
ORDER BY valor DESC;

-- [C3] Margen por unidad. Margen bruto en pesos por unidad vendida. De qué: toda la cadena. Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026). Abierto por subcategoría y marca propia o no, de mayor a menor.

-- parámetros: [2026]
SELECT p.subcategoria AS subcategoria, p.es_marca_propia AS es_marca_propia, (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ?
GROUP BY p.subcategoria, p.es_marca_propia
ORDER BY valor DESC;

-- [C4] Precio promedio. Ventas netas por unidad. De qué: toda la cadena. Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026). Abierto por subcategoría y marca propia o no, de mayor a menor.

-- parámetros: [2026]
SELECT p.subcategoria AS subcategoria, p.es_marca_propia AS es_marca_propia, SUM(v.importe_neto) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ?
GROUP BY p.subcategoria, p.es_marca_propia
ORDER BY valor DESC;

-- [C5] Margen por unidad. Margen bruto en pesos por unidad vendida. De qué: producto P0071 o P0298. Cuándo: el año fiscal 2026 sin diciembre de 2025. Abierto por producto, de mayor a menor.

-- parámetros: [2026, 'P0071', 'P0298', 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12]
SELECT p.sku AS producto, (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND p.sku IN (?, ?) AND f.mes_fiscal IN (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
GROUP BY p.sku
ORDER BY valor DESC;

