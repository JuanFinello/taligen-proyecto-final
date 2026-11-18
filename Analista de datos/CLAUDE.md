# Analista de datos: proyecto final (Taligen Spring Camp)

Agente que responde preguntas de negocio sobre **Almacenes del Sur** (cadena ficticia; al armarse, 40 sucursales, AF2025 y AF2026; admite ingestas de datos nuevos) y arma informes en PDF. Regla central: **cada número sale de una consulta registrada** que se puede mostrar y volver a correr.

El enunciado completo está en `Proyecto Final Analista de datos.pdf` (plan de 7 semanas). Modelo obligatorio: `claude-haiku-5-5`.

## Comandos
Todo se corre desde esta carpeta con `.venv/bin/python` (los scripts usan rutas relativas). La API key está en la variable de entorno `ANTHROPIC_API_KEY`.
- Chat para la demo (decisión 83): `.venv/bin/python puerta.py` sin argumentos; «?» muestra cada consulta en castellano (`explicar.py`), su resultado y su SQL.
- Hacer una pregunta (la puerta, decisión 78): `.venv/bin/python puerta.py "¿Cuál fue el margen bruto de Perfumería en el AF2026?"`. Reconoce el tipo y la manda al agente (`agente.py`) o, si es diagnóstico o informe, al coordinador (`informes.py`). `puerta.py --medir`: solo la clasificación contra `TIPOS` de `esperados.yaml`. El agente levanta solo `servidor_mcp.py` por stdio.
- Conversación: un argumento por turno. Guardar la traza (respuesta + consultas con SQL): `--traza trazas/X.md` antes de las preguntas.
- Todo con un comando (semana 6, decisión 81): `.venv/bin/python correr_todo.py [ids]` (20 preguntas, 5 conversaciones y 3 informes por la puerta, de a 5; ~US$ 0,10 y ~2 min). Resumen en `salidas/completa-<corrida>/resumen.md`.
- Evaluar: `.venv/bin/python evaluador.py [--veces N] [P03 C1 …]` (pasa por la puerta, decisión 78; vuelve a correr las consultas declaradas; ambigua y sin dato como el enunciado, decisiones 75–76). Sin ids corre todas (21: preguntas y conversaciones C1–C5, cada turno con su chequeo), de a 5 en paralelo (~60 s); con `--veces N` aprueba solo si pasa las N veces (Haiku varía entre corridas).
- Costo y tiempo: cada llamada al modelo queda en `registros/llamadas.jsonl` (no se commitea). `.venv/bin/python registro.py` resume la última corrida (`--todas`: una línea por corrida). Cada línea lleva la versión del diseño (huella de los archivos que leen o deciden por Haiku); para medir un cambio: `CAMBIO="decisión N" .venv/bin/python evaluador.py` 2 o 3 veces por versión y `registro.py --comparar A B`.
- Verificar la base (después de una ingesta): `.venv/bin/python verificar_base.py [ruta.duckdb]`: errores que bloquean (estructura, valores imposibles, importes que no cierran) y avisos que no (saltos contra los vecinos, días faltantes, textos con forma de orden; decisión 85). Guía: `Data/base/INGESTA.md`. Otra base para probar: `BASE_ALMACENES=ruta .venv/bin/python agente.py …`.
- Informes programados por calendario real (decisión 65): `informe_programado.py [--hoy AAAA-MM-DD]` (cada lunes, la semana que cerró; el primer lunes del mes, también el mes, y el trimestre o el AF fiscal si cerraron; cada uno responde otra pregunta, decisión 66; si faltan datos, avisa); lo lanza `informe-almacenes.timer` de systemd del usuario los lunes a las 8 (archivos en `programado/`, instalados en `~/.config/systemd/user/`). Historial: `salidas/programado/historial.txt`.
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
- `Data/base/almacenes_del_sur.duckdb` se abre en **solo lectura** (la ingesta se hace aparte, en una copia, según `Data/base/INGESTA.md`). `medidas_original.yaml` es la copia del curso: no se toca.
- `medidas.yaml` y `glosario.md` tienen finales de línea CRLF (Windows): un `sed` con `$` no encuentra las líneas. Editarlos conservando el CRLF.
- Los valores esperados van en `Data/preguntas/esperados.yaml`, no en el código. Los hallazgos de los diagnósticos también, como comentario.
- P09, P12, P14, P18 y P19 se abrieron en la semana 5 (decisión 79) y quedan como **reserva** (decisión 80, `RESERVA` en `esperados.yaml`): **nunca se ajusta nada por una falla de ellas** (si un cambio las rompe, se deshace el cambio), los ajustes se diseñan mirando solo las otras, y el evaluador las informa aparte. Para la entrega, el usuario escribe preguntas nuevas que Claude no ve hasta correrlas una vez (los valores esperados, con SQL, recién ese día y antes de correr el agente).
- Para no sobreajustar, no se corrige el prompt o la capa por un detalle de estilo de una sola pregunta.
- **Cada decisión nueva se agrega al `README.md` apenas se toma** (qué se hizo, alternativas, por qué). Al README van decisiones, no pasos de trabajo. Estilo: un párrafo por decisión, título en negrita, sin subsecciones.

## Decisiones de diseño (el por qué; el detalle de todas está en el README)
- **Las medidas salen siempre de `calcular()`; el SQL libre es solo para lo que la capa no cubre** (decisiones 14 y 34). Así cada número sale de una métrica definida en la capa semántica y queda registrado su SQL, que es la regla central del proyecto. `consultar_sql` (listados, como promociones vigentes) abre la base en solo lectura y **sin acceso externo**: `read_only` solo no frena `COPY … TO` ni la lectura de archivos. `buscar_producto` pasa de un nombre a su sku (decisión 33). El servidor usa mcp 2.x (`MCPServer`, no `FastMCP`).
- **Cada archivo de la capa responde una sola pregunta y nada está escrito dos veces** (decisiones 1 y 21). `medidas.yaml`: qué se calcula (solo métricas). `esquema.yaml`: sobre qué datos (tablas, alias, joins, dimensiones). `glosario.md`: con qué criterio; es la única fuente de criterio y va entero en el prompt de sistema. Las fórmulas usan los alias de `esquema.yaml`, así que los dos YAML van juntos.
- **`esquema.yaml` se mantiene a mano, pero los valores válidos y rangos se leen de la base al arrancar** (`valores: de la base`, decisión 62), para que una ingesta entre sola. Nada de período fijo en el glosario: la cobertura la da `ver_modelo`. `une_con` se usa solo para relaciones que no están en ningún `join`.
- **Haiku no lee los YAML tal cual** (decisión 3). El código le arma una versión compacta (`ver_modelo()`, ~1.700 tokens; el glosario, ~1.360) con lo que necesita para elegir la métrica y los filtros. Las fórmulas, los joins y los alias quedan para el código, porque a un modelo chico el texto que no le sirve lo confunde.
- **Un período de días va como rango** (`{"fecha": {"desde", "hasta"}}`, decisión 69): una lista de fechas cuenta solo esos días, y una de dos fechas salteadas da error.
- **Un desvío que incluye presupuesto sospechoso trae un aviso** (decisión 84): celda (mes, sucursal, categoría) con presupuesto ÷ ventas 3 veces distinto de sus meses vecinos. Lo hace el código, no el prompt.
- **Los errores de `calcular()` le explican a Haiku qué corregir** (decisiones 14, 15 y 25): dimensión no válida para esa métrica, valor que no existe (con la lista de válidos). Con el error genérico de MCP no puede corregirse solo.
- **Al agente se le da criterio, no hallazgos** (decisiones 7 y 24). Las respuestas de los diagnósticos no van en el esquema ni en el glosario. Los canvas de la bóveda sí los tienen: son documentación del usuario y ningún agente debe leerlos.

## Datos de la base que no se ven en el código
- La base no declara relaciones (sin claves foráneas). Todos los joins se verificaron contra los datos y calzan, incluidos los de `une_con` (`ventas.promocion_id → promociones`, `promociones.sku → productos`).
- `presupuesto` no tiene `sku`: no se une con productos; su categoría es `pz.categoria` (`dimensiones_propias`, decisión 22).
- Devoluciones: `tipo_movimiento = 'devolucion'`, con unidades, importes y costo negativos.
- Al armar la base, solo 2 sucursales habían abierto dentro del período: S39 (02-06-2025) y S40 (01-07-2025), ambas del Oeste; las demás, en 2022 o antes. Ninguna cerró. Importa para comparables.
- `promociones` no estaba documentada en el material del curso (28.793 ventas tienen `promocion_id`).
- 308 productos con 282 descripciones: 24 nombres se repiten en 2 o 3 SKU que solo difieren en `precio_lista`. **Filtrar por `sku`, nunca por nombre.**

## Fuera del proyecto
- Bóveda de Obsidian `../taligent_vault/`: `Modelo de datos.canvas` y `Diseño del agente.canvas` (la card `chequeos` tiene los valores verificados a mano con SQL). `Mapa del proyecto.canvas` está en esta carpeta, fuera de la bóveda.
- Obsidian es un AppImage sin el enlace `obsidian://` registrado: se abre con `~/Documentos/programas/Obsidian-1.11.5.AppImage "obsidian://open?vault=taligent_vault&file=…"`.

## Dónde estamos
Semanas 1 y 2 cerradas. **Semana 3 completa (2026-11-13), decisiones 38–57.** El evaluador controla 17 casos: 17 de 17 en las últimas corridas completas.
- Informes y diagnósticos: `informes.py "pedido" [carpeta]` (coordinador planifica → analistas, uno por pregunta → coordinador redacta → el código controla y arma). Informe: PDF de una página + anexo (decisiones 53–54); diagnóstico: `diagnostico.md` (55). Cada salida deja `informe.json`, `consultas.sql` y `traza.md` en `salidas/` (no se commitea); `--rearmar` y `--traza` rehacen sin llamar al modelo. Entregas: `trazas/I1.md` y `trazas/P16.md`.
- `controles.py`: ningún número sin respaldo en una consulta (49), en el agente y en la redacción; de los textos solo toma tamaños («300 g»), por P0040 (57). Adelanta el hook de la semana 4.
- `registro.py`: costo, tiempo y versión del diseño de cada llamada (45–46); `--comparar A B` mide cada cambio.
- **Semana 4 completa (2026-11-16), decisiones 58–71**: `hooks.py` (antes de cada tool: tools permitidas por agente y solo un SELECT en `consultar_sql`; después: registra la consulta; al terminar: números sin respaldo), `PERMITIDAS` por agente (coordinador sin tools) y el glosario servido por el servidor MCP como prompt `glosario`. Ingesta de datos nuevos (62–63: valores de la base, `verificar_base.py`, guía) e informes programados por calendario real, cada uno con su pregunta (64–66). Semana 4 completa.
- Diseño del PDF revisado contra bibliografía y escrito para la gerencia (decisiones 67–68 y 70–71: identificación arriba, mensaje como título, 2 o 3 puntos, formato uniforme, tiempo en columnas). Queda la tipografía, solo por gusto.
- **Semana 5 en curso**: caché del prefijo (72: evaluador US$ 0,073 → ~0,03), registro de cada respuesta por salida estructurada, validado antes de guardarse en `registros/respuestas.jsonl` (73, `salida.py`), y corridas en paralelo; la Batch API no encaja con el loop (74). Revisión total (75–77): el evaluador vuelve a correr las consultas declaradas, la ambigua y la sin dato se evalúan como el enunciado, el plan se corrige, quiebre relativo en el glosario. Una sola puerta que clasifica cada pregunta y elige agente o coordinador (78, `puerta.py`). Apartadas abiertas: pasan las cinco (79), quedan como reserva (80). **Semana 6**: todo con un comando (81, `correr_todo.py`). Respuestas vacías de Haiku y rangos «entre X y Y millones» (82): I2 ya detecta el error de carga del presupuesto.
- Pendiente: decidir si `Mapa del proyecto.canvas` se mueve a la bóveda.
