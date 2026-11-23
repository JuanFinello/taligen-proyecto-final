"""Las preguntas sugeridas después de cada respuesta (decisiones 86 y 121): salen del resultado, sin modelo, y con memoria
de la conversación no se repiten."""
import pytest

from procesador_capa_semantica import calcular
from sugerir import Memoria, sugerencias


def respuesta(*consultas):
    """Una respuesta del agente con estas consultas de calcular, como las arma el loop."""
    return {"ruta": "agente", "tipo": "ranking",
            "consultas": [{"tool": "calcular", "argumentos": a, "resultado": calcular(**a)} for a in consultas]}


def ranking_de_productos(**filtros):
    """Lo que hizo el agente en la conversación del 23-11: ventas netas y unidades por producto, top 5."""
    return respuesta({"medida": "ventas_netas", "filtros": filtros, "agrupar_por": ["producto"], "limite": 5},
                     {"medida": "unidades", "filtros": filtros, "agrupar_por": ["producto"], "limite": 5})


CONVERSACION = [("que producto se vende mas en el norte", {"region": "Norte"}),
                ("y en el sur ?", {"region": "Sur"}),
                ("y cual es el producto que mas se vende en todas las sucursales", {})]


@pytest.fixture(scope="module")
def turnos():
    memoria = Memoria()
    return [sugerencias(ranking_de_productos(**filtros), memoria, pregunta) for pregunta, filtros in CONVERSACION]


def test_con_memoria_ninguna_sugerencia_se_repite(turnos):
    todas = [s for turno in turnos for s in turno]
    assert len(todas) == len(set(todas))
    assert all(turno for turno in turnos)


def test_propone_otra_region_que_no_se_pregunto(turnos):
    assert "¿Y en el Centro?" in turnos[0] + turnos[1]
    assert not any("¿Y en el Sur?" in s or "¿Y en el Norte?" in s for turno in turnos[1:] for s in turno)


def test_parte_de_la_consulta_principal_no_de_la_de_apoyo(turnos):
    """La primera consulta (ventas netas) es la que responde; antes se usaba la última (unidades)."""
    assert not any("las unidades de P0185" in s for turno in turnos for s in turno)


def test_redaccion(turnos):
    for s in (s for turno in turnos for s in turno):
        assert s.startswith("¿") and s.endswith("?")
        assert "todo el período" not in s and "None" not in s and "{" not in s


def test_sin_memoria_sale_como_antes():
    assert len(sugerencias(ranking_de_productos(region="Norte"))) == 3


@pytest.mark.parametrize("consulta", [
    {"medida": "ventas_netas", "filtros": {"anio_fiscal": 2025}},
    {"medida": "margen_pct", "filtros": {"categoria": "Almacén", "anio_fiscal": 2026, "trimestre_fiscal": 2},
     "comparar_con": {"anio_fiscal": 2025}},
    {"medida": "ventas_netas", "filtros": {"categoria": "Bebidas", "anio_fiscal": 2026, "trimestre_fiscal": 3},
     "comparar_con": {"anio_fiscal": 2025}},
    {"medida": "ventas_netas", "filtros": {"anio_fiscal": 2026}, "agrupar_por": ["sucursal"], "limite": 5},
    {"medida": "unidades", "filtros": {"categoria": "Lácteos", "anio": 2026, "mes": 3}},
])
def test_respuestas_tipicas_tienen_sugerencias_bien_escritas(consulta):
    salida = sugerencias(respuesta(consulta), Memoria(), "pregunta")
    assert 1 <= len(salida) <= 3
    assert all(s.startswith("¿") and s.endswith("?") and "None" not in s for s in salida)


def test_dice_del_y_no_de_el():
    caida = {"medida": "margen_pct", "filtros": {"categoria": "Almacén", "anio_fiscal": 2026, "trimestre_fiscal": 2},
             "comparar_con": {"anio_fiscal": 2025}}
    salida = sugerencias(respuesta(caida), Memoria(), "pregunta")
    assert not any(" de el " in s for s in salida)
    assert any("del margen" in s for s in salida)


def test_no_sugiere_precio_o_costo_si_ya_se_separo():
    """La captura del README: la respuesta ya separó efecto precio y efecto costo, y la sugerencia lo volvía a preguntar."""
    filtros = {"categoria": "Almacén", "anio_fiscal": 2026, "trimestre_fiscal": 2}
    margen = {"medida": "margen_pct", "filtros": filtros, "comparar_con": {"anio_fiscal": 2025}}
    efectos = {"medida": "efectos_margen", "filtros": filtros, "comparar_con": {"anio_fiscal": 2025}}
    assert any("precio o por costo" in s for s in sugerencias(respuesta(margen), Memoria(), "pregunta"))
    assert not any("precio o por costo" in s for s in sugerencias(respuesta(margen, efectos), Memoria(), "pregunta"))
