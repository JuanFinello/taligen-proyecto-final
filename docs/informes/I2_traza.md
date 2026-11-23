# Traza: Necesito un informe de cumplimiento de presupuesto de enero de 2026, por categoría y por región.

Generada el 2026-11-23 con `claude-haiku-5-5`. Para volver a correrla:

```
.venv/bin/python puerta.py "Necesito un informe de cumplimiento de presupuesto de enero de 2026, por categoría y por región."
```

## Necesito un informe de cumplimiento de presupuesto de enero de 2026, por categoría y por región.

### Respuesta

Enero cerró bajo presupuesto en todas las categorías y regiones, pero un error de carga en Perfumería exagera la caída
- Lácteos, Almacén, Limpieza, Bebidas y Frescos quedaron entre −3,2 % y −5,9 % bajo presupuesto [C1].
- Perfumería cae −68,0 % contra presupuesto: en diez sucursales su presupuesto de enero es 9 a 11 veces el de los meses vecinos, lo que parece un error de carga [C1].
- Sur es la única región con esa carga sospechosa marcada, y explica casi todo su −53,7 % contra presupuesto [C3].

PDF: [I2.pdf](I2.pdf) · SQL: [I2_consultas.sql](I2_consultas.sql) · corrida `20261123-122701-2c8d`

### Consultas (4)

**1. `calcular`** `{"medida": "desvio_presupuesto_pct", "filtros": {"anio": 2026, "mes": 1}, "agrupar_por": ["categoria"], "orden": "desc"}`

> Qué se midió: Desvío contra presupuesto %. Cuánto se vendió por encima (+) o por debajo (-) del presupuesto.  
> De qué: toda la cadena.  
> Cuándo: enero de 2026.  
> Abierto por categoría, de mayor a menor.  

Resultado: total = {'valor': -23.723655535921342, 'ventas_netas': 938353763.0, 'presupuesto': 1230202849.3800006} · 6 filas

ventas_netas: parámetros `[2026, 1]`
```sql
SELECT p.categoria AS categoria, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio = ? AND f.mes = ?
GROUP BY p.categoria
ORDER BY valor DESC
```

presupuesto: parámetros `[2026, 1]`
```sql
SELECT pz.categoria AS categoria, SUM(pz.importe_presupuesto) AS valor
FROM presupuesto pz JOIN fechas f ON pz.mes = f.fecha JOIN sucursales s ON pz.sucursal_id = s.sucursal_id
WHERE f.anio = ? AND f.mes = ?
GROUP BY pz.categoria
ORDER BY valor DESC
```

**2. `calcular`** `{"medida": "desvio_presupuesto_pct", "filtros": {"anio": 2026, "mes": 1}}`

> Qué se midió: Desvío contra presupuesto %. Cuánto se vendió por encima (+) o por debajo (-) del presupuesto.  
> De qué: toda la cadena.  
> Cuándo: enero de 2026.  

Resultado: valor = -23.723655535921342

ventas_netas: parámetros `[2026, 1]`
```sql
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio = ? AND f.mes = ?
```

presupuesto: parámetros `[2026, 1]`
```sql
SELECT SUM(pz.importe_presupuesto) AS valor
FROM presupuesto pz JOIN fechas f ON pz.mes = f.fecha JOIN sucursales s ON pz.sucursal_id = s.sucursal_id
WHERE f.anio = ? AND f.mes = ?
```

**3. `calcular`** `{"medida": "desvio_presupuesto_pct", "filtros": {"anio": 2026, "mes": 1}, "agrupar_por": ["region"], "orden": "desc"}`

> Qué se midió: Desvío contra presupuesto %. Cuánto se vendió por encima (+) o por debajo (-) del presupuesto.  
> De qué: toda la cadena.  
> Cuándo: enero de 2026.  
> Abierto por región, de mayor a menor.  

Resultado: total = {'valor': -23.723655535921342, 'ventas_netas': 938353763.0, 'presupuesto': 1230202849.3800006} · 4 filas

ventas_netas: parámetros `[2026, 1]`
```sql
SELECT s.region AS region, SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio = ? AND f.mes = ?
GROUP BY s.region
ORDER BY valor DESC
```

presupuesto: parámetros `[2026, 1]`
```sql
SELECT s.region AS region, SUM(pz.importe_presupuesto) AS valor
FROM presupuesto pz JOIN fechas f ON pz.mes = f.fecha JOIN sucursales s ON pz.sucursal_id = s.sucursal_id
WHERE f.anio = ? AND f.mes = ?
GROUP BY s.region
ORDER BY valor DESC
```

**4. `calcular`** `{"medida": "desvio_presupuesto_pct", "filtros": {"anio": 2026, "mes": 1}}`

> Qué se midió: Desvío contra presupuesto %. Cuánto se vendió por encima (+) o por debajo (-) del presupuesto.  
> De qué: toda la cadena.  
> Cuándo: enero de 2026.  

Resultado: valor = -23.723655535921342

ventas_netas: parámetros `[2026, 1]`
```sql
SELECT SUM(v.importe_neto) AS valor
FROM ventas v JOIN fechas f ON v.fecha = f.fecha JOIN productos p ON v.sku = p.sku JOIN sucursales s ON v.sucursal_id = s.sucursal_id JOIN proveedores pr ON p.proveedor_id = pr.proveedor_id
WHERE f.anio = ? AND f.mes = ?
```

presupuesto: parámetros `[2026, 1]`
```sql
SELECT SUM(pz.importe_presupuesto) AS valor
FROM presupuesto pz JOIN fechas f ON pz.mes = f.fecha JOIN sucursales s ON pz.sucursal_id = s.sucursal_id
WHERE f.anio = ? AND f.mes = ?
```
