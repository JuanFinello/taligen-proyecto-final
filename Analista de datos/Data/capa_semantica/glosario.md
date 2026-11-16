# Almacenes del Sur: definiciones de negocio

Cómo se calcula cada indicador. Las fórmulas están en `medidas.yaml`; acá está el criterio que las fórmulas no dicen.

## Alcance de los datos

La base tiene los movimientos diarios de venta por sucursal y producto, la foto semanal de stock, el presupuesto mensual y las promociones. **No tiene datos de clientes, ni de tickets o transacciones individuales, ni de ventas online.** Indicadores como el ticket promedio, los clientes nuevos o la frecuencia de visita no se pueden calcular con esta base.

Los importes están en pesos constantes y sin impuestos: las comparaciones entre períodos no necesitan ajuste por inflación.

«Almacén», en singular, es una categoría de productos, no la empresa: a la empresa se la llama «la cadena» o «Almacenes del Sur».

## Calendario

El año fiscal empieza el 1 de mayo y se nombra por el año en que termina: el AF2026 va de mayo de 2025 a abril de 2026. Los trimestres fiscales son T1 (mayo a julio), T2 (agosto a octubre), T3 (noviembre a enero) y T4 (febrero a abril).

Finanzas habla en trimestres y años fiscales; las áreas comerciales, en calendario («el primer trimestre» es enero a marzo). Cuando un pedido dice «el último trimestre» o «el año pasado» sin aclarar cuál, la respuesta cambia: hay que preguntar o, como mínimo, declarar qué calendario se usó.

Qué período cubre la base lo dice ver_modelo (cobertura). «El último mes», «el último trimestre» o «este año» se cuentan desde el último dato de la base, no desde la fecha de hoy.

## Ventas

- **«Ventas», sin más, son ventas netas**: brutas menos descuentos y devoluciones.
- Las devoluciones son movimientos con `tipo_movimiento = 'devolucion'` e importes negativos. Sumar el importe bruto de todos los movimientos no da las ventas brutas.

## Margen

**«Margen bruto» es en pesos. «El margen», sin más, es el margen %**, y junto al % se muestran también los pesos.

El margen % se expresa en por ciento y **sus variaciones se informan en puntos porcentuales**: de 25 % a 24 % es una caída de 1 pp. Para explicar una variación conviene separar el efecto precio (precio promedio) del efecto costo (costo por unidad). El costo es el de reposición vigente el día de la venta: si un proveedor cambia su costo, se ve desde ese día.

## Presupuesto

Es mensual, por sucursal y categoría, así que solo se compara contra meses completos. Una sucursal nueva tiene presupuesto desde su mes de apertura. Un desvío enorme concentrado en una categoría y un mes, que no aparece en los meses vecinos, suele ser un error de carga: antes de concluir, conviene compararlo con los meses vecinos.

## Variación interanual y comparables

- La variación interanual compara contra el mismo período del año anterior. Sin aclarar, se informa la total.
- **Like-for-like (comparables, mismas sucursales)**: solo las sucursales abiertas durante todo el período y todo el mismo período del año anterior, es decir, con apertura anterior al inicio del período anterior. Una región que abrió sucursales puede crecer en total y caer en comparables.

## Stock y quiebre

La foto de stock se toma los lunes. Un producto está en quiebre cuando la foto muestra stock cero. La tasa normal ronda el 1 %. Ante una caída de ventas concentrada en una región y un proveedor, conviene mirar el stock antes que la demanda.

## Promociones y marca propia

Una promoción es un descuento sobre un producto en todas las sucursales entre dos fechas. Puede quitarle ventas a productos parecidos de la misma subcategoría (canibalización), así que se evalúa mirando la subcategoría completa. Al revés también: si un producto vende menos, conviene revisar si en ese período hubo promociones en otros productos de su subcategoría. La marca propia es **Del Sur**, y tiene más margen que las marcas de proveedores.
