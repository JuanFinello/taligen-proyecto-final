# Test 9: costo y tiempo por tipo de pregunta (decisión 100)

Comando: `.venv/bin/python evaluacion/pruebas/costos.py 2026-11-18` · 5.154 llamadas al modelo desde el 2026-11-18, agrupadas en 810 casos con tipo · sin modelo

| Tipo | Casos | Costo mediano | p95 | Máximo | Tiempo mediano | p95 | Máximo | Llamadas (mediana) |
|---|---|---|---|---|---|---|---|---|
| puntual | 295 | US$ 0,0010 | US$ 0,0018 | US$ 0,0027 | 7 s | 11 s | 16 s | 4 |
| comparativa | 157 | US$ 0,0017 | US$ 0,0028 | US$ 0,0036 | 10 s | 16 s | 21 s | 4 |
| ranking | 95 | US$ 0,0016 | US$ 0,0025 | US$ 0,0029 | 11 s | 14 s | 18 s | 5 |
| ambigua | 60 | US$ 0,0013 | US$ 0,0016 | US$ 0,0017 | 7 s | 9 s | 10 s | 4 |
| sin_dato | 95 | US$ 0,0009 | US$ 0,0016 | US$ 0,0021 | 6 s | 10 s | 14 s | 3 |
| conversación (turno) | 80 | US$ 0,0012 | US$ 0,0020 | US$ 0,0022 | 7 s | 11 s | 12 s | 4 |
| diagnostico | 13 | US$ 0,0116 | US$ 0,0155 | US$ 0,0176 | 52 s | 60 s | 65 s | 13 |
| informe | 15 | US$ 0,0134 | US$ 0,0156 | US$ 0,0160 | 54 s | 63 s | 64 s | 14 |

## El caché del prefijo (decisión 72)

| Quién | Llamadas | Tokens de entrada leídos del caché | Costo |
|---|---|---|---|
| clasificador | 1.453 | 94,9 % | US$ 0,2444 |
| analista | 3.583 | 84,1 % | US$ 1,47 |
| coordinador | 118 | 62,2 % | US$ 0,2185 |

## Qué costaría usarlo

- Una pregunta típica (mediana de puntual, comparativa y ranking): **US$ 0,0016**.
- 50 preguntas por día hábil, un año (250 días): **US$ 20,42**.
- Un diagnóstico: US$ 0,0116; un informe: US$ 0,0134.
- Los informes programados de un año (52 semanales, 12 mensuales, 4 trimestrales y 1 anual, decisión 65): **US$ 0,9222** con la mediana de un informe.

## Lectura (escrita después de correr)

- **Una pregunta cuesta alrededor de una décima de centavo de dólar** (mediana US$ 0,0010 a 0,0017 según el tipo) y tarda 6 a 11 s; el peor caso (p95) no llega al doble. Un diagnóstico o un informe cuestan unas 10 veces más (US$ 0,012 a 0,013) y tardan ~55 s, porque son 13 o 14 llamadas: el coordinador planifica, los analistas consultan en paralelo y el coordinador redacta.
- **La distribución es angosta:** el máximo de una pregunta (US$ 0,0036) es poco más del doble de su mediana. No hay preguntas que se disparen: el tope de vueltas (decisión 26) y el de correcciones (decisión 49) lo acotan.
- **El caché** (decisión 72) sirve casi todo el prompt del clasificador (95 %) y del analista (84 %); el del coordinador, menos (62 %), porque cada pedido trae su propio plan y los hallazgos.
- **Usarlo en serio es barato:** 50 preguntas por día hábil durante un año, unos US$ 20; los informes programados de un año, menos de US$ 1.
- **Límite:** son las corridas de los tests y del evaluador (desde el 18-11, con el diseño actual), de a 5 en paralelo; no hay tráfico real. Las conversaciones se cuentan por turno.
