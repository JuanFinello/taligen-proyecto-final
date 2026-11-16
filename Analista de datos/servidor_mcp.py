"""Servidor MCP: expone ver_modelo(), calcular(), buscar_producto() y consultar_sql() del procesador como tools,
y el glosario como prompt."""
import os

# El procesador abre Data/... con rutas relativas: el servidor corre siempre desde esta carpeta
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

import procesador_capa_semantica as procesador

servidor = MCPServer("almacenes-del-sur")


@servidor.prompt()
def glosario() -> str:
    """El criterio del negocio (glosario.md): va entero en el prompt de sistema de cada agente."""
    with open("Data/capa_semantica/glosario.md") as f:
        return f.read()


@servidor.tool()
def ver_modelo() -> dict:
    """Medidas disponibles (id, nombre, sinónimos, unidad), dimensiones con sus valores válidos.
    Llamar primero, antes de calcular."""
    return procesador.ver_modelo()


@servidor.tool()
def calcular(medida: str, filtros: dict | None = None, agrupar_por: list[str] | None = None,
             orden: str = "desc", limite: int | None = None, comparar_con: dict | None = None,
             comparables: bool = False) -> dict:
    """Calcula una medida y devuelve el valor junto con el SQL que lo produjo.
    medida: id de ver_modelo. filtros: {dimension: valor o lista de valores}, por ejemplo {"anio_fiscal": 2026} o {"anio": 2026, "mes": [1, 2, 3]}.
    agrupar_por: lista de dimensiones; devuelve una fila por grupo, ordenada por valor (orden "desc" o "asc", limite opcional).
    En medidas aditivas trae también el total (con los mismos filtros) y participacion_pct de cada grupo sobre ese total.
    comparar_con: solo los filtros que cambian en el período anterior, por ejemplo {"anio_fiscal": 2025}.
    comparables=True: compara solo sucursales abiertas al inicio del período anterior (requiere comparar_con).
    comparar_con + agrupar_por: por grupo, valor actual, anterior y variación; en medidas aditivas también la diferencia
    y aporte_pct (qué parte de la suba o caída total explica cada grupo), ordenado por diferencia ("asc" para las caídas)."""
    # Si falla, el agente recibe el motivo (no un error genérico) para poder corregir la llamada
    try:
        return procesador.calcular(medida, filtros, agrupar_por, orden, limite, comparar_con, comparables)
    except Exception as error:
        raise ToolError(f"{type(error).__name__}: {error}") from error


@servidor.tool()
def buscar_producto(texto: str) -> dict:
    """Busca productos por nombre o marca y devuelve su código (sku), nombre, marca, categoría y precio de lista.
    Usarla para pasar de un nombre («gaseosa cola Del Sur 2,25 L») al sku. En calcular, el sku va en la dimensión
    producto: filtros={"producto": "P0298"} (no existe la dimensión sku).
    Busca las palabras sueltas, sin importar mayúsculas ni tildes: conviene pocas palabras («cola Del Sur»).
    Hay nombres repetidos en varios sku que solo difieren en precio: si hay más de uno, aclararlo o sumar todos."""
    try:
        return procesador.buscar_producto(texto)
    except Exception as error:
        raise ToolError(f"{type(error).__name__}: {error}") from error


@servidor.tool()
def consultar_sql(sql: str) -> dict:
    """SQL de solo lectura (DuckDB) para lo que las medidas no cubren, como listados: qué promociones estuvieron
    vigentes en un mes, qué productos tiene un proveedor. NO usarla para ventas, margen, unidades, presupuesto ni
    ninguna medida de ver_modelo: esas se piden con calcular. Tablas y columnas: tablas_para_sql de ver_modelo.
    Devuelve hasta 100 filas (truncado=True si hay más) y queda registrada con su SQL."""
    try:
        return procesador.consultar_sql(sql)
    except Exception as error:
        raise ToolError(f"{type(error).__name__}: {error}") from error


if __name__ == "__main__":
    servidor.run()  # stdio
