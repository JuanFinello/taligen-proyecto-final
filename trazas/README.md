# Trazas

Cada traza muestra una corrida real: la pregunta, el camino que tomó, las consultas con su SQL y su resultado, y la respuesta. Todas se pueden volver a generar con el comando que figura al principio de cada una.

## Casos del enunciado

| Traza | Qué muestra |
|---|---|
| [corrida_completa](corrida_completa.md) | las 20 preguntas, 5 conversaciones y 3 informes con un comando, con su costo y su tiempo |
| [C1](C1.md) | una conversación de 3 turnos, turno por turno |
| [P17](P17.md) | una pregunta ambigua («el último trimestre»): las dos lecturas |
| [P20](P20.md) | una pregunta sin dato en la base: dice que no está |
| [P16](P16.md) · [P16_diagnostico](P16_diagnostico.md) | un diagnóstico: el recorrido entero y el texto final |
| [I1](I1.md) | un informe: plan, analistas, redacción, controles y PDF |
| [I_semanal_programado](I_semanal_programado.md) | un informe generado solo por el temporizador ([PDF](I_semanal_programado.pdf), [SQL](I_semanal_programado.sql)) |
| [hooks](hooks.md) | los hooks frenando: una respuesta con números sin respaldo y una consulta que no es un SELECT |
| [apartadas](apartadas.md) | las cinco preguntas apartadas, abiertas: qué falló y por qué |
| [comparacion_informes](comparacion_informes.md) | los informes medidos, calificados con código, versión por versión del diseño |

Los PDF de los tres pedidos de informe, generados con la versión actual del diseño, están en [`docs/informes/`](../docs/informes/).

## Tests de robustez

| Traza | Test |
|---|---|
| [ingesta_simulada](ingesta_simulada.md) | 1 · un mes de datos nuevos con errores de carga plantados |
| [anio_simulado](anio_simulado.md) · [agente_anio](agente_anio.md) | 1 · un año simulado con eventos nuevos, y el agente sobre ese año |
| [deteccion](deteccion.md) · [sensibilidad](sensibilidad.md) | 1 · cuántos errores de carga detecta la verificación, y el más chico que ve |
| [lenguaje](lenguaje.md) | 2 · la misma pregunta dicha de 4 maneras |
| [fechas](fechas.md) | 3 · fechas difíciles |
| [no_inventar](no_inventar.md) | 4 · preguntas que la base no puede responder |
| [ataques](ataques.md) | 5 · ataques, por capas |
| [consistencia](consistencia.md) | 6 · cada caso 10 veces (pass^k) |
| [conversacion](conversacion.md) | 7 · qué arrastra y qué suelta en una conversación |
| [matriz_puerta](matriz_puerta.md) | 8 · matriz de confusión de la puerta |
| [costos](costos.md) | 9 · costo y tiempo por tipo |

El método y el resumen de los resultados están en [`docs/evaluacion.md`](../docs/evaluacion.md).
