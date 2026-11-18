# Guía de ingesta de datos nuevos

Cómo sumar datos a `almacenes_del_sur.duckdb` (meses nuevos, sucursales, productos, proveedores, promociones) sin romper el agente ni los informes. El agente abre la base en solo lectura: la ingesta se hace aparte, con estos pasos.

## Qué se adapta solo y qué no

**Solo, sin tocar nada:** los valores válidos y los rangos de cada dimensión (meses, años fiscales, sucursales, categorías…), que el procesador lee de la base al arrancar (decisión 62); el período que cubre la base, que `ver_modelo` le informa a Haiku (`cobertura`); «el último mes» o «el último trimestre», que se cuentan desde el último dato; las sucursales comparables, que salen de `fecha_apertura`; y los informes programados, que toman el período del calendario real y avisan si todavía no hay datos.

**A mano:** una tabla o columna nueva va en `esquema.yaml` (y, si es una métrica, en `medidas.yaml`); un criterio nuevo del negocio, en `glosario.md`; y si la ingesta corrige datos históricos, los valores de `Data/preguntas/esperados.yaml` que cambien.

## Reglas que tienen que cumplir los datos

La base no declara claves foráneas: si algo no calza, los números salen mal sin ningún error. `verificar_base.py` controla todo esto.

1. **Agregar, no reemplazar.** Lo histórico no se toca. Si hay que corregir historia, es otra tarea: revisar `esperados.yaml` después.
2. **Pesos constantes.** Los importes van en pesos constantes y sin impuestos. Si la ingesta cambia la fecha de reexpresión, se reexpresa la base entera, no solo lo nuevo; si no, las comparaciones entre períodos mezclan inflación.
3. **`fechas` primero.** Un día por fila, sin huecos, cubriendo todas las fechas nuevas de ventas, stock y presupuesto. Las columnas fiscales siguen la regla del glosario: el año fiscal empieza el 1 de mayo y se nombra por el año en que termina (mayo de 2026 → `anio_fiscal` 2027, `mes_fiscal` 1, `trimestre_fiscal` 1). `semana_inicio` es el lunes de esa semana.
4. **Dimensiones antes que hechos.** Una sucursal nueva, con `fecha_apertura` (las comparables la usan); un producto nuevo, con `sku` único y un `proveedor_id` que exista; una promoción nueva, con `promocion_id` único y el `sku` de un producto existente.
5. **Hechos.**
   - `ventas`: una fila por fecha, sucursal, producto y tipo (`venta` o `devolucion`); las devoluciones con unidades, importes y costo negativos; ninguna venta antes de la apertura de su sucursal; si lleva `promocion_id`, la promoción es de ese producto y estaba vigente ese día.
   - `stock_semanal`: una fila por semana (el lunes), sucursal y producto.
   - `presupuesto`: una fila por mes (el día 1), sucursal y categoría; la categoría tiene que existir en `productos`.
6. **Al día.** Los informes programados salen por calendario real (decisión 65): cada lunes, el de la semana que cerró; el primer lunes del mes, también el del mes anterior (y el del trimestre o el año fiscal, si cerraron). Si la base todavía no cubre ese período, no hay informe: avisan que faltan datos. Conviene cargar cada semana antes del lunes a las 8.

## Pasos

```bash
# 1. Copia de respaldo de la base actual
cp Data/base/almacenes_del_sur.duckdb Data/base/almacenes_del_sur.respaldo.duckdb

# 2. Cargar los datos nuevos en una COPIA (con el cliente de DuckDB o un script propio)
cp Data/base/almacenes_del_sur.duckdb /tmp/base_nueva.duckdb
#    … INSERT INTO fechas …, sucursales, productos, proveedores, promociones, después ventas, stock, presupuesto

# 3. Verificar la copia: tiene que dar todos los controles bien
.venv/bin/python verificar_base.py /tmp/base_nueva.duckdb

# 4. Probar el agente sobre la copia, con una pregunta del período nuevo
BASE_ALMACENES=/tmp/base_nueva.duckdb .venv/bin/python agente.py "¿Cuánto vendimos el último mes?"

# 5. Reemplazar la base y comprobar que lo de antes sigue igual
cp /tmp/base_nueva.duckdb Data/base/almacenes_del_sur.duckdb
.venv/bin/python verificar_base.py
.venv/bin/python evaluador.py        # si no se tocó historia, tiene que seguir pasando todo
```

Si `verificar_base.py` marca un error, se corrige en la copia y se vuelve al paso 3. Los avisos (⚠) no bloquean: son cosas raras que pueden ser reales o un error de carga (un salto de 3 veces contra los meses o semanas vecinas, un día sin ventas, un texto escrito como una orden para el asistente). Hay que mirarlos uno por uno antes de dar la base por buena; los dos de la base original son conocidos: el presupuesto de Perfumería del Sur de enero de 2026 y el texto de P0040 (decisión 85). El informe programado también corre `verificar_base.py` antes de arrancar: con la base rota no gasta en el modelo, lo anota en `salidas/programado/historial.txt` y avisa.
