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

## Evaluación

*Pendiente.*

## Costos

*Pendiente.*
