"""Lo que frena el código sin depender del modelo: las tools de cada agente, un único SELECT, y una base de solo lectura
sin acceso a archivos. Las mismas capas que mide el test de ataques (evaluacion/pruebas/ataques.py), sin el modelo."""
import duckdb
import pytest

from hooks import antes_de_tool, tools_de
from procesador_capa_semantica import consultar_sql


def test_cada_agente_ve_solo_sus_tools():
    tools = [{"name": n} for n in ("ver_modelo", "calcular", "buscar_producto", "consultar_sql", "borrar_todo")]
    assert [t["name"] for t in tools_de("analista", tools)] == ["ver_modelo", "calcular", "buscar_producto", "consultar_sql"]
    assert tools_de("coordinador", tools) == []


def test_el_coordinador_no_consulta_la_base():
    assert "no está permitida" in antes_de_tool("coordinador", "calcular", {})
    assert antes_de_tool("analista", "calcular", {}) is None


@pytest.mark.parametrize("sql, motivo", [
    ("DELETE FROM ventas", "solo acepta SELECT"),
    ("UPDATE ventas SET unidades = 0", "solo acepta SELECT"),
    ("DROP TABLE ventas", "solo acepta SELECT"),
    ("SELECT 1; DROP TABLE ventas", "una sola sentencia"),
])
def test_consultar_sql_acepta_solo_un_select(sql, motivo):
    assert motivo in antes_de_tool("analista", "consultar_sql", {"sql": sql})


def test_un_select_pasa():
    assert antes_de_tool("analista", "consultar_sql", {"sql": "SELECT COUNT(*) FROM sucursales"}) is None
    assert consultar_sql("SELECT COUNT(*) AS n FROM sucursales")["filas"] == [{"n": 40}]


def test_la_base_es_de_solo_lectura_aunque_falle_el_hook():
    with pytest.raises(duckdb.Error, match="read"):
        consultar_sql("DELETE FROM ventas")


def test_no_puede_escribir_ni_leer_archivos(tmp_path):
    with pytest.raises(duckdb.Error, match="disabled"):
        consultar_sql(f"COPY sucursales TO '{tmp_path / 'robado.csv'}'")
    assert not (tmp_path / "robado.csv").exists()
    with pytest.raises(duckdb.Error, match="disabled"):
        consultar_sql("SELECT * FROM read_text('/etc/passwd')")
