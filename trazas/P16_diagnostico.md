# ¿Qué pasó con la gaseosa cola de marca propia en diciembre de 2025?

**Las ventas de la gaseosa cola Del Sur cayeron 46,6 % frente a diciembre de 2024 [C2], y los datos explican solo una parte de esa caída.**

- El precio se mantuvo en $1.600 y el margen % subió 0,13 pp frente a diciembre de 2024 [C8], así que la caída no viene de precio ni de margen.
- Tampoco se trata de cierres de sucursales: en las mismas sucursales la caída fue de 48,0 % [C10].
- Faltaron días con venta (866 contra 1.026) [C12], y en la subcategoría hubo una promoción de otra marca durante todo el mes [C13].

**Siguiente paso:** Confirmar con el área comercial y de operaciones por qué faltaron días de venta en diciembre, y revisar si la promoción de la otra marca le quitó ventas a la cola Del Sur; con eso se separa cuánto es demanda real y cuánto es un problema de carga o de operación.

## Supuestos

- Diciembre de 2025 se toma como mes calendario completo, que cae en el tercer trimestre fiscal del año fiscal 2026.
- La gaseosa cola de marca propia son los productos de la marca Del Sur de la subcategoría de gaseosas cuya descripción corresponde a cola; si hay varias presentaciones, se suman.
- Como referencia se usan diciembre de 2024 (mismo mes del año anterior) y noviembre de 2025 (mes previo).

## Consultas citadas (SQL en consultas.sql)

- [C2] Ventas netas. Ventas brutas menos descuentos y devoluciones. De qué: producto P0298. Cuándo: diciembre de 2025. Contra: diciembre de 2024, con todas las sucursales.
- [C8] Efecto precio y efecto costo del margen %. Separa la variación del margen % entre dos períodos en efecto precio y efecto costo, en pp (suman la variación). De qué: producto P0298. Cuándo: diciembre de 2025. Contra: diciembre de 2024, con todas las sucursales.
- [C10] Ventas netas. Ventas brutas menos descuentos y devoluciones. De qué: producto P0298. Cuándo: diciembre de 2025. Contra: diciembre de 2024, solo con las sucursales que estaban abiertas en los dos períodos (comparables).
- [C12] Días con ventas. Cuántos días vendió cada sucursal, sumados (una sucursal en un día cuenta 1). De qué: producto P0298. Cuándo: diciembre de 2025. Contra: diciembre de 2024, con todas las sucursales.
