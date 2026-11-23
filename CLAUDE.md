# Analista de datos · Almacenes del Sur

Instrucciones para agentes de código que trabajen en este repo. La presentación del proyecto está en `README.md`; el porqué de cada decisión, en `docs/decisiones.md`.

Agente que responde preguntas de negocio sobre **Almacenes del Sur** (cadena ficticia: 40 sucursales, AF2025 y AF2026; admite ingestas de datos nuevos) y arma informes en PDF. Regla central: **cada número sale de una consulta registrada** que se puede mostrar y volver a correr. Modelo obligatorio: `claude-haiku-5-5`.

## Estructura y comandos
- Todo se corre desde la raíz del repo con `.venv/bin/python`: los scripts usan rutas relativas a la raíz. La API key va en `ANTHROPIC_API_KEY` (o en `.env`, que carga el `Makefile`).
- `analista/`: el sistema. Los módulos se importan entre sí sin paquete, porque Python agrega la carpeta del script al path; los scripts de `evaluacion/` y `tests/` agregan `analista/`.
- `evaluacion/`: evaluador, corrida completa, chequeos de informes y los tests de robustez (`evaluacion/robustez/`, uno por archivo; método y resultados en `docs/evaluacion.md`).
- `tests/`: tests unitarios sin modelo (pytest, configurado en `pyproject.toml`). **Correrlos (`make tests`) después de tocar la capa, los controles o los hooks.**
- Atajos: `make ayuda`. Los demás comandos, con sus opciones, están en el README («Todos los comandos, sin make»).
- Medir un cambio que afecta a Haiku: `CAMBIO="decisión N" .venv/bin/python evaluacion/evaluador.py` 2 o 3 veces por versión y `analista/registro.py --comparar A B`. Cada llamada al modelo queda en `registros/llamadas.jsonl` con la versión del diseño (huella de los archivos que leen o deciden por Haiku).
- `salidas/` y `registros/` no se commitean; lo que se muestra va a `trazas/` (índice en `trazas/README.md`) y a `docs/informes/`.
- Antes de dar por bueno un cambio que afecta a Haiku, medirlo: evaluador y, si el comportamiento varía, varias corridas.

## Convenciones
- Los canvas de `docs/diagramas/` se editan en Obsidian (bóveda fuera del repo, `../taligent_vault/`); después de copiarlos, regenerar sus páginas con `python3 docs/diagramas/canvas_a_md.py docs/diagramas`.
- Código, nombres de archivos, métricas y dimensiones en español, en snake_case.
- `procesador_capa_semantica.py` (el script) no es lo mismo que `Data/capa_semantica/` (los YAML).
- `Data/base/almacenes_del_sur.duckdb` se abre en **solo lectura** (la ingesta se hace aparte, en una copia, según `Data/base/INGESTA.md`). `medidas_original.yaml` es la copia del curso: no se toca.
- `medidas.yaml` y `glosario.md` tienen finales de línea CRLF (Windows): un `sed` con `$` no encuentra las líneas. Editarlos conservando el CRLF.
- Los valores esperados van en `Data/preguntas/esperados.yaml`, no en el código. Los hallazgos de los diagnósticos también, como comentario.
- P09, P12, P14, P18 y P19 se abrieron en la semana 5 (decisión 79) y quedan como **reserva** (decisión 80, `RESERVA` en `esperados.yaml`): **nunca se ajusta nada por una falla de ellas** (si un cambio las rompe, se deshace el cambio), los ajustes se diseñan mirando solo las otras, y el evaluador las informa aparte.
- Para no sobreajustar, no se corrige el prompt o la capa por un detalle de estilo de una sola pregunta.
- **Cada decisión nueva se agrega a `docs/decisiones.md` apenas se toma** (qué se hizo, alternativas, por qué), con su ancla `<a id="dN"></a>`, su título `### N. …` y su entrada en el índice por tema. Van decisiones, no pasos de trabajo. Si cambia un resultado, se actualizan también `README.md` (Resultados) y `docs/evaluacion.md`.

## Decisiones de diseño (el por qué; el detalle de todas está en docs/decisiones.md)
- **Las medidas salen siempre de `calcular()`; el SQL libre es solo para lo que la capa no cubre** (decisiones 14 y 34). Así cada número sale de una métrica definida en la capa semántica y queda registrado su SQL, que es la regla central del proyecto. `consultar_sql` (listados, como promociones vigentes) abre la base en solo lectura y **sin acceso externo**: `read_only` solo no frena `COPY … TO` ni la lectura de archivos. `buscar_producto` pasa de un nombre a su sku (decisión 33). El servidor usa mcp 2.x (`MCPServer`, no `FastMCP`).
- **Cada archivo de la capa responde una sola pregunta y nada está escrito dos veces** (decisiones 1 y 21). `medidas.yaml`: qué se calcula (solo métricas). `esquema.yaml`: sobre qué datos (tablas, alias, joins, dimensiones). `glosario.md`: con qué criterio; es la única fuente de criterio y va entero en el prompt de sistema. Las fórmulas usan los alias de `esquema.yaml`, así que los dos YAML van juntos.
- **`esquema.yaml` se mantiene a mano, pero los valores válidos y rangos se leen de la base al arrancar** (`valores: de la base`, decisión 62), para que una ingesta entre sola. Nada de período fijo en el glosario: la cobertura la da `ver_modelo`. `une_con` se usa solo para relaciones que no están en ningún `join`.
- **Haiku no lee los YAML tal cual** (decisión 3). El código le arma una versión compacta (`ver_modelo()`, ~1.700 tokens; el glosario, ~1.360) con lo que necesita para elegir la métrica y los filtros. Las fórmulas, los joins y los alias quedan para el código, porque a un modelo chico el texto que no le sirve lo confunde.
- **Un período de días va como rango** (`{"fecha": {"desde", "hasta"}}`, decisión 69): una lista de fechas cuenta solo esos días, y una de dos fechas salteadas da error.
- **Un desvío que incluye presupuesto sospechoso trae un aviso** (decisión 84): celda (mes, sucursal, categoría) con presupuesto ÷ ventas 3 veces distinto de sus meses vecinos. Lo hace el código, no el prompt.
- **Los errores de `calcular()` le explican a Haiku qué corregir** (decisiones 14, 15 y 25): dimensión no válida para esa métrica, valor que no existe (con la lista de válidos). Con el error genérico de MCP no puede corregirse solo.
- **Al agente se le da criterio, no hallazgos** (decisiones 7 y 24). Las respuestas de los diagnósticos no van en el esquema ni en el glosario. Los canvas (`docs/diagramas/`) sí los tienen: son documentación, y nada del sistema los lee ni los pone en un prompt.

## Datos de la base que no se ven en el código
- La base no declara relaciones (sin claves foráneas). Todos los joins se verificaron contra los datos y calzan, incluidos los de `une_con` (`ventas.promocion_id → promociones`, `promociones.sku → productos`).
- `presupuesto` no tiene `sku`: no se une con productos; su categoría es `pz.categoria` (`dimensiones_propias`, decisión 22).
- Devoluciones: `tipo_movimiento = 'devolucion'`, con unidades, importes y costo negativos.
- Al armar la base, solo 2 sucursales habían abierto dentro del período: S39 (02-06-2025) y S40 (01-07-2025), ambas del Oeste; las demás, en 2022 o antes. Ninguna cerró. Importa para comparables.
- `promociones` no estaba documentada en el material del curso (28.793 ventas tienen `promocion_id`).
- 308 productos con 282 descripciones: 24 nombres se repiten en 2 o 3 SKU que solo difieren en `precio_lista`. **Filtrar por `sku`, nunca por nombre.**
