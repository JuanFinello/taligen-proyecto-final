# Analista de datos: proyecto final (Taligen Spring Camp)

Agente que responde preguntas de negocio sobre **Almacenes del Sur** (cadena ficticia, 40 sucursales, AF2025 y AF2026) y arma informes en PDF. Regla central: **cada número sale de una consulta registrada** que se puede mostrar y volver a correr.

El enunciado completo está en `Proyecto Final Analista de datos.pdf` (plan de 7 semanas). Modelo obligatorio: `claude-haiku-5-5`.

## Comandos
Todo se corre desde esta carpeta con `.venv/bin/python` (los scripts usan rutas relativas). La API key está en la variable de entorno `ANTHROPIC_API_KEY`.
- Hacer una pregunta al agente: `.venv/bin/python agente.py "¿Cuál fue el margen bruto de Perfumería en el AF2026?"` (levanta solo `servidor_mcp.py` por stdio; no hace falta correrlo aparte).
- Evaluar: `.venv/bin/python evaluador.py [--veces N] [P03 P05 …]`. Sin ids corre todas; con `--veces N` cada pregunta aprueba solo si pasa las N veces (Haiku varía entre corridas).
- Instalar paquetes: `.venv/bin/python -m pip install …`. El `pip` del venv está roto desde que se renombró la carpeta.

## Cómo trabajar con el usuario
- **Respuestas cortas y concisas, sin irse por las ramas** (pedido explícito del usuario).
- Hablar en español y explicar paso a paso, de a una pieza por vez. Primero simple, después detalles. Verificar que se entienda antes de avanzar.
- Antes de cambiar la organización de archivos, confirmar qué quiere el usuario: ya hubo malentendidos con esto.
- Separar siempre lo que es dato (verificado en la base o en los archivos) de lo que es interpretación propia.
- Los archivos son del usuario: el curso no manda versiones nuevas y todas las decisiones de diseño son suyas.
- Antes de dar por bueno un cambio que afecta a Haiku, medirlo: evaluador y, si el comportamiento varía, varias corridas.

## Convenciones
- Código, nombres de archivos, métricas y dimensiones en español, en snake_case.
- `procesador_capa_semantica.py` (el script) no es lo mismo que `Data/capa_semantica/` (los YAML).
- `Data/base/almacenes_del_sur.duckdb` se abre en **solo lectura**. `medidas_original.yaml` es la copia del curso: no se toca.
- `medidas.yaml` y `glosario.md` tienen finales de línea CRLF (Windows): un `sed` con `$` no encuentra las líneas. Editarlos conservando el CRLF.
- Los valores esperados van en `Data/preguntas/esperados.yaml`, no en el código. Los hallazgos de los diagnósticos también, como comentario.
- **P09, P12, P14, P18 y P19 están apartadas hasta la semana 5**: no usarlas para ajustar nada. La semana 1 trabajó con P01–P08, P10 y P11.
- Para no sobreajustar, no se corrige el prompt o la capa por un detalle de estilo de una sola pregunta.
- **Cada decisión nueva se agrega al `README.md` apenas se toma** (qué se hizo, alternativas, por qué). Al README van decisiones, no pasos de trabajo. Estilo: un párrafo por decisión, título en negrita, sin subsecciones.

## Decisiones de diseño (el por qué; el detalle de todas está en el README)
- **Haiku no escribe SQL: el servidor MCP solo expone `ver_modelo()` y `calcular()`** (decisión 14). Así cada número sale de una métrica definida en la capa semántica y queda registrado su SQL, que es la regla central del proyecto. Si una pregunta no se puede responder así, se agrega una métrica (como `sucursales_abiertas`, decisión 13) en lugar de abrir una tool de SQL libre. El servidor usa mcp 2.x (`MCPServer`, no `FastMCP`).
- **Cada archivo de la capa responde una sola pregunta y nada está escrito dos veces** (decisiones 1 y 21). `medidas.yaml`: qué se calcula (solo métricas). `esquema.yaml`: sobre qué datos (tablas, alias, joins, dimensiones). `glosario.md`: con qué criterio; es la única fuente de criterio y va entero en el prompt de sistema. Las fórmulas usan los alias de `esquema.yaml`, así que los dos YAML van juntos.
- **`esquema.yaml` se mantiene a mano.** Tipos, filas y valores se extrajeron una vez de la base, que no va a cambiar; el script que lo generó se borró a propósito. `une_con` se usa solo para relaciones que no están en ningún `join`.
- **Haiku no lee los YAML tal cual** (decisión 3). El código le arma una versión compacta (`ver_modelo()`, ~1.700 tokens; el glosario, ~1.360) con lo que necesita para elegir la métrica y los filtros. Las fórmulas, los joins y los alias quedan para el código, porque a un modelo chico el texto que no le sirve lo confunde.
- **Los errores de `calcular()` le explican a Haiku qué corregir** (decisiones 14, 15 y 25): dimensión no válida para esa métrica, valor que no existe (con la lista de válidos). Con el error genérico de MCP no puede corregirse solo.
- **Al agente se le da criterio, no hallazgos** (decisiones 7 y 24). Las respuestas de los diagnósticos no van en el esquema ni en el glosario. Los canvas de la bóveda sí los tienen: son documentación del usuario y ningún agente debe leerlos.

## Datos de la base que no se ven en el código
- La base no declara relaciones (sin claves foráneas). Todos los joins se verificaron contra los datos y calzan, incluidos los de `une_con` (`ventas.promocion_id → promociones`, `promociones.sku → productos`).
- `presupuesto` no tiene `sku`: no se une con productos; su categoría es `pz.categoria` (`dimensiones_propias`, decisión 22).
- Devoluciones: `tipo_movimiento = 'devolucion'`, con unidades, importes y costo negativos.
- Solo 2 sucursales abrieron dentro del período: S39 (02-06-2025) y S40 (01-07-2025), ambas del Oeste; las demás, en 2022 o antes. Ninguna cerró. Importa para comparables.
- `promociones` no estaba documentada en el material del curso (28.793 ventas tienen `promocion_id`).
- 308 productos con 282 descripciones: 24 nombres se repiten en 2 o 3 SKU que solo difieren en `precio_lista`. **Filtrar por `sku`, nunca por nombre.**

## Fuera del proyecto
- Bóveda de Obsidian `../taligent_vault/`: `Modelo de datos.canvas` y `Diseño del agente.canvas` (la card `chequeos` tiene los valores verificados a mano con SQL). `Mapa del proyecto.canvas` está en esta carpeta, fuera de la bóveda.
- Obsidian es un AppImage sin el enlace `obsidian://` registrado: se abre con `~/Documentos/programas/Obsidian-1.11.5.AppImage "obsidian://open?vault=taligent_vault&file=…"`.

## Dónde estamos
Semana 1 cerrada y revisada (2026-11-11): con `--veces 3`, 10 de 10 pasan las 3 veces.
- Siguiente: semana 2 (cuentas en código, criterio ante ambigüedad, conversaciones). Ya se sabe que falta: comparar y agrupar a la vez (C1), medidas derivadas (desvío contra presupuesto, participación), y conversaciones (`agente.py` responde una pregunta suelta).
- Pendientes: P07 escribió mal el año del período («ago a oct de 2026»); decidir si `Mapa del proyecto.canvas` se mueve a la bóveda.
