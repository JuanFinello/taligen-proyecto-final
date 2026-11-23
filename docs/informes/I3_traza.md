# Traza: Armame un informe del AF2026 para el gerente de la región Oeste.

Generada el 2026-11-23 con `claude-haiku-5-5`. Para volver a correrla:

```
.venv/bin/python analista/puerta.py "Armame un informe del AF2026 para el gerente de la región Oeste."
```

## Armame un informe del AF2026 para el gerente de la región Oeste.

### Respuesta

Oeste vendió 6,3 % más por sus sucursales nuevas, pero las que ya estaban cayeron 5,7 %
- Las ocho sucursales de siempre vendieron los 365 días en ambos años, así que la caída no viene de días sin ventas [C9].
- Desde junio, las ocho sucursales de siempre vendieron menos que un año antes en todos los meses, con caídas de entre 3,7 % (enero) y 8,9 % (marzo) [C12].
- Aparte de lo anterior, la región quedó 9,4 % por debajo del presupuesto, con ventas menores a lo presupuestado en las seis categorías y en los doce meses [C6] [C7] [C8].

PDF: [I3.pdf](I3.pdf) · SQL: [I3_consultas.sql](I3_consultas.sql) · corrida `20261123-122701-2c8d`

### Consultas (12)

**1. `calcular`** `{"medida": "ventas_netas", "filtros": {"region": "Oeste", "anio_fiscal": 2026}, "comparar_con": {"anio_fiscal": 2025}}`

> Qué se midió: Ventas netas. Ventas brutas menos descuentos y devoluciones.  
> De qué: región Oeste.  
> Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026).  
> Contra: el año fiscal 2025 (mayo de 2024 a abril de 2025), con todas las sucursales.  

Resultado: actual = 1940176821.5 · anterior = 1825638106.5 · variacion = 6.273900319685291 · unidad_variacion = % · comparables = False

actual: parámetros `["Oeste", 2026]`
```sql
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
```

anterior: parámetros `["Oeste", 2025]`
```sql
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
```

**2. `calcular`** `{"medida": "ventas_netas", "filtros": {"region": "Oeste", "anio_fiscal": 2026}, "comparar_con": {"anio_fiscal": 2025}, "agrupar_por": ["trimestre_fiscal"]}`

> Qué se midió: Ventas netas. Ventas brutas menos descuentos y devoluciones.  
> De qué: región Oeste.  
> Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026).  
> Contra: el año fiscal 2025 (mayo de 2024 a abril de 2025), con todas las sucursales.  
> Abierto por trimestre fiscal, en orden de fechas.  

Resultado: actual = 1940176821.5 · anterior = 1825638106.5 · variacion = 6.273900319685291 · unidad_variacion = % · comparables = False · 4 filas

actual: parámetros `["Oeste", 2026]`
```sql
SELECT f.trimestre_fiscal AS trimestre_fiscal, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY f.trimestre_fiscal
ORDER BY valor DESC
```

anterior: parámetros `["Oeste", 2025]`
```sql
SELECT f.trimestre_fiscal AS trimestre_fiscal, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY f.trimestre_fiscal
ORDER BY valor DESC
```

**3. `calcular`** `{"medida": "ventas_netas", "filtros": {"region": "Oeste", "anio_fiscal": 2026}, "comparar_con": {"anio_fiscal": 2025}, "comparables": true}`

> Qué se midió: Ventas netas. Ventas brutas menos descuentos y devoluciones.  
> De qué: región Oeste.  
> Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026).  
> Contra: el año fiscal 2025 (mayo de 2024 a abril de 2025), solo con las sucursales que estaban abiertas en los dos períodos (comparables).  

Resultado: actual = 1722050606.5 · anterior = 1825638106.5 · variacion = -5.674043482724598 · unidad_variacion = % · comparables = True

actual: parámetros `["Oeste", 2026, "2024-05-01"]`
```sql
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ? AND s.fecha_apertura <= ?
```

anterior: parámetros `["Oeste", 2025, "2024-05-01"]`
```sql
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ? AND s.fecha_apertura <= ?
```

**4. `calcular`** `{"medida": "margen_pct", "filtros": {"region": "Oeste", "anio_fiscal": 2026}, "comparar_con": {"anio_fiscal": 2025}}`

> Qué se midió: Margen bruto %. Margen bruto sobre ventas netas.  
> De qué: región Oeste.  
> Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026).  
> Contra: el año fiscal 2025 (mayo de 2024 a abril de 2025), con todas las sucursales.  

Resultado: actual = 26.577611073166484 · anterior = 26.841985844033168 · variacion = -0.26437477086668437 · unidad_variacion = pp · comparables = False

actual: parámetros `["Oeste", 2026]`
```sql
SELECT (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
```

anterior: parámetros `["Oeste", 2025]`
```sql
SELECT (SUM(v.importe_neto) - SUM(v.costo)) / NULLIF(SUM(v.importe_neto), 0) * 100 AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
```

**5. `calcular`** `{"medida": "efectos_margen", "filtros": {"region": "Oeste", "anio_fiscal": 2026}, "comparar_con": {"anio_fiscal": 2025}, "agrupar_por": ["categoria"]}`

> Qué se midió: Efecto precio y efecto costo del margen %. Separa la variación del margen % entre dos períodos en efecto precio y efecto costo, en pp (suman la variación).  
> De qué: región Oeste.  
> Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026).  
> Contra: el año fiscal 2025 (mayo de 2024 a abril de 2025), con todas las sucursales.  
> Abierto por categoría, de mayor a menor.  

Resultado: comparables = False · total = {'margen_pct_anterior': 26.84198584403382, 'margen_pct_actual': 26.57761107316643, 'variacion_pp': -0.26437477086739136, 'efecto_precio_pp': -0.814104563165674, 'efecto_costo_pp': 0.5497297922982808, 'precio_anterior': 3430.412532507065, 'precio_actual': 3392.65892284153, 'costo_unitario_anterior': 2509.6216861395565, 'costo_unitario_actual': 2490.9712292896306, 'variacion_precio_pct': -1.1005559625198558, 'variacion_costo_unitario_pct': -0.7431581003993881} · 6 filas

precio_promedio actual: parámetros `["Oeste", 2026]`
```sql
SELECT p.categoria AS categoria, SUM(v.importe_neto) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC
```

precio_promedio anterior: parámetros `["Oeste", 2025]`
```sql
SELECT p.categoria AS categoria, SUM(v.importe_neto) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC
```

costo_unitario actual: parámetros `["Oeste", 2026]`
```sql
SELECT p.categoria AS categoria, SUM(v.costo) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC
```

costo_unitario anterior: parámetros `["Oeste", 2025]`
```sql
SELECT p.categoria AS categoria, SUM(v.costo) / NULLIF(SUM(v.unidades), 0) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC
```

**6. `calcular`** `{"medida": "desvio_presupuesto_pct", "filtros": {"region": "Oeste", "anio_fiscal": 2026}}`

> Qué se midió: Desvío contra presupuesto %. Cuánto se vendió por encima (+) o por debajo (-) del presupuesto.  
> De qué: región Oeste.  
> Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026).  

Resultado: valor = -9.351085543581277

ventas_netas: parámetros `["Oeste", 2026]`
```sql
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
```

presupuesto: parámetros `["Oeste", 2026]`
```sql
SELECT SUM(pz.importe_presupuesto) AS valor
FROM presupuesto pz JOIN fechas f ON pz.mes = f.fecha JOIN sucursales s ON pz.sucursal_id = s.sucursal_id
WHERE s.region = ? AND f.anio_fiscal = ?
```

**7. `calcular`** `{"medida": "desvio_presupuesto_pct", "filtros": {"region": "Oeste", "anio_fiscal": 2026}, "agrupar_por": ["categoria"]}`

> Qué se midió: Desvío contra presupuesto %. Cuánto se vendió por encima (+) o por debajo (-) del presupuesto.  
> De qué: región Oeste.  
> Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026).  
> Abierto por categoría, de mayor a menor.  

Resultado: total = {'valor': -9.351085543581277, 'ventas_netas': 1940176821.5, 'presupuesto': 2140319973.0900018} · 6 filas

ventas_netas: parámetros `["Oeste", 2026]`
```sql
SELECT p.categoria AS categoria, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY p.categoria
ORDER BY valor DESC
```

presupuesto: parámetros `["Oeste", 2026]`
```sql
SELECT pz.categoria AS categoria, SUM(pz.importe_presupuesto) AS valor
FROM presupuesto pz JOIN fechas f ON pz.mes = f.fecha JOIN sucursales s ON pz.sucursal_id = s.sucursal_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY pz.categoria
ORDER BY valor DESC
```

**8. `calcular`** `{"medida": "desvio_presupuesto_pct", "filtros": {"region": "Oeste", "anio_fiscal": 2026}, "agrupar_por": ["mes"]}`

> Qué se midió: Desvío contra presupuesto %. Cuánto se vendió por encima (+) o por debajo (-) del presupuesto.  
> De qué: región Oeste.  
> Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026).  
> Abierto por mes, en orden de fechas.  

Resultado: total = {'valor': -9.351085543581277, 'ventas_netas': 1940176821.5, 'presupuesto': 2140319973.0900018} · 12 filas

ventas_netas: parámetros `["Oeste", 2026]`
```sql
SELECT f.mes AS mes, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY f.mes
ORDER BY valor DESC
```

presupuesto: parámetros `["Oeste", 2026]`
```sql
SELECT f.mes AS mes, SUM(pz.importe_presupuesto) AS valor
FROM presupuesto pz JOIN fechas f ON pz.mes = f.fecha JOIN sucursales s ON pz.sucursal_id = s.sucursal_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY f.mes
ORDER BY valor DESC
```

**9. `calcular`** `{"medida": "dias_con_ventas", "filtros": {"region": "Oeste", "anio_fiscal": 2026}, "agrupar_por": ["sucursal", "nombre_sucursal"], "comparar_con": {"anio_fiscal": 2025}}`

> Qué se midió: Días con ventas. Cuántos días vendió cada sucursal, sumados (una sucursal en un día cuenta 1).  
> De qué: región Oeste.  
> Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026).  
> Contra: el año fiscal 2025 (mayo de 2024 a abril de 2025), con todas las sucursales.  
> Abierto por sucursal, de mayor a menor.  

Resultado: actual = 3557 · anterior = 2920 · variacion = 21.815068493150687 · unidad_variacion = % · comparables = False · 10 filas

actual: parámetros `["Oeste", 2026]`
```sql
SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, COUNT(DISTINCT v.sucursal_id || '|' || CAST(v.fecha AS VARCHAR)) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY s.sucursal_id, s.nombre
ORDER BY valor DESC
```

anterior: parámetros `["Oeste", 2025]`
```sql
SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, COUNT(DISTINCT v.sucursal_id || '|' || CAST(v.fecha AS VARCHAR)) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY s.sucursal_id, s.nombre
ORDER BY valor DESC
```

**10. `calcular`** `{"medida": "cantidad_sucursales", "filtros": {"region": "Oeste", "anio_fiscal": 2026}, "comparar_con": {"anio_fiscal": 2025}}`

> Qué se midió: Cantidad de sucursales con venta. Sucursales con al menos un movimiento en el período.  
> De qué: región Oeste.  
> Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026).  
> Contra: el año fiscal 2025 (mayo de 2024 a abril de 2025), con todas las sucursales.  

Resultado: actual = 10 · anterior = 8 · variacion = 25.0 · unidad_variacion = % · comparables = False

actual: parámetros `["Oeste", 2026]`
```sql
SELECT COUNT(DISTINCT v.sucursal_id) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
```

anterior: parámetros `["Oeste", 2025]`
```sql
SELECT COUNT(DISTINCT v.sucursal_id) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
```

**11. `calcular`** `{"medida": "dias_con_ventas", "filtros": {"region": "Oeste", "anio_fiscal": 2026}, "comparar_con": {"anio_fiscal": 2025}, "agrupar_por": ["sucursal", "nombre_sucursal"]}`

> Qué se midió: Días con ventas. Cuántos días vendió cada sucursal, sumados (una sucursal en un día cuenta 1).  
> De qué: región Oeste.  
> Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026).  
> Contra: el año fiscal 2025 (mayo de 2024 a abril de 2025), con todas las sucursales.  
> Abierto por sucursal, de mayor a menor.  

Resultado: actual = 3557 · anterior = 2920 · variacion = 21.815068493150687 · unidad_variacion = % · comparables = False · 10 filas

actual: parámetros `["Oeste", 2026]`
```sql
SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, COUNT(DISTINCT v.sucursal_id || '|' || CAST(v.fecha AS VARCHAR)) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY s.sucursal_id, s.nombre
ORDER BY valor DESC
```

anterior: parámetros `["Oeste", 2025]`
```sql
SELECT s.sucursal_id AS sucursal, s.nombre AS nombre_sucursal, COUNT(DISTINCT v.sucursal_id || '|' || CAST(v.fecha AS VARCHAR)) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ?
GROUP BY s.sucursal_id, s.nombre
ORDER BY valor DESC
```

**12. `calcular`** `{"medida": "ventas_netas", "filtros": {"region": "Oeste", "anio_fiscal": 2026}, "comparar_con": {"anio_fiscal": 2025}, "agrupar_por": ["mes_fiscal"], "comparables": true}`

> Qué se midió: Ventas netas. Ventas brutas menos descuentos y devoluciones.  
> De qué: región Oeste.  
> Cuándo: el año fiscal 2026 (mayo de 2025 a abril de 2026).  
> Contra: el año fiscal 2025 (mayo de 2024 a abril de 2025), solo con las sucursales que estaban abiertas en los dos períodos (comparables).  
> Abierto por mes fiscal, en orden de fechas.  

Resultado: actual = 1722050606.5 · anterior = 1825638106.5 · variacion = -5.674043482724598 · unidad_variacion = % · comparables = True · 12 filas

actual: parámetros `["Oeste", 2026, "2024-05-01"]`
```sql
SELECT f.mes_fiscal AS mes_fiscal, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ? AND s.fecha_apertura <= ?
GROUP BY f.mes_fiscal
ORDER BY valor DESC
```

anterior: parámetros `["Oeste", 2025, "2024-05-01"]`
```sql
SELECT f.mes_fiscal AS mes_fiscal, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE s.region = ? AND f.anio_fiscal = ? AND s.fecha_apertura <= ?
GROUP BY f.mes_fiscal
ORDER BY valor DESC
```
