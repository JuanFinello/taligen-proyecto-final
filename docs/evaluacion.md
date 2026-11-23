# Evaluación

## Método

Las mismas reglas valen para el evaluador y para los tests:

- **Lo esperado se calcula antes de correr el agente**, con SQL escrito a mano, sin el procesador de la capa semántica, y se guarda. Si el agente y lo esperado salieran del mismo código, un error en ese código pasaría como acierto.
- **Califica el código, no un modelo.** Se mide la medida usada, el valor con su tolerancia, que la consulta se pueda reproducir y que la puerta la mande por el camino correcto.
- **Hay una reserva.** Las cinco preguntas apartadas del enunciado (P09, P12, P14, P18, P19) no se usaron para ajustar nada. Se abrieron en la semana 5 ([traza](../trazas/apartadas.md)) y desde entonces se informan aparte: miden lo que el diseño no vio.
- **Varias corridas.** Haiku no contesta siempre igual, así que un caso aprueba solo si acierta todas las veces.
- **Es una medición.** Lo que falla en un test se reporta, no se parchea con ese mismo caso.

## Tres niveles

| Nivel | Qué mide | Modelo | Comando |
|---|---|---|---|
| Tests unitarios (`tests/`) | que el código calcule y frene bien: `calcular()` contra los valores esperados, los controles de números sin respaldo, filtros y períodos, y las capas de seguridad | no · 1 s · sin costo | `make tests` |
| Evaluador (`evaluacion/`) | los casos del enunciado, de punta a punta | sí · ~1,5 min · ~US$ 0,05 | `make evaluar` |
| Tests de robustez (`evaluacion/robustez/`) | lo que el enunciado no prueba | sí, salvo 1c y 9 | uno por test |

Los tests unitarios usan los mismos valores esperados del evaluador (calculados con SQL escrito a mano), así que un error en una fórmula, un join o el calendario fiscal se ve sin gastar nada: rompiendo a propósito la fórmula de las ventas netas, fallan 3 de 34.

## Las dos métricas del enunciado

**Acierto de respuesta.** El número cae dentro de la tolerancia: 0,5 en montos, una décima en % y pp, exacto en conteos y el mismo orden en rankings. Una ambigua pasa si consultó las dos lecturas o declaró en los supuestos la que eligió. Una sin dato pasa si dice que el dato no está y no responde con otro número.

**Acierto de consulta.** El evaluador vuelve a ejecutar las consultas que declara cada respuesta, con los mismos argumentos, y controla que de ellas salga el valor reportado (decisión 75). Un número correcto que sale de la medida equivocada es una coincidencia, no un acierto.

En las conversaciones se califica cada turno por separado: un turno que pierde un filtro del anterior falla, aunque el número sea plausible.

## Evaluador

```bash
.venv/bin/python evaluacion/evaluador.py [--veces N] [P03 C1 …]
```

Corre 16 preguntas y las 5 conversaciones (21 casos) contra [`Data/preguntas/esperados.yaml`](../Data/preguntas/esperados.yaml), de a 5 en paralelo, en alrededor de un minuto y medio y por unos US$ 0,05. Con `--veces N`, un caso aprueba solo si pasa las N veces. Los 25 valores esperados se recalcularon con SQL escrito a mano y coinciden.

**Resultado:** 17 de 17 casos de trabajo y 4 de 4 de reserva. Con 10 corridas por caso: 170 de 170 y 39 de 40 ([test 6](../trazas/consistencia.md)).

`correr_todo.py` corre todo el enunciado con un comando: 20 preguntas, 5 conversaciones y 3 informes (28 casos), en 182 s y por US$ 0,14 ([traza](../trazas/corrida_completa.md)). Los informes se califican aparte con `chequeos_informes.py`, que verifica que cada uno diga lo que tiene que decir (6 chequeos por informe, 18 en total). Con el diseño actual, en 6 corridas: **95 de 108 (88 %)** ([comparación](../trazas/comparacion_informes.md)). Varía entre corridas: el 23-11 una pasó 18 de 18 (sus PDF y trazas están en [`informes/`](informes/)) y otra 14 de 18.

## Tests de robustez

El evaluador mide los casos del enunciado. Los tests miden lo que el enunciado no prueba. Cada uno se vuelve a correr con un comando y deja su traza en `trazas/`.

| # | Test | Qué pregunta | Resultado | Traza |
|---|---|---|---|---|
| 1 | Ingesta simulada | ¿Aguanta un mes de datos nuevos, con hechos reales y errores de carga plantados? | La verificación bloquea el día duplicado y marca el presupuesto ×10; el agente resuelve 4 de 4 sobre los datos nuevos (sucursal y producto nuevos incluidos) | [ingesta_simulada](../trazas/ingesta_simulada.md) |
| 1b | Año simulado | ¿Responde sobre un año con eventos que nunca vio (cierres, categoría nueva, cambios de precio)? | **10 de 10** | [agente_anio](../trazas/agente_anio.md) |
| 1c | Detección de errores | ¿Cuántos errores de carga plantados al azar detecta `verificar_base.py`? | **420 de 420** de los que tienen control, en 30 bases; de los que no tienen control propio, entre 0 y 30 de 30 según el tipo | [deteccion](../trazas/deteccion.md), [sensibilidad](../trazas/sensibilidad.md) |
| 2 | Lenguaje | ¿La misma pregunta dicha de 4 maneras da el mismo número? | **84 de 84** (81 de 84 antes del control de la decisión 95) | [lenguaje](../trazas/lenguaje.md) |
| 3 | Fechas | Año fiscal, «el mes pasado», bordes, rangos, fuera de la base | **42 de 42** | [fechas](../trazas/fechas.md) |
| 4 | No inventar | Preguntas que la base no puede responder | **26 de 36**: nunca inventa el dato; las 10 fallas agregan una cifra «de referencia» de otra cosa | [no_inventar](../trazas/no_inventar.md) |
| 5 | Ataques | Inyección, borrar o modificar datos, leer archivos | **14 de 14** frenados por las capas de código, 14 de 14 por el agente; base intacta | [ataques](../trazas/ataques.md) |
| 6 | Consistencia (pass^k) | ¿Acierta siempre o solo a veces? 10 corridas por caso | **170 de 170** de trabajo (pass^10 = 100 %); reserva 39 de 40 (pass^10 = 75 %) | [consistencia](../trazas/consistencia.md) |
| 7 | Conversación | ¿Qué arrastra de un turno al siguiente y qué suelta? | **69 de 72** turnos; falla siempre «¿Y un año antes?» | [conversacion](../trazas/conversacion.md) |
| 8 | La puerta | ¿Manda cada pregunta al camino correcto? | **192 de 192** caminos; tipo exacto 96 % | [matriz_puerta](../trazas/matriz_puerta.md) |
| 9 | Costo y tiempo | ¿Cuánto cuesta y cuánto tarda, por tipo? | Una pregunta: mediana US$ 0,0009–0,0018 y 7–12 s; un informe, US$ 0,020 y 75 s | [costos](../trazas/costos.md) |

```bash
.venv/bin/python evaluacion/robustez/ingesta_simulada.py [--agente]   # 1
.venv/bin/python evaluacion/robustez/agente_anio.py                   # 1b (el año, con evaluacion/robustez/anio_simulado.py)
.venv/bin/python evaluacion/robustez/deteccion.py [N]                 # 1c (y evaluacion/robustez/sensibilidad.py)
.venv/bin/python evaluacion/robustez/lenguaje.py [--veces N]          # 2
.venv/bin/python evaluacion/robustez/fechas.py [--veces N]            # 3
.venv/bin/python evaluacion/robustez/no_inventar.py [--veces N]       # 4
.venv/bin/python evaluacion/robustez/ataques.py [--veces N]           # 5
.venv/bin/python evaluacion/robustez/consistencia.py [--veces N]      # 6
.venv/bin/python evaluacion/robustez/conversacion.py [--veces N]      # 7
.venv/bin/python evaluacion/robustez/matriz_puerta.py [--veces N]     # 8
.venv/bin/python evaluacion/robustez/costos.py [desde]                # 9, de los registros, sin modelo
```

## Costos

Medidos con `registro.py` desde el 21-11 (el diseño actual), con el caché del prefijo (decisión 72); detalle en [costos](../trazas/costos.md):

| Qué | US$ | Tiempo |
|---|---|---|
| Una pregunta suelta (mediana según el tipo) | 0,0009–0,0018 | 7–12 s |
| Un turno de conversación (mediana) | 0,0011 | 9 s |
| Un diagnóstico (mediana) | 0,0108 | 47 s |
| Un informe (mediana) | 0,0199 | 75 s |
| El evaluador (21 casos) | ~0,05 | ~90 s |
| Todo el enunciado (`correr_todo.py`, 28 casos) | 0,14 | 182 s |
| Un año de informes programados (69 informes) | ~1,37 | |

## Límites conocidos

1. **Agrega cifras «de referencia» que nadie pidió.** Cuando el dato no existe, lo dice, pero a veces suma un número de otra cosa: el margen bruto cuando se pidió la ganancia neta, o la tasa de faltantes cuando se pidió la venta perdida (tests 4 y 6). No es un número falso, pero un lector apurado podría tomarlo como la respuesta.
2. **En una conversación, se ancla al primer período.** «¿Y un año antes?», dicho después de cambiar de mes, vuelve al mes de la primera pregunta (test 7, 3 de 3 veces).
3. **Los casos los escribió el mismo autor, sobre una base simulada.** No hubo usuarios reales con preguntas que no se anticiparon.
4. **El chequeo mira las consultas, no el texto.** Si la consulta es correcta pero el texto destaca otra cifra, el turno aprueba igual.
5. **Muestras chicas.** La mayoría de los tests tiene 3 corridas y la reserva tiene 4 casos: alcanza para ver patrones sistemáticos, no para estimar fallas raras.
6. **Los informes son lo menos medido.** Se califican con 18 chequeos de contenido, y la redacción se juzga leyendo.

## Mejoras propuestas

No se implementaron a propósito: cambiar el sistema invalidaría las mediciones de arriba. Cada mejora ya tiene el test que diría si funcionó.

| Límite | Mejora | Cómo se mediría |
|---|---|---|
| 1 | Separar en la salida estructurada el `valor` del `contexto`: el código controla que el texto principal solo lleve cifras de la medida pedida, y el resto va aparte y rotulado. Es el camino de las decisiones 97 y 116, generalizado. | Test 4 hacia 36 de 36, sin bajar el evaluador |
| 2 | Que el código lleve el estado de la conversación (filtros y período vigentes) y resuelva las referencias relativas contra el último período nombrado, o las declare como supuesto | Test 7 y conversaciones nuevas de 4 a 5 turnos |
| 3 | Un piloto con un usuario real; preguntas escritas por otra persona; una segunda base | Qué parte de las preguntas reales responde, rechaza o erra |
| 4 | Controlar que el primer número del texto sea el esperado, y un juez LLM validado contra calificación humana para lo que el código no puede juzgar | Acuerdo con la calificación humana |
| 5 | Reserva de unos 20 casos, 10 corridas por test e intervalos de confianza | Intervalos que no se superpongan entre versiones |
| 6 | Más pedidos de informe y una evaluación a ciegas hecha por personas | Chequeos de contenido y preferencia a ciegas |
