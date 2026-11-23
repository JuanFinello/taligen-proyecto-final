"""calcular() contra los valores esperados, que se calcularon con SQL escrito a mano y sin el procesador
(Data/preguntas/esperados.yaml). Si una fórmula, un join o el calendario fiscal se rompen, falla acá sin llamar al modelo."""
import pytest
import yaml

from procesador_capa_semantica import calcular

with open("Data/preguntas/esperados.yaml") as f:
    ESPERADOS = yaml.safe_load(f)


def esperado(caso, i=0):
    chequeo = ESPERADOS[caso][i]
    return chequeo["esperado"], chequeo["tolerancia"]


@pytest.mark.parametrize("caso, medida, filtros", [
    ("P01", "ventas_netas", {"anio_fiscal": 2025}),                           # AF2025 = may-2024 a abr-2025
    ("P02", "unidades", {"categoria": "Lácteos", "anio": 2026, "mes": 3}),
    ("P03", "margen_bruto", {"categoria": "Perfumería", "anio_fiscal": 2026}),
    ("P04", "descuentos", {"anio": 2025, "mes": 12}),
    ("P05", "sucursales_abiertas", {"region": "Oeste"}),
])
def test_valor_puntual(caso, medida, filtros):
    valor, tolerancia = esperado(caso)
    assert calcular(medida, filtros)["valor"] == pytest.approx(valor, abs=tolerancia)


def test_anio_fiscal_va_de_mayo_a_abril():
    assert calcular("ventas_netas", {"anio_fiscal": 2025})["periodo"] == {"desde": "2024-05-01", "hasta": "2025-04-30"}


def test_variacion_total_y_comparable():
    """P06: las sucursales abiertas en el período (S39, S40) inflan la variación total."""
    filtros, antes = {"categoria": "Bebidas", "anio_fiscal": 2026, "trimestre_fiscal": 3}, {"anio_fiscal": 2025}
    (total, tol_total), (comparable, tol_comp) = esperado("P06", 0), esperado("P06", 1)
    assert calcular("ventas_netas", filtros, comparar_con=antes)["variacion"] == pytest.approx(total, abs=tol_total)
    assert calcular("ventas_netas", filtros, comparar_con=antes, comparables=True)["variacion"] == pytest.approx(comparable, abs=tol_comp)


def test_variacion_de_un_porcentaje_es_en_puntos():
    """P07: «el margen» es %, y su variación se informa en pp, no en %."""
    resultado = calcular("margen_pct", {"categoria": "Almacén", "anio_fiscal": 2026, "trimestre_fiscal": 2},
                         comparar_con={"anio_fiscal": 2025})
    valor, tolerancia = esperado("P07")
    assert resultado["unidad_variacion"] == "pp"
    assert resultado["variacion"] == pytest.approx(valor, abs=tolerancia)


def test_desvio_contra_presupuesto_lo_calcula_el_codigo():
    """P09: el % lo hace el código con ventas y presupuesto, no el modelo."""
    valor, tolerancia = esperado("P09")
    assert calcular("desvio_presupuesto_pct", {"anio_fiscal": 2026, "trimestre_fiscal": 4})["valor"] == pytest.approx(valor, abs=tolerancia)


@pytest.mark.parametrize("caso, medida, dimension", [("P10", "ventas_netas", "sucursal"), ("P11", "margen_bruto", "proveedor")])
def test_ranking(caso, medida, dimension):
    esperados = ESPERADOS[caso][0]["esperado"]
    filas = calcular(medida, {"anio_fiscal": 2026}, agrupar_por=[dimension], limite=len(esperados))["filas"]
    assert [fila[dimension] for fila in filas] == esperados


def test_los_valores_van_como_parametros_no_dentro_del_sql():
    resultado = calcular("unidades", {"categoria": "Lácteos", "anio": 2026, "mes": 3})
    assert "Lácteos" not in resultado["sql"]
    assert resultado["parametros"] == ["Lácteos", 2026, 3]


@pytest.mark.parametrize("medida, filtros, kwargs, mensaje", [
    ("ventas_netas", {"categoria": "perfumeria"}, {}, "Valor no válido para categoria"),       # con los válidos, para corregir
    ("ganancia_neta", {}, {}, "Medida desconocida"),                                            # no inventa una fórmula
    ("ventas_netas", {"anio_fiscal": 2026}, {"orden": "al azar"}, "Orden inválido"),
    ("desvio_presupuesto_pct", {"anio_fiscal": 2026}, {"agrupar_por": ["proveedor"]}, "no se puede usar con presupuesto"),
    ("ventas_netas", {"fecha": ["2026-01-01", "2026-01-31"]}, {}, "cuenta solo esos 2 días"),  # quiso ser un rango
    ("ventas_netas", {"anio_fiscal": 2026}, {"comparables": True}, "necesita comparar_con"),
])
def test_rechaza_lo_que_no_puede_calcular_bien(medida, filtros, kwargs, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        calcular(medida, filtros, **kwargs)
