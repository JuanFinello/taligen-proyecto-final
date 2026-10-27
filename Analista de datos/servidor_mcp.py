"""Servidor MCP: expone ver_modelo() y calcular() del procesador como tools para el agente."""
import os

# El procesador abre Data/... con rutas relativas: el servidor corre siempre desde esta carpeta
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

import procesador_capa_semantica as procesador

servidor = MCPServer("almacenes-del-sur")


@servidor.tool()
def ver_modelo() -> dict:
    """Medidas disponibles (id, nombre, sinónimos, unidad), dimensiones con sus valores válidos y reglas de negocio.
    Llamar primero, antes de calcular."""
    return procesador.ver_modelo()


@servidor.tool()
def calcular(medida: str, filtros: dict | None = None, agrupar_por: list[str] | None = None,
             orden: str = "desc", limite: int | None = None, comparar_con: dict | None = None,
             comparables: bool = False) -> dict:
    """Calcula una medida y devuelve el valor junto con el SQL que lo produjo.
    medida: id de ver_modelo. filtros: {dimension: valor}, por ejemplo {"anio_fiscal": 2026}.
    agrupar_por: lista de dimensiones; devuelve una fila por grupo, ordenada por valor (orden "desc" o "asc", limite opcional).
    comparar_con: solo los filtros que cambian en el período anterior, por ejemplo {"anio_fiscal": 2025}.
    comparables=True: compara solo sucursales abiertas al inicio del período anterior (requiere comparar_con)."""
    # Si falla, el agente recibe el motivo (no un error genérico) para poder corregir la llamada
    try:
        return procesador.calcular(medida, filtros, agrupar_por, orden, limite, comparar_con, comparables)
    except Exception as error:
        raise ToolError(f"{type(error).__name__}: {error}") from error


if __name__ == "__main__":
    servidor.run()  # stdio
