# Test 9: costo y tiempo por tipo de pregunta (decisión 100)

Comando: `.venv/bin/python evaluacion/robustez/costos.py 2026-11-21` · 3.443 llamadas al modelo desde el 2026-11-21, agrupadas en 332 casos con tipo · sin modelo

| Tipo | Casos | Costo mediano | p95 | Máximo | Tiempo mediano | p95 | Máximo | Llamadas (mediana) |
|---|---|---|---|---|---|---|---|---|
| puntual | 79 | US$ 0,0010 | US$ 0,0019 | US$ 0,0027 | 9 s | 14 s | 18 s | 4 |
| comparativa | 60 | US$ 0,0015 | US$ 0,0029 | US$ 0,0032 | 11 s | 17 s | 19 s | 4 |
| ranking | 45 | US$ 0,0018 | US$ 0,0023 | US$ 0,0025 | 12 s | 16 s | 17 s | 5 |
| ambigua | 30 | US$ 0,0013 | US$ 0,0018 | US$ 0,0021 | 10 s | 15 s | 18 s | 4 |
| sin_dato | 30 | US$ 0,0009 | US$ 0,0011 | US$ 0,0012 | 7 s | 8 s | 9 s | 3 |
| conversación (turno) | 77 | US$ 0,0011 | US$ 0,0024 | US$ 0,0028 | 9 s | 16 s | 21 s | 4 |
| diagnostico | 4 | US$ 0,0108 | US$ 0,0138 | US$ 0,0138 | 47 s | 63 s | 63 s | 13 |
| informe | 7 | US$ 0,0199 | US$ 0,0236 | US$ 0,0236 | 75 s | 105 s | 105 s | 21 |

## El caché del prefijo (decisión 72)

| Quién | Llamadas | Tokens de entrada leídos del caché | Costo |
|---|---|---|---|
| clasificador | 817 | 94,6 % | US$ 0,1436 |
| analista | 2.574 | 86,7 % | US$ 1,00 |
| coordinador | 44 | 58,7 % | US$ 0,0982 |

## Qué costaría usarlo

- Una pregunta típica (mediana de puntual, comparativa y ranking): **US$ 0,0015**.
- 50 preguntas por día hábil, un año (250 días): **US$ 19,07**.
- Un diagnóstico: US$ 0,0108; un informe: US$ 0,0199.
- Los informes programados de un año (52 semanales, 12 mensuales, 4 trimestrales y 1 anual, decisión 65): **US$ 1,37** con la mediana de un informe.

## Lectura (escrita después de correr)

- **Desde el 21-11, el diseño actual.** La versión anterior de esta traza medía desde el 18-11, antes del editor y de la profundización en código de los informes (decisiones 105 y 113), que les sumaron llamadas: un informe pasó de 14 llamadas y US$ 0,0134 a 21 llamadas y US$ 0,0199. Las preguntas casi no cambiaron.
- **Una pregunta cuesta alrededor de una décima de centavo de dólar** (mediana US$ 0,0009 a 0,0018 según el tipo) y tarda 7 a 12 s; el peor caso (p95) ronda el doble. Un diagnóstico cuesta unas 10 veces más (US$ 0,011, 47 s) y un informe unas 15 (US$ 0,020, 75 s).
- **La distribución es angosta:** el máximo de una pregunta (US$ 0,0032) es poco más del doble de su mediana. El tope de vueltas (decisión 26) y el de correcciones (decisión 49) lo acotan.
- **El caché** (decisión 72) sirve casi todo el prompt del clasificador (95 %) y del analista (87 %); el del coordinador, menos (59 %), porque cada pedido trae su propio plan y los hallazgos.
- **Usarlo en serio es barato:** 50 preguntas por día hábil durante un año, unos US$ 19; los informes programados de un año, unos US$ 1,40.
- **Límite:** son las corridas de los tests y del evaluador, de a 5 en paralelo; no hay tráfico real. Hay pocos diagnósticos (4) e informes (7) desde el 21-11. Las conversaciones se cuentan por turno.
