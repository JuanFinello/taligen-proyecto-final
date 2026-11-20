# Comparación de versiones del diseño en los informes medidos (I1, I2, I3)

Lo arma `chequeos_informes.py --guardar` (decisión 110) con los chequeos de `Data/preguntas/esperados_informes.yaml`: cada celda dice en cuántas corridas el informe cumplió. Sin modelo: lee los `informe.json` de `salidas/completa-*`. Las corridas cortadas no cuentan.

| Versión | Huella | Decisión | Corridas | Qué es |
|---|---|---|---|---|
| Ejemplos inventados | `bd8da1` | 107 | 3 | los 3 ejemplos inventados de la decisión 105; título hasta 15 palabras, oraciones hasta 25 |
| Semana + marca propia + lecciones | `d52c32` | 108 | 6 | 2 informes aprobados completos y 5 lecciones del margen; título hasta 22, oraciones hasta 30 (la versión en uso) |
| Más una región del año simulado | `445f82` | 109 | 7 | la 108 más el informe del Norte del AF2027 con nombres que no existen (no entró) |
| Solo semana + lecciones | `da7bd6` | 111 | 6 | la 108 sin el ejemplo de marca propia; su lección, en una línea («un margen % más alto no alcanza para decir que algo conviene») |

| Caso | Chequeo | Ejemplos inventados | Semana + marca propia + lecciones | Más una región del año simulado | Solo semana + lecciones |
|---|---|---|---|---|---|
| I1 | dice cuánto bajó el margen % | 2 de 3 | 5 de 6 | 6 de 7 | 6 de 6 |
| I1 | cuenta que en pesos subió | 3 de 3 | 5 de 6 | 7 de 7 | 6 de 6 |
| I1 | nombra la categoría (Almacén) | 3 de 3 | 6 de 6 | 7 de 7 | 6 de 6 |
| I1 | dice que es por costo | 3 de 3 | 6 de 6 | 7 de 7 | 6 de 6 |
| I1 | llega al proveedor (Molinos del Plata) | 0 de 3 | 3 de 6 | 2 de 7 | 0 de 6 |
| I1 | título sin citas [Cn] | 3 de 3 | 6 de 6 | 7 de 7 | 6 de 6 |
| I2 | dice el desvío total | 3 de 3 | 6 de 6 | 4 de 6 | 4 de 6 |
| I2 | avisa del presupuesto sospechoso | 2 de 3 | 6 de 6 | 6 de 6 | 6 de 6 |
| I2 | lo dice en el título | 3 de 3 | 6 de 6 | 6 de 6 | 6 de 6 |
| I2 | nombra dónde está (Perfumería) | 3 de 3 | 6 de 6 | 6 de 6 | 6 de 6 |
| I2 | dice el desvío sin ese presupuesto | 1 de 3 | 6 de 6 | 6 de 6 | 5 de 6 |
| I2 | título sin citas [Cn] | 2 de 3 | 6 de 6 | 6 de 6 | 5 de 6 |
| I3 | dice que el total creció | 1 de 3 | 5 de 6 | 3 de 6 | 5 de 6 |
| I3 | dice que las comparables cayeron | 2 de 3 | 4 de 6 | 4 de 6 | 6 de 6 |
| I3 | lo atribuye a las aperturas | 3 de 3 | 4 de 6 | 5 de 6 | 6 de 6 |
| I3 | dice desde cuándo | 0 de 3 | 0 de 6 | 1 de 6 | 0 de 6 |
| I3 | no se va al margen en el título | 3 de 3 | 4 de 6 | 4 de 6 | 5 de 6 |
| I3 | título sin citas [Cn] | 3 de 3 | 4 de 6 | 4 de 6 | 6 de 6 |
| | **Total** | **40 de 54** (74 %) | **88 de 108** (81 %) | **91 de 114** (80 %) | **90 de 108** (83 %) |

Corridas usadas:

- Ejemplos inventados: completa-20261120-155830-f41c, completa-20261120-160126-130d, completa-20261120-160411-f4fa
- Semana + marca propia + lecciones: completa-20261120-161314-c3c0, completa-20261120-161617-86a9, completa-20261120-161856-9c47, completa-20261120-170509-9d06, completa-20261120-170809-26a1, completa-20261120-171047-10e3
- Más una región del año simulado: completa-20261120-163835-49fa, completa-20261120-164155-2fd8, completa-20261120-164415-82f0, completa-20261120-165141-330e, completa-20261120-165408-a422, completa-20261120-165902-91e0, completa-20261120-170147-3ec8
- Solo semana + lecciones: completa-20261120-172238-b75a, completa-20261120-172533-b77c, completa-20261120-172819-57f8, completa-20261120-173050-42d8, completa-20261120-173305-ae4a, completa-20261120-173538-d665
