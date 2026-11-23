"""Los controles en código que corren al terminar cada respuesta: ningún número sin respaldo, los filtros que nombra
la pregunta, y los períodos o valores que la base no tiene."""
import pytest

from controles import grupos_sin_filtro, numeros_del_texto, periodo_fuera_de_la_base, sin_respaldo, valores_de, valores_que_no_estan
from procesador_capa_semantica import calcular


@pytest.fixture(scope="module")
def respaldo():
    """Los valores de una consulta real: el margen bruto de Perfumería en el AF2026 (460.758.207)."""
    return valores_de([calcular("margen_bruto", {"categoria": "Perfumería", "anio_fiscal": 2026})])


def test_numeros_del_texto_en_formato_argentino():
    numeros = [texto for _, _, texto in numeros_del_texto("Vendió $1.309.106.714 y el margen fue 35,2 %")]
    assert numeros == ["1.309.106.714", "35,2"]


def test_un_numero_que_sale_de_la_consulta_pasa(respaldo):
    assert sin_respaldo("El margen bruto fue de $460.758.207.", respaldo) == []


def test_un_numero_redondeado_o_en_millones_pasa(respaldo):
    assert sin_respaldo("Fue de 460,8 millones.", respaldo) == []


def test_un_numero_inventado_se_frena(respaldo):
    assert sin_respaldo("El margen bruto fue de $512.000.000.", respaldo) == ["512.000.000"]


def test_una_categoria_nombrada_tiene_que_estar_en_alguna_consulta():
    pregunta = "¿Cuánto vendió Perfumería en el AF2026?"
    sin_filtro = [{"tool": "calcular", "argumentos": {"medida": "ventas_netas", "filtros": {"anio_fiscal": 2026}}}]
    con_filtro = [{"tool": "calcular", "argumentos": {"medida": "ventas_netas",
                                                      "filtros": {"anio_fiscal": 2026, "categoria": "Perfumería"}}}]
    assert grupos_sin_filtro(pregunta, sin_filtro) == [("categoria", "Perfumería")]
    assert grupos_sin_filtro(pregunta, con_filtro) == []


def test_un_periodo_fuera_de_la_base_se_detecta():
    assert periodo_fuera_de_la_base("¿Cuánto vendimos en marzo de 2027?")
    assert periodo_fuera_de_la_base("¿Cuánto vendimos en marzo de 2026?") == []


def test_un_valor_que_no_existe_se_detecta():
    assert valores_que_no_estan("¿Cuánto vendió la sucursal S77 en el AF2026?") == [("sucursal", "S77")]
    assert valores_que_no_estan("¿Cuánto vendió la sucursal S02 en el AF2026?") == []
