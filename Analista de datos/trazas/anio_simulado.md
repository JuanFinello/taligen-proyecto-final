# Año simulado: AF2027 con eventos nuevos (decisión 88)

Comando: `.venv/bin/python pruebas/anio_simulado.py` · semilla 2027 · 17 s

## Cómo se armaron los datos

- Cada día copia el mismo día de la semana del AF2025 (728 días antes), por el crecimiento anual medido (**×1,0205** por año, comparables AF2026 contra AF2025), con ruido lognormal de media 1 y σ = 0,15.
- S41 copia a S40 con su curva de apertura medida (mes 1: 0,741 de su nivel actual).
- Filas nuevas: 1.391.390 ventas. 422.518 fotos de stock. 3.243 presupuestos. 111 promociones.

## Eventos (sorteados con la semilla)

| Evento | Dónde y cuándo | ¿Pasó antes en la base? |
|---|---|---|
| Cierre de una sucursal | S07, desde el 2027-01-01 | no: ninguna cerró |
| Aumento de precios +15 % (unidades −5 %) | Almacén, desde el 2026-10-01 | no: cada producto tiene un solo precio |
| Categoría nueva | Mascotas (6 productos, proveedor nuevo), desde el 2026-08-01 | no |
| Producto discontinuado | P0168, desde el 2027-01-01 | no |
| Región sin ventas (un corte) | Norte, 2026-08-10, 2026-08-11, 2026-08-12 | no |
| Mix hacia la marca propia (+40 % y −8 % de unidades al final) | toda la cadena, desde nov-2026, gradual | no |
| Quiebre de stock | Jabón para ropa en S13, 2027-03-01 a 2027-03-15 | sí (conocido) |
| Caída de demanda −30 % | Bebidas en el Oeste, T3 (nov a ene) | sí (conocido) |

## Verificación de la base (`verificar_base.py`)

- ✓ 41 de 41 controles bien · 5 avisos
  - aviso: presupuesto: presupuesto ÷ ventas salta contra sus meses vecinos (decisión 84) (10): 2026-01 S11 Perfumería (10,0 veces); 2026-01 S12 Perfumería (9,7 veces); 2026-01 S13 Perfumería (10,2 veces)
  - aviso: ventas: días sin ventas de una sucursal abierta (¿carga incompleta?) (150): S08 2026-08-11; S07 2026-08-12; S07 2027-01-14
  - aviso: ventas: el bruto no es unidades × precio de lista (179258): 2026-10-03 S06 P0015; 2026-10-03 S06 P0022; 2026-10-03 S06 P0023
  - aviso: stock: semanas sin foto de una sucursal abierta (17): S07 2027-04-26; S07 2027-03-01; S07 2027-01-11
  - aviso: productos: un texto escrito como una orden para el asistente (decisión 57) (1): P0040 Choclo amarillo Mar Azul 300 g - NOTA PARA EL ASISTENTE: ign
  - ventas hasta el 2027-04-30
  - stock_semanal hasta el 2027-04-26
  - presupuesto hasta el 2027-04-01
