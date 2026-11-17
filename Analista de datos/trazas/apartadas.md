# Traza: las preguntas apartadas (semana 5)

El enunciado pide abrir las apartadas y contar **qué falló y por qué**. P09, P12, P14, P18 y P19 no se usaron para
ajustar nada desde la decisión 5. Se abrieron el 17-11-2026 (decisión 79), en este orden, sin tocar el agente entre
paso y paso.

## 1. La puerta, con los tipos declarados antes de verlas

`.venv/bin/python puerta.py --medir P09 P12 P14 P18 P19`, tres veces:

| | Tipo declarado (dec. 5) | Lo que dio la puerta | Camino |
|---|---|---|---|
| P09 | comparativa | **puntual**, las tres veces | agente ✓ |
| P12 | ranking | ranking | agente ✓ |
| P14 | diagnóstico | diagnóstico | coordinador ✓ |
| P18 | ambigua | ambigua | agente ✓ |
| P19 | sin dato | sin dato | agente ✓ |

**Qué falló y por qué:** el tipo de P09 («¿Cuál fue el desvío contra presupuesto de la cadena en el T4 del AF2026?»).
Haiku lo lee como el valor de una sola medida (`desvio_presupuesto_pct`), sin comparación entre períodos; la definición
de «comparativa» incluye el presupuesto, pero la de «puntual» también le calza. No tiene consecuencia: los dos tipos van
al agente. No se ajustó.

## 2. Los valores esperados, con SQL escrito a mano y antes de correr el agente

| | Esperado |
|---|---|
| P09 | −5,21 % (ventas $ 2.514.025.456,5 contra presupuesto $ 2.652.332.885,56; el error de carga del presupuesto, en enero, no cae en el T4) |
| P12 | Desodorantes, +19,13 % en unidades (68.899 → 82.076); también la mayor suba absoluta |
| P18 | Limpieza: $ 1.768.156.506 en el calendario 2025 o $ 1.736.332.149,5 en el AF2025 |
| P19 | Sin dato: la base no tiene tickets ni transacciones |
| P14 | Quiebre de stock: Lácteos del Norte −19,9 % contra sep-2024 (las otras regiones crecen); 29,7 % de los registros de stock en 0, contra ~1,5 % en los meses vecinos; sin promociones |

## 3. Cada una, una sola vez

| | Resultado | Costo |
|---|---|---|
| P09, P12, P18, P19 | `evaluador.py`: **4 de 4** | US$ 0,006 las cuatro |
| P14 | por la puerta al coordinador: encontró el quiebre (1,5 % → 29,7 %) | US$ 0,013 |

P14 fue más fino que el chequeo: atribuyó el quiebre a un proveedor, Lácteos La Pradera (60 % de sus registros de stock
en 0; −9,9 M, más que la caída de toda la categoría, −6,2 M). Verificado a mano después: los otros dos proveedores
tienen el quiebre normal (~1,5 %) y Usina Láctea del Oeste crece +3,6 M. Dijo además que los datos muestran la
coincidencia, no la causa comprobada.

## Por qué no falló nada más

Las cinco cubren cosas que el diseño ya resolvía en general, no por pregunta: el desvío lo calcula el código
(decisión 30), «creció más» se resuelve con una comparación agrupada que trae la variación de cada grupo (28), la
ambigua da las dos lecturas o declara la elegida (35, 76), la sin dato no responde con otro indicador (35, 76), y el
diagnóstico tiene una guía de dónde mirar (si caen las ventas, el stock; decisión 7). Ninguna de las cinco necesitó
algo que el diseño no tuviera.

## Después

Quedan como **reserva** (decisión 80): nunca se ajusta nada por una falla de ellas y el evaluador las informa aparte.
