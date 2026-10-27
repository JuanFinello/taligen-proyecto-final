# Analista de datos

Agente que responde preguntas de negocio sobre **Almacenes del Sur** (40 sucursales, AF2025 y AF2026) y arma informes en PDF. Cada número sale de una consulta registrada que se puede volver a correr.

> Estado: semana 1. Está lista la capa semántica; el agente todavía no existe.

## Cómo correrlo

Requiere Python 3.12 y la variable `ANTHROPIC_API_KEY`.

```bash
python3 -m venv .venv
.venv/bin/pip install duckdb anthropic python-dotenv pyyaml
```

## Estructura

```
Data/base/almacenes_del_sur.duckdb    la base (solo lectura)
Data/capa_semantica/
  medidas.yaml                        qué se calcula: métricas y reglas
  esquema.yaml                        sobre qué datos: tablas, columnas, joins, dimensiones
  glosario.md                         con qué criterio
  medidas_original.yaml               el archivo original, como referencia
Data/preguntas/                       preguntas, conversaciones y pedidos de informe
```

## Análisis de los datos

Antes de construir el agente revisé las 8 tablas y sus joins contra la base (22-10-2026). La estructura está limpia: todos los joins calzan y no duplican filas, no hay nulos, claves repetidas ni textos mal escritos, los signos son coherentes y el precio de cada venta coincide con `precio_lista`. Hay un solo error de carga: el presupuesto de ene-2026, Perfumería, región Sur, viene ×10. Una trampa de calendario: la primera y la última semana tienen 5 y 4 días, así que por semana parecen caídas. El resto son eventos reales que el agente tiene que saber explicar: el aumento de costo de PR01 desde ago-2025, la caída de las comparables del Oeste desde la apertura de S39, el quiebre de stock de PR09 en el Norte en sep-2025, quiebres crónicos en Almacén (P0005, S10, S38) y ventas bajo costo por promociones. Todo está, con gráficos, en `Modelo de datos.canvas`; en `esquema.yaml` quedaron el error del presupuesto, las semanas incompletas, PR01 y el Oeste.

## Preguntas

Estudio las preguntas de a una para entender el patrón general. Casi todas se ordenan en **qué + de qué + cuándo**: qué se mide (la métrica), de qué (los filtros: cadena, categoría, región…) y cuándo (el período). Es el mismo formulario que el modelo le completa a `calcular()`. Las trampas suelen estar en las palabras que define el glosario: en P01 ("¿Cuánto vendió la cadena en el AF2025?"), "vendió" son ventas netas, no brutas, y AF2025 va de mayo de 2024 a abril de 2025, no es el año calendario.

## Decisiones de diseño

**1. Métricas y estructura en archivos separados.** El `medidas.yaml` original mezclaba las métricas con los joins y las dimensiones. Moví toda la estructura a `esquema.yaml`, así cada archivo responde una sola pregunta y nada está escrito dos veces. Descarté dejar la estructura repartida entre los dos archivos o duplicarla. Costo: las fórmulas usan alias definidos en `esquema.yaml`, así que los dos archivos van juntos.

**2. El modelo elige la métrica y los filtros; la fórmula la pone el código.** *(Por implementar.)* Así no puede confundir bruto con neto, ni el año fiscal con el calendario, y cada respuesta deja registrados la métrica, los filtros y el SQL. El SQL escrito por el modelo queda solo para lo que la capa no cubre.

**3. Al modelo le llega una versión compacta.** *(Por implementar.)* Solo lo que necesita para decidir: métricas (id, nombre, sinónimos, unidad), dimensiones con sus valores válidos y reglas. Las fórmulas y los joins son para el código. No es por costo (los tres archivos suman unos 7.500 tokens), sino porque a un modelo chico el texto irrelevante lo confunde.

**4. Tres tools en el servidor MCP.** *(Por implementar.)* Alcanzan para las preguntas puntuales, comparativas y de ranking de la semana 1 (P01–P12, salvo las apartadas P09 y P12). `ver_modelo` devuelve la versión compacta de la decisión 3; `calcular(metrica, filtros, agrupar_por)` arma el SQL desde los YAML, lo corre y devuelve el número con su SQL (con `agrupar_por` cubre los rankings, y una comparativa son dos llamadas); `consultar_sql` es SQL de solo lectura para lo que la capa no cubre, y también queda registrado. Descarté una sola tool de SQL libre: es más simple, pero deja al modelo rearmar las fórmulas a mano. Pocas tools bien distintas, porque a un modelo chico le cuesta menos elegir.

**5. Cinco preguntas apartadas hasta la semana 5.** P09 (comparativa), P12 (ranking), P14 (diagnóstico), P18 (ambigua) y P19 (sin dato). De cada tipo elegí la que no se repite en las conversaciones ni en los informes, que sí se practican: P06, P07 y P08 se parecen a C1, C2 y C3; P10 y P11 se cruzan con I3 y C2; P13, P15 y P16, con C2, C3 y C4; y P17 es igual a C5. No se usan para ajustar el sistema: dicen si resuelve lo que no vio.

**6. El error de carga del presupuesto queda anotado en el esquema.** En ene-2026, Perfumería, región Sur (10 filas), el presupuesto es 10 veces mayor que lo vendido, mientras que las ventas y los meses vecinos son normales. Lo anoté en la descripción de `presupuesto`. La alternativa era no anotarlo y ver si el agente lo detecta solo con la regla del glosario (comparar con los meses vecinos). Elegí anotarlo para que ninguna respuesta de desvío salga distorsionada.

**7. Al agente se le da el criterio de dónde mirar, no los hallazgos.** *(Para la semana 3, diagnósticos.)* Para que sea propositivo, el agente recibe una guía de qué revisar según la situación: si caen las ventas, el stock (¿hubo quiebre?) y los comparables (¿abrió una sucursal?); si cae el margen, el costo por unidad y las promociones; si hay un desvío enorme contra el presupuesto, los meses vecinos (¿error de carga?); si se compara por semana, la primera y la última, que están incompletas. El número lo encuentra él con una consulta. La alternativa era pasarle los hallazgos del análisis (los del canvas `Modelo de datos`). La descarté por tres razones: citaría números sin una consulta registrada, la evaluación ya no mediría si sabe diagnosticar y, con un modelo chico, el texto de más empeora la elección. Los hallazgos sirven en cambio como respuesta esperada del evaluador.

**8. El modelo pregunta solo si el glosario no resuelve la ambigüedad.** *(Por implementar.)* Si el glosario define la palabra, el modelo aplica la definición y dice qué criterio usó: "ventas" son netas, así que responde con ventas netas y lo aclara. Si el glosario no la resuelve, pregunta o, como mínimo, declara qué supuso: "el último trimestre" puede ser fiscal o calendario, y "el margen" puede ser en % o en pesos (P07). Descarté que pregunte ante cualquier palabra con más de un sentido: molestaría con dudas que el glosario ya resuelve y lo dejaría de lado. Un supuesto por defecto: "el margen", sin aclarar, es **margen %** y su variación va en puntos porcentuales, mostrando también los pesos. Lo elegí porque el glosario solo habla de variaciones de margen en pp, y porque en P07 el margen en pesos casi no cambia (−0,006 %) mientras el % cae 1,2 pp: en pesos se escondería lo que pasó.

**9. El SQL usa siempre el join completo de la tabla.** `procesador_capa_semantica.py` copia el `join` de `esquema.yaml` tal cual, aunque los filtros no usen todas las tablas. Las tablas que sobran no cambian el resultado, porque cada venta tiene exactamente una fecha, un producto, una sucursal y un proveedor (verificado: ninguna fila queda sin pareja). La alternativa era agregar solo los joins que piden los filtros: es más eficiente, pero complica el código, y la diferencia no se nota (P01 tarda 0,03 s con el join completo y da el mismo número). El nombre del script lleva "procesador" para no confundirlo con la carpeta `capa_semantica/`, que tiene los archivos.

**10. `agrupar_por` recibe una lista de dimensiones.** `calcular()` acepta `agrupar_por`, `orden` (`desc` o `asc`) y `limite`, y devuelve una fila por grupo ordenada por el valor: así resuelve los rankings (P10, P11). Es una lista porque un ranking suele necesitar más de una columna: P10 pide código y nombre de la sucursal, así que se pasa `["sucursal", "nombre_sucursal"]`. Descarté que el código agregue el nombre solo cuando se agrupa por sucursal: es más cómodo para el modelo, pero es un caso especial escondido en el código.

**11. Una comparativa es una sola llamada, y la variación la calcula el código.** `calcular()` acepta `comparar_con`, que lleva solo los filtros que cambian en el período anterior: el resto se copia del actual. Por ejemplo, en P06 basta `{"anio_fiscal": 2025}` para que Bebidas y el T3 se mantengan. Devuelve los dos valores con sus filtros completos (para comprobar que compara lo mismo), sus SQL y la variación: en % si la medida está en pesos o unidades, y en pp si es un porcentaje. Esto reemplaza lo que decía la decisión 4 ("una comparativa son dos llamadas"): así la cuenta no la hace el modelo de cabeza y queda registrada. Descarté repetir todos los filtros del período anterior: es más explícito, pero si Haiku se olvida uno, compara cosas distintas sin darse cuenta. Por ahora no se puede comparar y agrupar a la vez (eso hace falta para P12).

**12. Los comparables los aplica el código con `comparables=True`.** Junto con `comparar_con`, el código busca el primer día del período anterior en la tabla `fechas` y deja, en los dos períodos, solo las sucursales con `fecha_apertura` hasta ese día. En P08 el anterior es el AF2025, que empieza el 01-05-2024: quedan 38 sucursales (sin S39 ni S40) y el crecimiento baja de +4,3 % a +2,1 %. Descarté los filtros con operador (`fecha_apertura <= fecha`): son más generales, pero Haiku tendría que calcular la fecha y es fácil errar (AF2025 empieza en 2024).

**13. P05 se resuelve con una métrica nueva, no con SQL del modelo.** Agregué `sucursales_abiertas` (`COUNT(*)` sobre `sucursales`), que cuenta las sucursales que existen; `cantidad_sucursales` cuenta las que vendieron en un período y es la trampa de P05. El sinónimo «sucursales» pasó a la métrica nueva. Para soportarla, `calcular()` usa la tabla sola cuando no tiene `join`. La alternativa era `consultar_sql`, pero que Haiku escriba SQL es justo lo que la capa quiere evitar. Si `consultar_sql` sigue en el agente para lo que la capa no cubre queda para más adelante, cuando se vea qué preguntas no cubre.

**14. El servidor MCP expone solo `ver_modelo()` y `calcular()`.** `servidor_mcp.py` envuelve las dos funciones del procesador sin agregar lógica, y `abiertas_hasta` queda fuera porque lo pone `comparables`. Por ahora no hay `consultar_sql`: con estas dos tools, cada número sale de una métrica definida en la capa. Si alguna pregunta de la semana 5 no se puede responder así, se agrega en ese momento. Cuando `calcular()` falla, el servidor le devuelve a Haiku el motivo (por ejemplo, `anio_fiscal` es un número, `2026`, y no `"AF2026"`) en lugar del error genérico de MCP, para que pueda corregir la llamada. Usa `mcp` 2.x (`MCPServer`, antes llamado `FastMCP`).

**15. `calcular()` rechaza las dimensiones que no están en el join de la métrica.** En la primera corrida del agente, Haiku filtró `sucursales_abiertas` por `fecha` y DuckDB falló con un error de SQL poco claro ("table f not found"): esa métrica usa la tabla `sucursales` sola, sin `fechas`. Ahora el procesador saca los alias del `join` y, antes de armar el SQL, rechaza la dimensión con un mensaje que lista las válidas para esa métrica, así Haiku puede corregirse. Descarté marcar en `ver_modelo()` qué dimensiones sirven para cada métrica: es más preventivo, pero agranda lo que Haiku lee en cada pregunta y por ahora el error alcanza. Queda a la vista un hueco: `presupuesto` no se puede filtrar por `categoria` (la dimensión apunta a `p.categoria` y su join no tiene `productos`; el presupuesto guarda la categoría como texto en `pz.categoria`).

**16. `ver_modelo()` incluye la descripción de cada métrica.** En P05, Haiku dudaba si alguna sucursal había cerrado e intentaba filtrar por fecha, aunque la descripción de `sucursales_abiertas` ya decía «ninguna cerró; no lleva período»: la versión compacta de la decisión 4 no la mandaba. Con la descripción, P05 sale en una sola llamada correcta. Cuesta unos pocos cientos de tokens por pregunta. La alternativa era repetir esa información en las reglas, pero habría quedado duplicada.

**17. «Margen bruto» es en pesos; «el margen», sin más, es %.** En P03 («¿qué margen bruto…?») Haiku elegía `margen_pct`, porque su nombre es «Margen bruto %» y el glosario solo habla del %. Agregué la regla a `reglas` y pasé el sinónimo `margen` de `margen_bruto` a `margen_pct`, que contradecía la decisión 8. Ahora P03 da siempre los pesos, aunque a veces pone el % primero. No lo sigo ajustando para no sobreajustar una sola pregunta.

**18. Códigos y comparables, por prompt; `proveedor` pasa a ser el código.** En P10 y P11 Haiku mostraba solo nombres, y en P06 no informaba la variación comparable. Agregué dos líneas al prompt de sistema de `agente.py`: mostrar código y nombre al nombrar sucursales o proveedores, e informar la variación total y la comparable al comparar ventas. Para el proveedor no había una dimensión con el código, así que la armé igual que la de sucursal: `proveedor` es ahora `pr.proveedor_id` y el nombre pasó a `nombre_proveedor`. Descarté agregar un `codigo_proveedor` y dejar `proveedor` como nombre: no cambiaba nada existente, pero dejaba dos patrones distintos para lo mismo.

## Evaluación

*Pendiente.*

## Costos

*Pendiente.*
