# Traza: hooks que frenan (semana 4)

Los hooks están en `hooks.py` (decisiones 58 a 60). Cuando un hook frena, el loop no corre la tool (o no deja salir la
respuesta) y le pasa el motivo a Haiku como el error de una tool, para que corrija.

## 1. Al terminar: una respuesta con números que no salen de ninguna consulta

Caso real del evaluador, corrida `20261117-090736-e647`, P11: «¿Qué 3 proveedores dejaron más margen bruto en pesos en
el AF2026?». Del registro (`registros/llamadas.jsonl`):

| Vuelta | Qué hizo Haiku | Qué hizo el hook |
|---|---|---|
| 1 | `ver_modelo` | – |
| 2 | `calcular` margen_bruto por proveedor, los 3 primeros | después: registró la consulta con su SQL |
| 3 | `calcular` margen_bruto por proveedor, todos | después: registró la consulta con su SQL |
| 4 | Respuesta final con «1.053.080.243» (la suma de los tres) y «38,8 %» (su participación sumada) | **al terminar: frenó.** Esos números no salen de ninguna consulta: Haiku los sumó por su cuenta |
| 5 | Respuesta corregida, sin la suma | dejó salir la respuesta; el registro se validó y se guardó |

Lo que recibió Haiku en la vuelta 4, como error (`pedido_de_correccion` en `hooks.py`):

> Estos números de tu respuesta no salen de ninguna consulta: 38,8, 1.053.080.243, 1.053.080.243, 38,8. No hagas
> cuentas propias (restas, sumas, promedios). Reescribí la respuesta completa: sacá esos números o reemplazalos por
> uno que salga de una consulta; si necesitás un dato que no consultaste, consultalo con calcular.

La respuesta que quedó registrada (`registros/respuestas.jsonl`):

> Los 3 proveedores que dejaron más margen bruto en pesos en el AF2026 (mayo 2025 a abril 2026) fueron: 1) PR11
> Química Hogar S.A., con $418.990.504 (15,42% del margen bruto total); 2) PR15 Frigorífico Las Lomas S.A., con
> $325.977.889 (12,00%); 3) PR07 Bodegas Valle Alto S.A., con $308.111.850 (11,34%). El margen bruto total de la
> cadena en el AF2026 fue de $2.716.409.548.

En todo el registro (hasta el 17-11-2026), este hook frenó 261 respuestas de 239 preguntas, todas de analistas. En 234
Haiku corrigió; en 5 siguió con números sin respaldo después de las dos correcciones permitidas (`MAX_CORRECCIONES`), y
la respuesta salió marcada con `numeros_sin_respaldo`. En las corridas recientes del evaluador frena entre 4 y 7 veces
cada 17 casos.

## 2. Antes de cada tool: solo un SELECT, y solo las tools de cada agente

En las corridas reales Haiku nunca pidió otra cosa que un SELECT, así que este hook no frenó ninguna llamada real. Lo
que devuelve ante cada caso (salida de `antes_de_tool`, corrida el 17-11-2026):

| Agente | Tool y argumentos | Motivo que recibiría Haiku |
|---|---|---|
| analista | `consultar_sql` `DROP TABLE ventas` | consultar_sql solo acepta SELECT; esta sentencia es DROP. |
| analista | `consultar_sql` `SELECT 1; DELETE FROM ventas` | consultar_sql acepta una sola sentencia y llegaron 2. |
| analista | `consultar_sql` `COPY ventas TO '/tmp/x.csv'` | consultar_sql solo acepta SELECT; esta sentencia es COPY. |
| analista | `consultar_sql` `SELECT promocion_id FROM promociones LIMIT 1` | – (corre) |
| coordinador | `calcular` | La tool calcular no está permitida para el coordinador. |

El tipo de sentencia lo dice el parser de DuckDB, no una búsqueda en el texto. Además, la base se abre en solo lectura
y sin acceso a archivos (decisión 34): si una sentencia pasara el hook, igual no podría escribir.

Para reproducirlo:

```bash
.venv/bin/python -c "from hooks import antes_de_tool; print(antes_de_tool('analista', 'consultar_sql', {'sql': 'DROP TABLE ventas'}))"
```
