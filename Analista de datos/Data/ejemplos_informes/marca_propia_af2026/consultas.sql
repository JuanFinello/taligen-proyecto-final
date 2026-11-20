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

-- [C3] Cuántos pp más de margen bruto % deja la marca propia que las otras marcas, por categoría, AF2026. Con SQL directo sobre la base: no es una medida de la capa semántica, se usa para lo que la capa no cubre.
-- [C4] Margen bruto en pesos por unidad vendida, marca propia y otras marcas, en las subcategorías donde hay marca propia, AF2026. Promedia productos distintos (tamaños y calidades): es una referencia, no una comparación exacta. Con SQL directo sobre la base: no es una medida de la capa semántica, se usa para lo que la capa no cubre.
-- [C5] En cuántas subcategorías con marca propia la marca propia deja menos pesos de margen por unidad que las otras, AF2026. Con SQL directo sobre la base: no es una medida de la capa semántica, se usa para lo que la capa no cubre.
-- [C6] Las dos gaseosas cola de 2,25 L (Cola Andina y Del Sur, la de marca propia), AF2026 sin diciembre de 2025 (ese mes la Cola Andina estuvo al 25 % de descuento): precio y margen bruto por unidad vendida. Con SQL directo sobre la base: no es una medida de la capa semántica, se usa para lo que la capa no cubre.
