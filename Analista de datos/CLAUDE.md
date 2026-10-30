# Analista de datos: proyecto final (Taligen Spring Camp)

Agente que responde preguntas de negocio sobre **Almacenes del Sur** (cadena ficticia, 40 sucursales, AF2025 y AF2026) y arma informes en PDF. Regla central: **cada número sale de una consulta registrada** que se puede mostrar y volver a correr.

El enunciado completo está en `Proyecto Final Analista de datos.pdf` (plan de 7 semanas). Modelo obligatorio: `claude-haiku-5-5`.

## Cómo trabajar con el usuario
- **Respuestas cortas y concisas, sin irse por las ramas** (pedido explícito del usuario).
- Hablar en español y explicar paso a paso, de a una pieza por vez. Verificar que se entienda antes de avanzar.
- Antes de cambiar la organización de archivos, confirmar qué quiere el usuario: ya hubo malentendidos con esto.
- Separar siempre lo que es dato (verificado en la base o en los archivos) de lo que es interpretación propia.
- Los archivos son del usuario: el curso no manda versiones nuevas y todas las decisiones de diseño son suyas.

## Estructura
```
Data/
├── base/almacenes_del_sur.duckdb   base en SOLO LECTURA (8 tablas, ventas = 2,8 M filas)
├── capa_semantica/
│   ├── medidas.yaml                QUÉ se calcula: métricas, métricas derivadas y reglas
│   ├── esquema.yaml                SOBRE QUÉ DATOS: tablas, columnas, alias, joins y dimensiones
│   ├── glosario.md                 CON QUÉ CRITERIO (año fiscal desde mayo, ventas = netas, etc.)
│   └── medidas_original.yaml       copia intacta del curso (solo lectura), solo como referencia
└── preguntas/                      preguntas.json (P01–P20), conversaciones.json (C1–C5),
                                    pedidos_de_informe.json (I1–I3)
.venv/                              Python con duckdb, anthropic, python-dotenv, pyyaml, mcp
```
Correr todo con `.venv/bin/python` desde esta carpeta (el `pip` del venv está roto por el renombre de la carpeta: usar `.venv/bin/python -m pip`). La API key está en la variable de entorno `ANTHROPIC_API_KEY`.

## Decisiones tomadas (2026-10-20)
1. **Sin redundancia entre archivos.** `medidas.yaml` tiene solo métricas y reglas. Toda la estructura de la base (incluidos `tablas_hecho`, `dimensiones` y `nota_dimensiones`, que venían en el original) está en `esquema.yaml`. Las fórmulas usan alias (`v.`, `p.`…) definidos en `esquema.yaml`, así que los dos archivos van juntos.
2. **`esquema.yaml` se mantiene a mano.** Tipos, filas y valores se extrajeron una vez de la base (que no va a cambiar); el script que lo generó se borró para mantener el proyecto simple. Lo demás (`tipo`, `alias`, `grano`, `join`, `descripcion`, `une_con`, `dimensiones`, `nota_dimensiones`) se escribe a mano.
3. **`une_con` solo para relaciones que no están en los `join`**: `ventas.promocion_id → promociones.promocion_id` y `promociones.sku → productos.sku`. Están verificadas: 0 valores sin pareja.
4. **Claude no lee los archivos tal cual.** El código le arma una versión compacta. Claude elige la métrica y los filtros (necesita id, nombre, sinónimos, unidad, dimensiones y valores válidos). Fórmulas, joins y alias son para el código. Tamaños: medidas ~2,3 k tokens, esquema ~3,9 k, glosario ~1,3 k.

## Datos útiles ya verificados
- La base no declara relaciones (sin claves foráneas). Todos los joins se verificaron contra los datos y calzan.
- `presupuesto` no tiene `sku`: se cruza con productos solo por el texto de `categoria`.
- Devoluciones: `tipo_movimiento = 'devolucion'`, con unidades, importes y costo negativos.
- Solo 2 sucursales abrieron dentro del período: S39 (02-06-2025) y S40 (01-07-2025), ambas del Oeste; las demás, en 2022 o antes. Ninguna cerró. Importa para comparables.
- 28.793 ventas tienen `promocion_id`. `promociones` no estaba documentada en el material del curso.
- 308 productos con 282 descripciones: 24 nombres se repiten en 2 o 3 SKU que solo difieren en `precio_lista` (Perfumería, Lácteos, Limpieza, Bebidas). Filtrar por `sku`, nunca por nombre.
- Verificado con SQL directo (no con la capa semántica, que todavía no existe): P03 (margen bruto de Perfumería, AF2026) = **460.758.207 ARS**.

## Estado y próximos pasos
- [x] Entender los archivos de partida y hacer los diagramas (en la bóveda de Obsidian `../taligent_vault/`: `Mapa del proyecto.canvas` y `Modelo de datos.canvas`).
- [x] Separar métricas y estructura en `medidas.yaml` y `esquema.yaml`.
- [x] Completar y revisar a mano las descripciones de `esquema.yaml` (las 8 tablas; también en `Modelo de datos.canvas`).
- [x] Script `procesador_capa_semantica.py` (no confundir con la carpeta `capa_semantica/`): `calcular()` con filtros, `agrupar_por`, `comparar_con` y `comparables`. Resuelve las 10 preguntas de semana 1 con los valores de `chequeos` (2026-10-26).
- [x] `servidor_mcp.py` (mcp 2.x, `MCPServer`): tools `ver_modelo()` y `calcular()`, sin `consultar_sql` (decisión 14). Probado por stdio: P03 da 460.758.207 (2026-10-27).
- [ ] Pendiente decidir si `Mapa del proyecto.canvas` (hoy fuera de la bóveda) se mueve a `taligent_vault/`.
- [x] Apartar 5 preguntas hasta la semana 5: **P09, P12, P14, P18 y P19** (no usarlas para ajustar nada). Semana 1 trabaja con P01–P08, P10 y P11.
- [x] Verificar a mano las 10 preguntas de semana 1 con SQL directo (valores en la card `chequeos` de `../taligent_vault/Diseño del agente.canvas`).
- [x] `agente.py`: loop manual de Haiku sobre `servidor_mcp.py`. Primera corrida (2026-10-27): los 10 números dan bien; fallan chequeos de criterio en P03 (elige `margen_pct`, varía entre corridas), P05, P06 (no informa comparables), P10 y P11 (sin códigos). El error de P05 se corrigió (decisión 15).
- [x] Fallos de la primera corrida corregidos (decisiones 16 a 18): P05, P06, P10 y P11 cumplen el chequeo.
- [ ] Pendientes de criterio: P03 a veces pone el % antes que los pesos; P07 escribió mal el año del período ("ago a oct de 2026").
- [x] `evaluador.py` + `Data/preguntas/esperados.yaml` (decisión 19). Primera evaluación (2026-10-27): **10 de 10 pasan**. Correr: `.venv/bin/python evaluador.py [P03 P05 …]`.
- [ ] **Siguiente:** semana 2 (cuentas en código, criterio ante ambigüedad, conversaciones).
- [x] `README.md` con las decisiones 1 a 4. **Cada decisión nueva se agrega ahí apenas se toma** (qué se hizo, alternativas, por qué), redactada para que la revise el usuario. Al README van decisiones, no pasos de trabajo. **Estilo conciso**: un párrafo por decisión, en negrita el título, sin subsecciones.
