# Sensibilidad de `verificar_base.py` (decisión 91)

Comando: `.venv/bin/python evaluacion/robustez/sensibilidad.py` · 1 s, sin modelo · base real (AF2025 y AF2026)

La curva de detección es exacta sobre todos los lugares normales de la base: un error ×k en un lugar con cociente natural r contra sus vecinos se detecta si k·r ≥ 3.

## 1. El error más chico que detecta, con el umbral de cada control

Umbrales de `verificar_base.py`: presupuesto de una celda (mes, sucursal, categoría): 1,5, costo de un producto en un mes: 1,5, importes de un día de una sucursal: 3 (decisión 92). El agente sigue avisando desde 3 en el presupuesto (decisión 84).

| Error | Lugares | ×1,25 | ×1,5 | ×2 | ×3 | ×5 | ×10 |
|---|---|---|---|---|---|---|---|
| presupuesto de una celda (mes, sucursal, categoría) | 5.588 | 2 % | 50 % | 100 % | 100 % | 100 % | 100 % |
| costo de un producto en un mes | 7.392 | 0 % | 50 % | 100 % | 100 % | 100 % | 100 % |
| importes de un día de una sucursal | 28.377 | 0 % | <1 % | 1 % | 50 % | 100 % | 100 % |
| unidades de una fila (control: 50 veces la mediana de su producto) | 199.214 (muestra) | 0 % | 0 % | 0 % | 0 % | <1 % | <1 % |

Con más tamaños para las unidades: ×10: <1 % · ×25: 11 % · ×50: 34 % · ×100: 85 % · ×1000: 100 %

## 2. Un día cargado a medias

Si falta una parte de un día (por ejemplo, una categoría), las ventas del día bajan esa fracción. El control lo ve si el día queda por debajo de 1/3 de sus vecinos.

| Falta | 10 % | 25 % | 50 % | 67 % | 75 % | 90 % | 100 % |
|---|---|---|---|---|---|---|---|
| Detectado | <1 % | <1 % | 1 % | 54 % | 98 % | 100 % | 100 % (días sin ventas) |

## 3. ¿Por qué 3 y no otro umbral? Detección contra falsas alarmas

Falsas alarmas: lugares de la base real, sin errores, que el control marcaría con ese umbral. Detección: de un error ×2.

| Umbral | presupuesto de una celda (mes, sucursal, categoría): falsas alarmas · detecta ×2 | costo de un producto en un mes: falsas alarmas · detecta ×2 | importes de un día de una sucursal: falsas alarmas · detecta ×2 |
|---|---|---|---|
| 1,5 | 12 (<1 %) · 100 % | 0 (0 %) · 100 % | 450 (2 %) · 97 % |
| 2 | 10 (<1 %) · 50 % | 0 (0 %) · 50 % | 29 (<1 %) · 50 % |
| 2,5 | 10 (<1 %) · 1 % | 0 (0 %) · 0 % | 3 (<1 %) · 5 % |
| 3 | 10 (<1 %) · <1 % | 0 (0 %) · 0 % | 0 (0 %) · 1 % |
| 4 | 10 (<1 %) · 0 % | 0 (0 %) · 0 % | 0 (0 %) · <1 % |

(Con el umbral actual, las falsas alarmas incluyen los lugares que la base ya marca: las 10 celdas del error de carga de enero de 2026 en el presupuesto, que no son falsas.)

## 4. Confirmación con inyecciones reales

Presupuesto ×2 y ×3 en 20 celdas sorteadas de una copia, corriendo la función del control: **20 de 20** coinciden con la cuenta.

| Error | Celda | r natural | Predicho | Marcado por el control |
|---|---|---|---|---|
| ×2 | S01 Almacén 2024-08 | 1,039 | no | no |
| ×2 | S36 Almacén 2026-01 | 0,941 | no | no |
| ×2 | S08 Frescos 2024-11 | 0,895 | no | no |
| ×2 | S36 Almacén 2026-04 | 1,019 | no | no |
| ×2 | S31 Bebidas 2024-10 | 0,96 | no | no |
| ×2 | S17 Bebidas 2025-07 | 1,032 | no | no |
| ×2 | S14 Limpieza 2025-09 | 0,933 | no | no |
| ×2 | S28 Perfumería 2025-08 | 1,013 | no | no |
| ×2 | S23 Frescos 2025-09 | 1,054 | no | no |
| ×2 | S13 Frescos 2025-09 | 1,001 | no | no |
| ×3 | S07 Perfumería 2025-02 | 0,939 | no | no |
| ×3 | S29 Lácteos 2025-01 | 1,089 | sí | sí |
| ×3 | S29 Limpieza 2024-11 | 0,969 | no | no |
| ×3 | S13 Frescos 2026-02 | 1,008 | sí | sí |
| ×3 | S12 Perfumería 2025-06 | 0,974 | no | no |
| ×3 | S17 Limpieza 2025-10 | 1,082 | sí | sí |
| ×3 | S32 Bebidas 2024-12 | 1,034 | sí | sí |
| ×3 | S30 Lácteos 2024-12 | 0,888 | no | no |
| ×3 | S34 Lácteos 2025-06 | 1,093 | sí | sí |
| ×3 | S10 Perfumería 2024-08 | 0,923 | no | no |

## Lectura (escrita después de correr; actualizada con la decisión 92)

- **Los controles por salto tienen un borde claro:** con el umbral de 3, un error ×2 no se ve nunca, un ×3 la mitad de las veces (está justo en el umbral, y el cociente natural ronda 1) y un ×5 siempre.
- **Un día cargado a medias** se ve recién cuando falta más de dos tercios (67 %: 54 %; 75 %: 98 %). Una categoría sola, alrededor de una sexta parte, no se ve. Un control propio no sirve: la base real ya tiene 57 días en que una categoría que suele ser el 15 % del día vende cero.
- **Dos familias de controles:** los de **consistencia** (una identidad que se cumple o no, como bruto = unidades × precio de lista) ven cualquier tamaño; los **estadísticos** (un salto contra los vecinos) necesitan un umbral. El presupuesto, el costo y una carga parcial dependen solo del umbral.
- **Un solo umbral no le sirve a todos** (tabla 3): en el presupuesto y el costo, bajarlo a 1,5 agrega 2 avisos en dos años (los dos hechos reales: la apertura de S39 y el quiebre de Lácteos de S08) y ninguno en el costo; en las ventas de un día, 1,5 daría 450 alarmas. **Decisión 92:** la verificación usa 1,5 en el presupuesto y el costo, y 3 en las ventas de un día; el agente sigue con 3. Con eso, un error ×2 en el presupuesto o el costo pasa de no verse nunca a verse siempre (tabla 1).
- **La cuenta coincide con el control real:** 20 de 20 inyecciones.
