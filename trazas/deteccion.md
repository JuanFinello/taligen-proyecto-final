# Tasa de detección de `verificar_base.py` (decisión 89)

Comando: `.venv/bin/python evaluacion/robustez/deteccion.py 30` · 30 semillas · ~240 s, sin modelo · sobre el año simulado (decisión 88), con los errores en el AF2027

| Error de carga | Nivel esperado | Control | Detectado |
|---|---|---|---|
| un día de una sucursal cargado dos veces | error | ventas: una fila por fecha, sucursal, producto y tipo | **30 de 30** (100 %) |
| ventas de un producto que no está en el maestro | error | ventas: cada fila encuentra su productos | **30 de 30** (100 %) |
| el descuento restado dos veces en un día de una sucursal | error | ventas: neto = bruto − descuento | **30 de 30** (100 %) |
| devoluciones de un día con el signo cambiado | error | ventas: devoluciones con unidades negativas y ventas con positivas | **30 de 30** (100 %) |
| ventas con una promoción que ya había terminado | error | ventas: la promoción es de ese producto y estaba vigente | **30 de 30** (100 %) |
| una foto de stock con unidades negativas | error | stock: sin unidades negativas | **30 de 30** (100 %) |
| el mes fiscal corrido en un mes del calendario | error | fechas: año, mes y trimestre fiscal | **30 de 30** (100 %) |
| presupuesto de una categoría mal escrita («Almacen») | error | presupuesto: categorías que existen en productos | **30 de 30** (100 %) |
| un día de una sucursal sin cargar | aviso | ventas: días sin ventas de una sucursal abierta (¿carga incompleta?) | **30 de 30** (100 %) |
| una semana de stock de una sucursal sin cargar | aviso | stock: semanas sin foto de una sucursal abierta | **30 de 30** (100 %) |
| el costo de un producto ×10 durante un mes | aviso | ventas: el costo por unidad de un producto salta contra sus meses vecinos | **30 de 30** (100 %) |
| el presupuesto de una celda (mes, sucursal, categoría) ×10 | aviso | presupuesto: presupuesto ÷ ventas salta contra sus meses vecinos (decisión 84) | **30 de 30** (100 %) |
| los importes de un día de una sucursal en centavos (×100) | aviso | ventas: las ventas de un día de una sucursal saltan contra el mismo día de las semanas vecinas | **30 de 30** (100 %) |
| las unidades de un producto en una sucursal y un día cargadas en miles | aviso | ventas: una fila con más de 50 veces las unidades habituales de su producto | **30 de 30** (100 %) |

**Total: 420 de 420 (100.0 %).**

## Errores sin control propio (contra el problema del oráculo)

Errores comunes de carga elegidos sin buscar un control que los atrape (no es un oráculo independiente: los eligió quien conoce los controles): cuenta como detectado si cualquier control marca más filas.

| Error de carga | Detectado | Por qué control |
|---|---|---|
| un día de una sucursal cargado con el código de otra | **30 de 30** (100 %) | presupuesto: presupuesto ÷ ventas salta contra sus meses vecinos (decisión 84); ventas: días sin ventas de una sucursal abierta (¿carga incompleta?); ventas: las ventas de un día de una sucursal saltan contra el mismo día de las semanas vecinas |
| un día de una sucursal cargado sin una categoría | **0 de 30** (0 %) | — |
| la foto de stock de una sucursal repite la de la semana anterior | **30 de 30** (100 %) | stock: una foto de una sucursal idéntica a la de la semana anterior |
| el presupuesto de una sucursal cargado con los números del mes siguiente | **4 de 30** (13 %) | presupuesto: presupuesto ÷ ventas salta contra sus meses vecinos (decisión 84) |
| un día de una sucursal con los importes 5 % más altos (lista de precios vieja) | **30 de 30** (100 %) | ventas: el bruto no es unidades × precio de lista |
| un día de una sucursal cargado con la fecha del día siguiente | **30 de 30** (100 %) | ventas: días sin ventas de una sucursal abierta (¿carga incompleta?); ventas: la promoción es de ese producto y estaba vigente |
