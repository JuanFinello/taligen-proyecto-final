# Test 8: matriz de confusión de la puerta (decisión 99)

Comando: `.venv/bin/python pruebas/matriz_puerta.py --veces 3` · 64 preguntas × 3 · US$ 0.031

**Camino correcto (agente o coordinador): 192 de 192 (100.0 %)** · tipo exacto: 185 de 192 (96.4 %)

## La matriz (filas: tipo real · columnas: lo que dio la puerta)

| Real \ Dio | puntual | comparativa | ranking | diagnostico | ambigua | sin_dato | informe | Total | Acierto |
|---|---|---|---|---|---|---|---|---|---|
| **puntual** | **75** | · | · | · | · | · | · | 75 | 100 % |
| **comparativa** | 3 | **33** | · | · | · | · | · | 36 | 92 % |
| **ranking** | · | · | **21** | · | · | · | · | 21 | 100 % |
| **diagnostico** | · | · | · | **12** | · | · | · | 12 | 100 % |
| **ambigua** | 4 | · | · | · | **11** | · | · | 15 | 73 % |
| **sin_dato** | · | · | · | · | · | **24** | · | 24 | 100 % |
| **informe** | · | · | · | · | · | · | **9** | 9 | 100 % |

## Precisión y exhaustividad por tipo

Precisión: de lo que la puerta llamó X, cuánto era X. Exhaustividad: de lo que era X, cuánto llamó X.

| Tipo | Precisión | Exhaustividad | Camino |
|---|---|---|---|
| puntual | 91 % | 100 % | agente |
| comparativa | 100 % | 92 % | agente |
| ranking | 100 % | 100 % | agente |
| diagnostico | 100 % | 100 % | coordinador |
| ambigua | 100 % | 73 % | agente |
| sin_dato | 100 % | 100 % | agente |
| informe | 100 % | 100 % | coordinador |

## Camino equivocado (0)

Ninguno.

## Tipo equivocado dentro del camino correcto

- P09: real comparativa, dio puntual (3 de 3) · «¿Cuál fue el desvío contra presupuesto de la cadena en el T4 del AF2026?»
- fechas F08: real ambigua, dio puntual (3 de 3) · «¿Cuánto vendimos en abril?»
- P18: real ambigua, dio puntual (1 de 3) · «¿Cuánto vendió Limpieza en 2025?»

## Lectura (escrita después de correr)

- **El camino, 192 de 192.** Ninguna pregunta fue al agente equivocado: los diagnósticos y los informes, siempre al coordinador; lo demás, siempre al agente. Es lo que importa (decisión 78): el tipo exacto, dentro del mismo camino, no cambia quién responde.
- **El tipo exacto, 185 de 192 (96 %).** Las 7 confusiones son dentro del camino del agente: P09 (desvío contra presupuesto, comparativa leída como puntual, ya visto en la decisión 79, 3 de 3), «¿Cuánto vendimos en abril?» (ambigua leída como puntual, 3 de 3) y P18 (ambigua leída como puntual, 1 de 3).
- **La ambigua es el tipo con menos exhaustividad (73 %):** la puerta a veces la llama puntual. No tiene consecuencia porque el agente la resuelve igual: en el test 3, «¿Cuánto vendimos en abril?» declaró qué abril usó las 3 veces. La segunda línea cubre a la primera.
- **Un error del test, encontrado en la primera corrida:** se habían incluido las preguntas de los tests 1 y 4, que hablan de las bases simuladas (mayo de 2026, el AF2027). Contra la base real la puerta las llamó sin dato, y tenía razón: lee la cobertura de la base. Se sacaron; la primera corrida queda en `salidas/matriz_puerta/resultado_con_preguntas_de_bases_simuladas.md`.
