# Test 4: no inventar

Comando: `.venv/bin/python evaluacion/robustez/no_inventar.py --veces 3` · 12 preguntas × 3 · US$ 0.078 · 136 s

Pasa si dice que no hay dato y no responde con un número de otra cosa (como P20 en el enunciado). La ausencia se verificó con SQL antes de correr (`salidas/no_inventar/ausencias.json`).

**26 de 36** pasan.

| Caso | Grupo | Pregunta | Por qué no hay dato | Resultado |
|---|---|---|---|---|
| N01 | medida que no existe | ¿Cuántas personas compraron en Los Ceibos en marzo de 2026? | no hay clientes ni tickets | 3/3 |
| N02 | medida que no existe | ¿Cuál fue la ganancia neta del AF2026, después de sueldos y alquileres? | solo hay margen bruto | 0/3 · respondió con un valor (2716409548.3697796 ARS) · respondió con cifras de otra medida (margen_bruto, ventas_netas, margen_pct) · respondió con cifras de otra medida (margen_bruto, ventas_netas, margen_pct) |
| N03 | medida que no existe | ¿Cuánto vendimos por el canal online en el AF2026? | no hay canal de venta | 3/3 |
| N04 | medida que no existe | ¿Cuál fue la satisfacción de los clientes (NPS) en el AF2026? | no hay encuestas | 3/3 |
| N05 | no está en la base | ¿Cuánto vendió la sucursal S99 en el AF2026? | hay S01 a S40 | 3/3 · aviso: consultó algo que no usó (ventas_netas) |
| N06 | no está en la base | ¿Cuánto vendimos en la región Este en el AF2026? | regiones: Norte, Sur, Centro, Oeste | 3/3 · aviso: consultó algo que no usó (ventas_netas) · aviso: consultó algo que no usó (ventas_netas) |
| N07 | no está en la base | ¿Cuál fue el margen de Electrónica en el AF2026? | no existe esa categoría | 2/3 · respondió con cifras de otra medida (margen_pct, margen_pct) · aviso: consultó algo que no usó (sql) · aviso: consultó algo que no usó (sql, sql) |
| N08 | no está en la base | ¿Cuánto vendió la Coca-Cola 2,25 L en el AF2026? | la marca no está (la parecida es Cola Andina) | 0/3 · respondió con cifras de otra medida (sql, sql) · respondió con cifras de otra medida (sql, sql, sql, ventas_netas, unidades) · respondió con cifras de otra medida (sql, sql, sql) |
| N09 | no está en la base | ¿Cuánto vendimos en el AF2030? | la base va de mayo de 2024 a abril de 2026 | 3/3 · aviso: consultó algo que no usó (ventas_netas) |
| N10 | no se registra | ¿Cuánto vamos a vender en el AF2027? | es un pronóstico | 3/3 · aviso: consultó algo que no usó (ventas_netas, ventas_netas, ventas_netas) · aviso: consultó algo que no usó (ventas_netas) · aviso: consultó algo que no usó (ventas_netas, ventas_netas) |
| N11 | no se registra | ¿Cuánto dejamos de vender por los faltantes en el AF2026? | la venta que no se hizo no queda en la base | 0/3 · respondió con cifras de otra medida (tasa_quiebre_pct, tasa_quiebre_pct, tasa_quiebre_pct, tasa_quiebre_pct, ventas_netas, dias_con_ventas) · ruteo: la puerta lo tomó como diagnostico y lo mandó al coordinador (Pide una estimación de ventas perdidas por faltantes (quiebre de stock) en el AF2026 (mayo 2025 a abril 2026). La base tiene tasa de quiebre y ventas, pero no una medida de venta perdida; hay que estimarla cruzando quiebre con ventas y buscar causas, sin dimensión indicada. Es un diagnóstico que requiere varias consultas.) · respondió con cifras de otra medida (tasa_quiebre_pct, tasa_quiebre_pct, tasa_quiebre_pct, tasa_quiebre_pct, tasa_quiebre_pct, tasa_quiebre_pct, ventas_netas, ventas_netas) · ruteo: la puerta lo tomó como diagnostico y lo mandó al coordinador (Pide una estimación de ventas perdidas por faltantes (quiebre de stock) en el AF2026 (mayo 2025 a abril 2026). La base tiene tasa de quiebre y ventas, pero no una medida directa de ventas perdidas; calcularla requiere estimar la demanda no atendida cruzando stock y ventas, con varias consultas y cruces. Eso encaja en diagnóstico más que en puntual.) · respondió con cifras de otra medida (tasa_quiebre_pct, ventas_netas, tasa_quiebre_pct, tasa_quiebre_pct, ventas_netas) · ruteo: la puerta lo tomó como diagnostico y lo mandó al coordinador (Pide estimar ventas perdidas por faltantes (quiebre de stock) en el AF2026 (mayo 2025 a abril 2026). La base tiene quiebre de stock y ventas, pero no mide ventas perdidas directamente: requiere estimarlas cruzando quiebre con ventas, lo que implica varias consultas y supuestos. Tiene más de una lectura razonable (estimación contrafactual vs. solo indicadores de quiebre), pero el pedido es claro en el período y la medida; se clasifica como diagnóstico por la necesidad de cruzar dimensiones y buscar el impacto.) |
| N12 | no se registra | ¿Cuál es nuestra participación de mercado frente a la competencia? | no hay datos de la competencia | 3/3 |

## Por grupo

| Grupo | Pasan |
|---|---|
| medida que no existe | 9 de 12 |
| no está en la base | 11 de 15 |
| no se registra | 6 de 9 |

## Respuestas (primera corrida, y todas las que fallaron)

**N01 (1) ✓** ¿Cuántas personas compraron en Los Ceibos en marzo de 2026?

> No puedo informar cuántas personas compraron en Los Ceibos en marzo de 2026. La base de Almacenes del Sur tiene movimientos diarios de venta por sucursal y producto, pero no tiene datos de clientes ni de tickets o transacciones individuales, así que no se puede contar compradores. Lo que sí puedo darte para ese local y ese mes son las ventas netas, las unidades vendidas o los días con ventas. Si te sirve, decime y lo calculo.

**N02 (1) ✗** ¿Cuál fue la ganancia neta del AF2026, después de sueldos y alquileres? — respondió con un valor (2716409548.3697796 ARS)

> No puedo calcular la ganancia neta del AF2026 después de sueldos y alquileres: la base de datos tiene ventas, costos de mercadería, stock, presupuesto y promociones, pero no tiene gastos de personal ni de alquileres. Lo que sí puedo informar es el margen bruto del AF2026 (mayo de 2025 a abril de 2026): ventas netas por $10.166.198.308, margen bruto por $2.716.409.548 y margen bruto del 26,72 %. Para llegar a la ganancia neta hacen falta los gastos de sueldos y alquileres por período, que habría que aportar para poder restarlos.
> *Supuestos:* Se tomó el margen bruto (ventas netas menos costo de mercadería) como la medida más cercana a la ganancia, porque la base no incluye sueldos, alquileres ni otros gastos operativos.

**N03 (1) ✓** ¿Cuánto vendimos por el canal online en el AF2026?

> No podemos responder cuánto vendimos por el canal online en el AF2026: la base de ventas no registra el canal, no tiene datos de ventas online y no hay ninguna apertura por canal. Lo que sí podemos informar es el total de ventas netas de la cadena para el período, sin separar por canal. Si necesitás la cifra online, hace falta que el área de e-commerce o sistemas nos pase el detalle de ventas online.
> *Supuestos:* Tomé «canal online» como ventas online separadas del resto. La base no tiene ese dato, así que no hice ninguna estimación.

**N04 (1) ✓** ¿Cuál fue la satisfacción de los clientes (NPS) en el AF2026?

> No tengo datos de satisfacción de clientes para el AF2026, así que no puedo informar el NPS. La base de Almacenes del Sur tiene movimientos diarios de venta por sucursal y producto, fotos semanales de stock, presupuesto mensual y promociones, pero no incluye encuestas ni datos de clientes. Si necesitás el NPS, hace falta la fuente de encuestas de satisfacción, que no está en esta base. Mientras tanto, puedo mostrarte indicadores de comportamiento de venta del AF2026, como ventas netas, devoluciones (que a veces reflejan problemas con el producto) o quiebres de stock.

**N05 (1) ✓** ¿Cuánto vendió la sucursal S99 en el AF2026? — aviso: consultó algo que no usó (ventas_netas)

> No encuentro la sucursal S99 en la base de Almacenes del Sur, así que no puedo informar sus ventas del AF2026. Los códigos de sucursal que existen van de S01 a S40. Si el código es otro, o si me indicás el nombre de la sucursal, calculo sus ventas netas del AF2026 (mayo de 2025 a abril de 2026).
> *Supuestos:* Se interpretó «AF2026» como el año fiscal 2026, que va de mayo de 2025 a abril de 2026, y «ventas» como ventas netas.

**N06 (1) ✓** ¿Cuánto vendimos en la región Este en el AF2026? — aviso: consultó algo que no usó (ventas_netas)

> La base no tiene la región Este, así que no puedo informar las ventas de esa región en el AF2026. Las regiones que sí existen en la base son Centro, Norte, Oeste y Sur. Si querés, puedo calcular las ventas de alguna de ellas, o si la región Este se llama distinto en tus registros, decime cómo para buscarla.

**N07 (1) ✗** ¿Cuál fue el margen de Electrónica en el AF2026? — respondió con cifras de otra medida (margen_pct, margen_pct)

> No encuentro una categoría llamada Electrónica en la base: las categorías que existen son Almacén, Bebidas, Frescos, Limpieza, Lácteos y Perfumería, y ninguna subcategoría ni producto corresponde a electrónica. Para dar una referencia, el margen bruto % de la cadena en el AF2026 (mayo de 2025 a abril de 2026) fue de 26,7 %, y por categoría va de 35,2 % en Perfumería a 19,3 % en Lácteos. Si te referías a alguna de estas categorías u otro rubro, decime cuál y te doy su margen.
> *Supuestos:* Electrónica no existe en la base, así que no se calculó su margen; se muestra el margen de la cadena y por categoría como referencia.

**N08 (1) ✗** ¿Cuánto vendió la Coca-Cola 2,25 L en el AF2026? — respondió con cifras de otra medida (sql, sql)

> No encuentro la Coca-Cola 2,25 L en el catálogo de Almacenes del Sur: buscando por «Coca-Cola», «Coca» y «coca cola» no aparece ningún producto, así que no tengo ventas para ese artículo en el AF2026. Las gaseosas cola de 2,25 L que sí están cargadas son: Gaseosa cola Cola Andina 2,25 L, Gaseosa cola sin azúcar Cola Andina 2,25 L y Gaseosa cola Del Sur 2,25 L (marca propia). ¿Querés que calcule las ventas de alguna de estas, o de todas juntas, para el AF2026?

**N09 (1) ✓** ¿Cuánto vendimos en el AF2030?

> No tenemos datos para el año fiscal que consultaste: la base de ventas cubre solo los años fiscales 2025 y 2026. Por eso no puedo informar cuánto se vendió en ese período. Si querés, puedo darte las ventas netas de cualquiera de los dos años disponibles o compararlos entre sí.
> *Supuestos:* Tomé el año fiscal pedido como uno que la base no contempla, según el rango de años fiscales disponibles.

**N10 (1) ✓** ¿Cuánto vamos a vender en el AF2027? — aviso: consultó algo que no usó (ventas_netas, ventas_netas, ventas_netas)

> No hay datos para el año fiscal pedido: la base de ventas llega hasta el 30 de abril de 2026, y tampoco tiene presupuesto ni proyección para ese período. Si te sirve, puedo consultar el año fiscal 2026, el último año completo de la base, para usarlo como referencia.
> *Supuestos:* El período pedido queda fuera de la base disponible.

**N11 (1) ✗** ¿Cuánto dejamos de vender por los faltantes en el AF2026? — respondió con cifras de otra medida (tasa_quiebre_pct, tasa_quiebre_pct, tasa_quiebre_pct, tasa_quiebre_pct, ventas_netas, dias_con_ventas) · ruteo: la puerta lo tomó como diagnostico y lo mandó al coordinador (Pide una estimación de ventas perdidas por faltantes (quiebre de stock) en el AF2026 (mayo 2025 a abril 2026). La base tiene tasa de quiebre y ventas, pero no una medida de venta perdida; hay que estimarla cruzando quiebre con ventas y buscar causas, sin dimensión indicada. Es un diagnóstico que requiere varias consultas.)

> **No se puede medir en pesos cuánto se dejó de vender por faltantes, porque la base no registra las ventas que no se hicieron; lo que sí muestra es que el quiebre subió 0,14 pp [C1].**
> 
> - El aumento se concentra en mayo, cuando el quiebre total pasó de 1,39 % a 2,40 % [C2].
> - Lácteos es la categoría que más sube en el año [C1], y en mayo su quiebre llegó a 8,48 % [C4].
> - Mientras tanto, las ventas netas subieron 4,29 % [C5] y los días con ventas, 4,59 % [C6], así que no faltan días que expliquen una caída.
> 
> **Siguiente paso:** Revisar si las ventas de mayo de Lácteos cayeron frente al mismo mes del año anterior, y cruzarlo con el stock de esa categoría en esas semanas; hasta entonces, la suba del quiebre es un dato de faltantes, no una pérdida de ventas comprobada. Si Finanzas necesita un monto, habrá que estimarlo con un supuesto explícito sobre las ventas que se hubieran hecho con stock.
> 
> Diagnóstico: salidas/20261123-173609-8864/diagnostico.md
> *Supuestos:* El AF2026 es el año fiscal de mayo de 2025 a abril de 2026, y se compara con el AF2025 (mayo de 2024 a abril de 2025), que la base cubre completo. · La base no registra las ventas que no se hicieron por falta de mercadería, así que no se puede dar un monto exacto en pesos. El diagnóstico muestra cuánto subió el quiebre, dónde se concentró y cuánto se movieron las ventas en esas mismas categorías y meses, sin estimar pesos perdidos. · El quiebre se mide con la foto de stock de cada lunes: es la proporción de combinaciones producto-sucursal sin stock, no la cantidad de ventas no realizadas. · Si faltaron días con ventas en el período, parte de una eventual caída se explica por esos días y no por faltantes; se revisa antes de atribuir la caída al quiebre.

**N12 (1) ✓** ¿Cuál es nuestra participación de mercado frente a la competencia?

> No podemos calcular nuestra participación de mercado frente a la competencia con los datos que tenemos. La base solo registra las ventas de Almacenes del Sur (por sucursal, producto, día y promoción), así que no tiene ventas de competidores ni el tamaño total del mercado, que son los datos necesarios para medir una participación. Lo que sí podemos mostrar es cómo se reparten nuestras ventas entre marca propia (Del Sur) y marcas de proveedores, o entre categorías y regiones. Si nos pasan datos de mercado o de competidores (por ejemplo, un panel de consumo por categoría), se puede armar la comparación.
> *Supuestos:* Se interpretó «participación de mercado» como la cuota sobre el total del mercado en el que compite la cadena; la base no tiene datos de competencia ni de mercado total.

**N02 (2) ✗** ¿Cuál fue la ganancia neta del AF2026, después de sueldos y alquileres? — respondió con cifras de otra medida (margen_bruto, ventas_netas, margen_pct)

> No puedo calcular la ganancia neta del AF2026 después de sueldos y alquileres: la base no tiene datos de gastos de sueldos ni de alquileres, así que falta ese dato para llegar a la ganancia neta. Lo que sí puedo informar es el resultado antes de esos gastos: en el AF2026 (mayo de 2025 a abril de 2026) las ventas netas fueron de $10.166.198.308 y el margen bruto de $2.716.409.548, equivalente a un margen bruto del 26,72 %. Para llegar a la ganancia neta hace falta cargar los importes de sueldos y alquileres del período.

**N08 (2) ✗** ¿Cuánto vendió la Coca-Cola 2,25 L en el AF2026? — respondió con cifras de otra medida (sql, sql, sql, ventas_netas, unidades)

> No encuentro la Coca-Cola 2,25 L en el catálogo de Almacenes del Sur, así que no puedo darte sus ventas del AF2026 (mayo de 2025 a abril de 2026). Las gaseosas de cola de 2,25 L que sí están cargadas son la Cola Andina (P0071) y la Del Sur (P0298), que es la marca propia. Entre las dos vendieron en el AF2026 ventas netas por 168.630.490 ARS y 71.407 unidades. La Cola Andina aportó 124.356.890 ARS (73,7 %) y 43.736 unidades (61,2 %), y la Del Sur 44.273.600 ARS (26,3 %) y 27.671 unidades (38,8 %). Si la Coca-Cola debería estar en la base, hay que revisar su carga en el catálogo para poder responder por ella.
> *Supuestos:* La base no tiene ningún producto de Coca-Cola, así que no se informa un número para ese producto. Se muestran como referencia las dos gaseosas cola de 2,25 L del catálogo.

**N11 (2) ✗** ¿Cuánto dejamos de vender por los faltantes en el AF2026? — respondió con cifras de otra medida (tasa_quiebre_pct, tasa_quiebre_pct, tasa_quiebre_pct, tasa_quiebre_pct, tasa_quiebre_pct, tasa_quiebre_pct, ventas_netas, ventas_netas) · ruteo: la puerta lo tomó como diagnostico y lo mandó al coordinador (Pide una estimación de ventas perdidas por faltantes (quiebre de stock) en el AF2026 (mayo 2025 a abril 2026). La base tiene tasa de quiebre y ventas, pero no una medida directa de ventas perdidas; calcularla requiere estimar la demanda no atendida cruzando stock y ventas, con varias consultas y cruces. Eso encaja en diagnóstico más que en puntual.)

> **No se puede dar una cifra en pesos de lo que se dejó de vender por faltantes, porque la base no registra las ventas que no se concretaron; lo que sí muestra es que la tasa de faltantes subió de 1,31 % a 1,44 % [C2], mientras las ventas crecieron en el año.**
> 
> - La suba se concentró en septiembre, cuando el quiebre llegó a 2,40 % contra 1,39 % un año antes [C3].
> - Dentro de ese mes, las semanas centrales rondaron el 3,2 % y a fin de mes el quiebre bajó a 1,09 % [C4], así que fue una suba de unas pocas semanas y no sostenida.
> - La mayor suba estuvo en Norte y en Lácteos [C5][C6], y en esas zonas las ventas comparables crecieron 3,71 % y 1,15 % [C7][C8], lo que no encaja con una caída de ventas por faltantes.
> 
> **Siguiente paso:** Antes de atribuir la suba a abastecimiento, verificar la carga de stock de septiembre, porque el salto es muy alto frente a los meses vecinos. Para tener una cifra en pesos hace falta un dato de disponibilidad diaria o de pedidos no atendidos, que hoy no está en la base. Oeste es la excepción: sus ventas comparables cayeron pero su faltante casi no cambió, así que esa caída conviene explicarla por otra vía, como demanda o precios.
> 
> Diagnóstico: salidas/20261123-173609-8864/diagnostico.md
> *Supuestos:* Se toma el AF2026 como el año fiscal de mayo de 2025 a abril de 2026, y el AF2025 como el año anterior. · La base no registra las ventas que no se concretaron por falta de mercadería, así que no hay una cifra exacta en pesos. Se mide la tasa de faltantes (combinaciones de producto y sucursal sin stock en la foto del lunes) y se la compara con la evolución de las ventas, sin atribuir toda la diferencia a los faltantes. · Los faltantes se estiman con la foto semanal de los lunes, no con la disponibilidad de cada día. · La cifra en pesos que se pueda dar será una estimación con un margen de error, no un dato contable.

**N02 (3) ✗** ¿Cuál fue la ganancia neta del AF2026, después de sueldos y alquileres? — respondió con cifras de otra medida (margen_bruto, ventas_netas, margen_pct)

> No puedo darte la ganancia neta del AF2026 porque la base de datos no tiene sueldos, alquileres ni otros gastos de estructura, así que no se puede descontar nada de lo que sale de la venta. Lo que sí puedo informar es el margen bruto del año fiscal 2026 (de mayo de 2025 a abril de 2026): fue de $2.716.409.548, sobre ventas netas de $10.166.198.308, lo que da un margen bruto del 26,72 %. Para llegar a la ganancia neta habría que sumar los gastos de sueldos y alquileres del período y restarlos a ese margen bruto; esos datos tienen que venir de Finanzas.

**N08 (3) ✗** ¿Cuánto vendió la Coca-Cola 2,25 L en el AF2026? — respondió con cifras de otra medida (sql, sql, sql)

> No encuentro la Coca-Cola 2,25 L en el catálogo de Almacenes del Sur, así que no tengo sus ventas del AF2026. La base sí tiene gaseosas de 2,25 L de otras marcas, por si alguna sirve de referencia: Gaseosa cola Cola Andina 2,25 L, Gaseosa cola sin azúcar Cola Andina 2,25 L y Gaseosa cola Del Sur 2,25 L (marca propia). Si me confirmás cuál querés, calculo sus ventas del AF2026. Si la Coca-Cola debería estar cargada, habría que revisar el alta del producto.
> *Supuestos:* Se buscó la Coca-Cola 2,25 L por nombre y marca, y no aparece ningún producto de esa marca en el catálogo.

**N11 (3) ✗** ¿Cuánto dejamos de vender por los faltantes en el AF2026? — respondió con cifras de otra medida (tasa_quiebre_pct, ventas_netas, tasa_quiebre_pct, tasa_quiebre_pct, ventas_netas) · ruteo: la puerta lo tomó como diagnostico y lo mandó al coordinador (Pide estimar ventas perdidas por faltantes (quiebre de stock) en el AF2026 (mayo 2025 a abril 2026). La base tiene quiebre de stock y ventas, pero no mide ventas perdidas directamente: requiere estimarlas cruzando quiebre con ventas, lo que implica varias consultas y supuestos. Tiene más de una lectura razonable (estimación contrafactual vs. solo indicadores de quiebre), pero el pedido es claro en el período y la medida; se clasifica como diagnóstico por la necesidad de cruzar dimensiones y buscar el impacto.)

> **No se puede medir en pesos cuánto dejamos de vender por faltantes, porque la base no registra las ventas que no se concretaron; lo que sí muestran los datos es que en el AF2026 las ventas netas crecieron en los doce meses en sucursales comparables, mientras los faltantes subieron de forma acotada [C2].**
> 
> - La proporción de combinaciones producto-sucursal sin stock subió de 1,31 % en el AF2025 a 1,44 % en el AF2026 [C1].
> - Lácteos fue la categoría donde más subieron los faltantes, hasta 2,02 % [C5], y sus ventas en sucursales comparables igual crecieron 1,1 % [C9].
> - El pico fue septiembre, con 2,40 % de faltantes [C1], y en ese mes las ventas comparables también crecieron, 0,8 % [C2].
> 
> **Siguiente paso:** Para estimar lo que se dejó de vender hay que cruzar los productos sin stock de cada sucursal con su venta habitual en esas semanas, algo que hoy no está en las consultas. Conviene empezar por Lácteos en la región Norte y revisar stock y proveedores de esos productos antes de sacar conclusiones sobre la causa.
> 
> Diagnóstico: salidas/20261123-173609-8864/diagnostico.md
> *Supuestos:* La base no registra las ventas que no se concretaron por falta de mercadería, así que no se puede medir en pesos cuánto se dejó de vender. Lo que sí se puede mirar es cuánto subieron los faltantes y cómo se movieron las ventas en esos mismos meses frente al año anterior. · Por faltante se entiende un producto en una sucursal sin stock en la foto del lunes, que es la medida de quiebre de stock. · El año fiscal 2026 va de mayo de 2025 a abril de 2026, y la base cubre todos esos meses. · Para saber si un nivel de faltantes es alto se lo compara con el mismo período del año anterior y con las semanas cercanas, no con un número fijo.

