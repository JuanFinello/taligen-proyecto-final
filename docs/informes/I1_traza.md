# Traza: Preparame un informe ejecutivo del T2 del AF2026 con foco en margen.

Generada el 2026-11-23 con `claude-haiku-5-5`. Para volver a correrla:

```
.venv/bin/python puerta.py "Preparame un informe ejecutivo del T2 del AF2026 con foco en margen."
```

## Preparame un informe ejecutivo del T2 del AF2026 con foco en margen.

### Respuesta

El margen % bajó por el costo de Almacén, pero el margen en pesos subió porque se vendió más
- Almacén es la categoría que más bajó: su margen cayó 1,20 pp [C4]; ninguna otra bajó más de 0,28 pp [C4].
- Dentro de Almacén, Molinos del Plata es el único proveedor que bajó: su margen cayó 8,6 pp, a 17,3 % [C18].
- En Almacén, el costo por unidad subió 1,61 % con el precio casi quieto [C9].

PDF: [I1.pdf](I1.pdf) · SQL: [I1_consultas.sql](I1_consultas.sql) · corrida `20261123-122701-2c8d`

### Consultas (18)

**1. `calcular`** `{"medida": "margen_pct", "filtros": {"anio_fiscal": 2026, "trimestre_fiscal": 2}, "comparar_con": {"anio_fiscal": 2025, "trimestre_fiscal": 2}}`

> Qué se midió: Margen bruto %. Margen bruto sobre ventas netas.  
> De qué: toda la cadena.  
> Cuándo: el T2 del año fiscal 2026 (agosto a octubre de 2025).  
> Contra: el T2 del año fiscal 2025 (agosto a octubre de 2024), con todas las sucursales.  

Resultado: actual = 26.784140179708317 · anterior = 27.026195482998205 · variacion = -0.242055303289888 · unidad_variacion = pp · comparables = False

actual: parámetros `[2026, 2]`
```sql
SELECT (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
```

anterior: parámetros `[2025, 2]`
```sql
SELECT (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
```

**2. `calcular`** `{"medida": "margen_bruto", "filtros": {"anio_fiscal": 2026, "trimestre_fiscal": 2}, "comparar_con": {"anio_fiscal": 2025, "trimestre_fiscal": 2}}`

> Qué se midió: Margen bruto. Ventas netas menos costo.  
> De qué: toda la cadena.  
> Cuándo: el T2 del año fiscal 2026 (agosto a octubre de 2025).  
> Contra: el T2 del año fiscal 2025 (agosto a octubre de 2024), con todas las sucursales.  

Resultado: actual = 663149555.8899846 · anterior = 638303717.6499152 · variacion = 3.89247901164448 · unidad_variacion = % · comparables = False

actual: parámetros `[2026, 2]`
```sql
SELECT SUM(v.importe_neto) - SUM(v.costo) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
```

anterior: parámetros `[2025, 2]`
```sql
SELECT SUM(v.importe_neto) - SUM(v.costo) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
```

**3. `calcular`** `{"medida": "efectos_margen", "filtros": {"anio_fiscal": 2026, "trimestre_fiscal": 2}, "comparar_con": {"anio_fiscal": 2025, "trimestre_fiscal": 2}}`

> Qué se midió: Efecto precio y efecto costo del margen %. Separa la variación del margen % entre dos períodos en efecto precio y efecto costo, en pp (suman la variación).  
> De qué: toda la cadena.  
> Cuándo: el T2 del año fiscal 2026 (agosto a octubre de 2025).  
> Contra: el T2 del año fiscal 2025 (agosto a octubre de 2024), con todas las sucursales.  

Resultado: comparables = False

precio_promedio actual: parámetros `[2026, 2]`
```sql
SELECT SUM(v.importe_neto) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
```

precio_promedio anterior: parámetros `[2025, 2]`
```sql
SELECT SUM(v.importe_neto) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
```

costo_unitario actual: parámetros `[2026, 2]`
```sql
SELECT SUM(v.costo) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
```

costo_unitario anterior: parámetros `[2025, 2]`
```sql
SELECT SUM(v.costo) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
```

**4. `calcular`** `{"medida": "margen_pct", "filtros": {"anio_fiscal": 2026, "trimestre_fiscal": 2}, "comparar_con": {"anio_fiscal": 2025}, "agrupar_por": ["categoria"]}`

> Qué se midió: Margen bruto %. Margen bruto sobre ventas netas.  
> De qué: toda la cadena.  
> Cuándo: el T2 del año fiscal 2026 (agosto a octubre de 2025).  
> Contra: el T2 del año fiscal 2025 (agosto a octubre de 2024), con todas las sucursales.  
> Abierto por categoría, de mayor a menor.  

Resultado: actual = 26.784140179708317 · anterior = 27.026195482998205 · variacion = -0.242055303289888 · unidad_variacion = pp · comparables = False · 6 filas

actual: parámetros `[2026, 2]`
```sql
SELECT p.categoria AS categoria, (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC
```

anterior: parámetros `[2025, 2]`
```sql
SELECT p.categoria AS categoria, (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC
```

**5. `calcular`** `{"medida": "margen_bruto", "filtros": {"anio_fiscal": 2026, "trimestre_fiscal": 2}, "agrupar_por": ["categoria"]}`

> Qué se midió: Margen bruto. Ventas netas menos costo.  
> De qué: toda la cadena.  
> Cuándo: el T2 del año fiscal 2026 (agosto a octubre de 2025).  
> Abierto por categoría, de mayor a menor.  

Resultado: total = 663149555.8899846 · 6 filas

parámetros `[2026, 2]`
```sql
SELECT p.categoria AS categoria, SUM(v.importe_neto) - SUM(v.costo) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC
```

**6. `calcular`** `{"medida": "margen_pct", "filtros": {"anio_fiscal": 2026, "trimestre_fiscal": 2}, "comparar_con": {"anio_fiscal": 2025}}`

> Qué se midió: Margen bruto %. Margen bruto sobre ventas netas.  
> De qué: toda la cadena.  
> Cuándo: el T2 del año fiscal 2026 (agosto a octubre de 2025).  
> Contra: el T2 del año fiscal 2025 (agosto a octubre de 2024), con todas las sucursales.  

Resultado: actual = 26.784140179708317 · anterior = 27.026195482998205 · variacion = -0.242055303289888 · unidad_variacion = pp · comparables = False

actual: parámetros `[2026, 2]`
```sql
SELECT (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
```

anterior: parámetros `[2025, 2]`
```sql
SELECT (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
```

**7. `calcular`** `{"medida": "ventas_netas", "filtros": {"anio_fiscal": 2026, "trimestre_fiscal": 2}, "agrupar_por": ["categoria"]}`

> Qué se midió: Ventas netas. Ventas brutas menos descuentos y devoluciones.  
> De qué: toda la cadena.  
> Cuándo: el T2 del año fiscal 2026 (agosto a octubre de 2025).  
> Abierto por categoría, de mayor a menor.  

Resultado: total = 2475903842.5 · 6 filas

parámetros `[2026, 2]`
```sql
SELECT p.categoria AS categoria, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC
```

**8. `calcular`** `{"medida": "margen_bruto", "filtros": {"anio_fiscal": 2026, "trimestre_fiscal": 2}, "agrupar_por": ["categoria"], "limite": 1}`

> Qué se midió: Margen bruto. Ventas netas menos costo.  
> De qué: toda la cadena.  
> Cuándo: el T2 del año fiscal 2026 (agosto a octubre de 2025).  
> Abierto por categoría, de mayor a menor, los 1 primeros.  

Resultado: total = 663149555.8899846 · 1 filas

parámetros `[2026, 2]`
```sql
SELECT p.categoria AS categoria, SUM(v.importe_neto) - SUM(v.costo) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC
LIMIT 1
```

**9. `calcular`** `{"medida": "efectos_margen", "filtros": {"anio_fiscal": 2026, "trimestre_fiscal": 2}, "comparar_con": {"anio_fiscal": 2025}, "agrupar_por": ["categoria"]}`

> Qué se midió: Efecto precio y efecto costo del margen %. Separa la variación del margen % entre dos períodos en efecto precio y efecto costo, en pp (suman la variación).  
> De qué: toda la cadena.  
> Cuándo: el T2 del año fiscal 2026 (agosto a octubre de 2025).  
> Contra: el T2 del año fiscal 2025 (agosto a octubre de 2024), con todas las sucursales.  
> Abierto por categoría, de mayor a menor.  

Resultado: comparables = False · total = {'margen_pct_anterior': 27.026195482998205, 'margen_pct_actual': 26.784140179708317, 'variacion_pp': -0.242055303289888, 'efecto_precio_pp': -0.08341633100402701, 'efecto_costo_pp': -0.1586389722858633, 'precio_anterior': 3436.309912906333, 'precio_actual': 3432.38635323899, 'costo_unitario_anterior': 2507.606078442622, 'costo_unitario_actual': 2513.051180878281, 'variacion_precio_pct': -0.11417944733700391, 'variacion_costo_unitario_pct': 0.21714345337049412} · 6 filas

precio_promedio actual: parámetros `[2026, 2]`
```sql
SELECT p.categoria AS categoria, SUM(v.importe_neto) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC
```

precio_promedio anterior: parámetros `[2025, 2]`
```sql
SELECT p.categoria AS categoria, SUM(v.importe_neto) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC
```

costo_unitario actual: parámetros `[2026, 2]`
```sql
SELECT p.categoria AS categoria, SUM(v.costo) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC
```

costo_unitario anterior: parámetros `[2025, 2]`
```sql
SELECT p.categoria AS categoria, SUM(v.costo) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC
```

**10. `calcular`** `{"medida": "margen_pct", "filtros": {"anio": 2025, "mes": [8, 9, 10]}, "agrupar_por": ["mes"], "comparar_con": {"anio": 2024}}`

> Qué se midió: Margen bruto %. Margen bruto sobre ventas netas.  
> De qué: toda la cadena.  
> Cuándo: agosto a octubre de 2025.  
> Contra: agosto a octubre de 2024, con todas las sucursales.  
> Abierto por mes, en orden de fechas.  

Resultado: actual = 26.784140179708317 · anterior = 27.026195482998205 · variacion = -0.242055303289888 · unidad_variacion = pp · comparables = False · 3 filas

actual: parámetros `[2025, 8, 9, 10]`
```sql
SELECT f.mes AS mes, (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio = ? AND f.mes IN (?, ?, ?)
GROUP BY f.mes
ORDER BY valor DESC
```

anterior: parámetros `[2024, 8, 9, 10]`
```sql
SELECT f.mes AS mes, (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio = ? AND f.mes IN (?, ?, ?)
GROUP BY f.mes
ORDER BY valor DESC
```

**11. `calcular`** `{"medida": "margen_pct", "filtros": {"anio": 2025, "mes": [8, 9, 10]}, "agrupar_por": ["mes"]}`

> Qué se midió: Margen bruto %. Margen bruto sobre ventas netas.  
> De qué: toda la cadena.  
> Cuándo: agosto a octubre de 2025.  
> Abierto por mes, en orden de fechas.  

Resultado: 3 filas

parámetros `[2025, 8, 9, 10]`
```sql
SELECT f.mes AS mes, (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio = ? AND f.mes IN (?, ?, ?)
GROUP BY f.mes
ORDER BY valor DESC
```

**12. `calcular`** `{"medida": "margen_pct", "filtros": {"anio": 2024, "mes": [8, 9, 10]}, "agrupar_por": ["mes"]}`

> Qué se midió: Margen bruto %. Margen bruto sobre ventas netas.  
> De qué: toda la cadena.  
> Cuándo: agosto a octubre de 2024.  
> Abierto por mes, en orden de fechas.  

Resultado: 3 filas

parámetros `[2024, 8, 9, 10]`
```sql
SELECT f.mes AS mes, (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio = ? AND f.mes IN (?, ?, ?)
GROUP BY f.mes
ORDER BY valor DESC
```

**13. `calcular`** `{"medida": "margen_pct", "filtros": {"anio_fiscal": 2026, "trimestre_fiscal": 2}, "comparar_con": {"anio_fiscal": 2025}, "agrupar_por": ["es_marca_propia"]}`

> Qué se midió: Margen bruto %. Margen bruto sobre ventas netas.  
> De qué: toda la cadena.  
> Cuándo: el T2 del año fiscal 2026 (agosto a octubre de 2025).  
> Contra: el T2 del año fiscal 2025 (agosto a octubre de 2024), con todas las sucursales.  
> Abierto por marca propia o no, de mayor a menor.  

Resultado: actual = 26.784140179709283 · anterior = 27.026195482998205 · variacion = -0.24205530328892166 · unidad_variacion = pp · comparables = False · 2 filas

actual: parámetros `[2026, 2]`
```sql
SELECT p.es_marca_propia AS es_marca_propia, (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.es_marca_propia
ORDER BY valor DESC
```

anterior: parámetros `[2025, 2]`
```sql
SELECT p.es_marca_propia AS es_marca_propia, (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.es_marca_propia
ORDER BY valor DESC
```

**14. `calcular`** `{"medida": "ventas_netas", "filtros": {"anio_fiscal": 2026, "trimestre_fiscal": 2}, "comparar_con": {"anio_fiscal": 2025}, "agrupar_por": ["es_marca_propia"]}`

> Qué se midió: Ventas netas. Ventas brutas menos descuentos y devoluciones.  
> De qué: toda la cadena.  
> Cuándo: el T2 del año fiscal 2026 (agosto a octubre de 2025).  
> Contra: el T2 del año fiscal 2025 (agosto a octubre de 2024), con todas las sucursales.  
> Abierto por marca propia o no, de mayor a menor.  

Resultado: actual = 2475903842.5 · anterior = 2361796421.0 · variacion = 4.8313826071294566 · unidad_variacion = % · comparables = False · 2 filas

actual: parámetros `[2026, 2]`
```sql
SELECT p.es_marca_propia AS es_marca_propia, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.es_marca_propia
ORDER BY valor DESC
```

anterior: parámetros `[2025, 2]`
```sql
SELECT p.es_marca_propia AS es_marca_propia, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.es_marca_propia
ORDER BY valor DESC
```

**15. `calcular`** `{"medida": "ventas_netas", "filtros": {"anio_fiscal": 2026, "trimestre_fiscal": 2}, "comparar_con": {"anio_fiscal": 2025}, "agrupar_por": ["es_marca_propia"], "comparables": true}`

> Qué se midió: Ventas netas. Ventas brutas menos descuentos y devoluciones.  
> De qué: toda la cadena.  
> Cuándo: el T2 del año fiscal 2026 (agosto a octubre de 2025).  
> Contra: el T2 del año fiscal 2025 (agosto a octubre de 2024), solo con las sucursales que estaban abiertas en los dos períodos (comparables).  
> Abierto por marca propia o no, de mayor a menor.  

Resultado: actual = 2414317363.5 · anterior = 2361796421.0 · variacion = 2.223770941178846 · unidad_variacion = % · comparables = True · 2 filas

actual: parámetros `[2026, 2, "2024-08-01"]`
```sql
SELECT p.es_marca_propia AS es_marca_propia, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ? AND s.fecha_apertura <= ?
GROUP BY p.es_marca_propia
ORDER BY valor DESC
```

anterior: parámetros `[2025, 2, "2024-08-01"]`
```sql
SELECT p.es_marca_propia AS es_marca_propia, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ? AND s.fecha_apertura <= ?
GROUP BY p.es_marca_propia
ORDER BY valor DESC
```

**16. `calcular`** `{"medida": "ventas_netas", "filtros": {"anio_fiscal": 2026, "trimestre_fiscal": 2}, "agrupar_por": ["es_marca_propia"]}`

> Qué se midió: Ventas netas. Ventas brutas menos descuentos y devoluciones.  
> De qué: toda la cadena.  
> Cuándo: el T2 del año fiscal 2026 (agosto a octubre de 2025).  
> Abierto por marca propia o no, de mayor a menor.  

Resultado: total = 2475903842.5 · 2 filas

parámetros `[2026, 2]`
```sql
SELECT p.es_marca_propia AS es_marca_propia, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.es_marca_propia
ORDER BY valor DESC
```

**17. `calcular`** `{"medida": "ventas_netas", "filtros": {"anio_fiscal": 2025, "trimestre_fiscal": 2}, "agrupar_por": ["es_marca_propia"]}`

> Qué se midió: Ventas netas. Ventas brutas menos descuentos y devoluciones.  
> De qué: toda la cadena.  
> Cuándo: el T2 del año fiscal 2025 (agosto a octubre de 2024).  
> Abierto por marca propia o no, de mayor a menor.  

Resultado: total = 2361796421.0 · 2 filas

parámetros `[2025, 2]`
```sql
SELECT p.es_marca_propia AS es_marca_propia, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ?
GROUP BY p.es_marca_propia
ORDER BY valor DESC
```

**18. `calcular`** `{"medida": "margen_pct", "filtros": {"anio_fiscal": 2026, "trimestre_fiscal": 2, "categoria": "Almacén"}, "comparar_con": {"anio_fiscal": 2025}, "agrupar_por": ["nombre_proveedor"]}`

> Qué se midió: Margen bruto %. Margen bruto sobre ventas netas.  
> De qué: categoría Almacén.  
> Cuándo: el T2 del año fiscal 2026 (agosto a octubre de 2025).  
> Contra: el T2 del año fiscal 2025 (agosto a octubre de 2024), con todas las sucursales.  
> Abierto por proveedor, de mayor a menor.  

Resultado: actual = 24.462146123057618 · anterior = 25.666425069853595 · variacion = -1.2042789467959771 · unidad_variacion = pp · comparables = False · 5 filas

actual: parámetros `[2026, 2, "Almacén"]`
```sql
SELECT pr.nombre AS nombre_proveedor, (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ? AND p.categoria = ?
GROUP BY pr.nombre
ORDER BY valor DESC
```

anterior: parámetros `[2025, 2, "Almacén"]`
```sql
SELECT pr.nombre AS nombre_proveedor, (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio_fiscal = ? AND f.trimestre_fiscal = ? AND p.categoria = ?
GROUP BY pr.nombre
ORDER BY valor DESC
```
