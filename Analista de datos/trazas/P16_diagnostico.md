# ¿Qué pasó con la gaseosa cola de marca propia en diciembre de 2025?

**La gaseosa cola Del Sur cayó 33 % frente a noviembre [C13] y 48 % frente al mismo mes del año anterior [C12]; la explicación más probable es la promoción de una marca rival en la misma subcategoría, aunque los datos no alcanzan para confirmarlo.**

- El margen casi no se movió: 31,6 % en diciembre frente a 31,8 % en noviembre [C10], así que la caída es de ventas y no de rentabilidad.
- La falta de stock no parece la causa: el quiebre fue de 1,0 % en diciembre [C16], cerca de la tasa normal, aunque el stock promedio bajó a 25 unidades [C18].
- La única promoción de la subcategoría en diciembre fue un 25 % de descuento sobre la cola de Cola Andina, otra marca [C20], pero no tenemos sus ventas para confirmar que le quitó ventas a la Del Sur; en cambio, la lima limón Del Sur subió 41,6 % en el mismo mes [C4], lo que sugiere un cambio de elección dentro de la marca, aunque esto es una interpretación.

**Siguiente paso:** Conviene revisar las ventas de Cola Andina en diciembre frente a noviembre para confirmar si la promoción le ganó a la cola Del Sur, y revisar el stock por sucursal para ver si la baja de stock promedio se concentró en algunas tiendas. También conviene consultar si hubo otras promociones o cambios de precio de la cola en diciembre que la base no esté mostrando, porque la búsqueda por subcategoría no devolvió ninguna.

## Supuestos

- «Diciembre de 2025» se toma en calendario (del 1 al 31 de diciembre de 2025), no en calendario fiscal.
- «Gaseosa cola» se toma como la subcategoría de gaseosa cola dentro de Bebidas, filtrada por es_marca_propia = verdadero (marca Del Sur). Si la subcategoría tiene otro nombre en la base, el analista lo ajusta sin cambiar el criterio.
- Para contextualizar se compara contra noviembre de 2025 (mes anterior) y contra diciembre de 2024 (mismo mes del año anterior), sin comparables, porque se trata de un único producto.
- La base no tiene datos de clientes ni de ventas online, así que el diagnóstico se limita a ventas, unidades, margen, stock y promociones.

## Consultas citadas (SQL en consultas.sql)

- [C4] ventas_netas · {"anio": 2025, "mes": 12, "categoria": "Bebidas", "subcategoria": "Gaseosas", "es_marca_propia": true} · contra {"anio": 2025, "mes": 11} · por producto
- [C10] margen_pct · {"anio": 2025, "mes": 12, "producto": "P0298"} · contra {"anio": 2025, "mes": 11}
- [C12] ventas_netas · {"anio": 2025, "mes": 12, "producto": "P0298"} · contra {"anio": 2024, "mes": 12} (comparables)
- [C13] ventas_netas · {"anio": 2025, "mes": 12, "producto": "P0298"} · contra {"anio": 2025, "mes": 11} (comparables)
- [C16] tasa_quiebre_pct · {"anio": 2025, "mes": 12, "categoria": "Bebidas", "subcategoria": "Gaseosas", "es_marca_propia": true} · por producto
- [C18] stock_promedio · {"anio": 2025, "mes": 12, "categoria": "Bebidas", "subcategoria": "Gaseosas", "es_marca_propia": true} · por producto
