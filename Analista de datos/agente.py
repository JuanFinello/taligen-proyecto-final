"""Agente mínimo: Haiku responde una pregunta usando las tools del servidor MCP.
Uso: .venv/bin/python agente.py "¿Cuál fue el margen bruto de Perfumería en el AF2026?" """
import asyncio
import json
import sys

import anthropic
from mcp import ClientSession, StdioServerParameters, stdio_client

MODELO = "claude-haiku-5-5"

with open("Data/capa_semantica/glosario.md") as f:
    SISTEMA = ("Sos un analista de datos de Almacenes del Sur. Respondé en español. "
               "Cada número tiene que salir de la tool calcular: no calcules ni inventes números. "
               "Empezá llamando a ver_modelo para conocer las medidas y dimensiones.\n"
               "- Al nombrar sucursales o proveedores, mostrá código y nombre (agrupá por las dos dimensiones).\n"
               "- Si comparás ventas de dos períodos, informá la variación total y la comparable (comparables=True).\n\n"
               + f.read())


async def responder(pregunta):
    # Paso 1: lanzar el servidor MCP y pedirle la lista de tools
    servidor = StdioServerParameters(command=".venv/bin/python", args=["servidor_mcp.py"])
    async with (stdio_client(servidor) as (lectura, escritura), ClientSession(lectura, escritura) as mcp,
                anthropic.AsyncAnthropic() as claude):
        await mcp.initialize()
        tools = [{"name": t.name, "description": t.description, "input_schema": t.input_schema}
                 for t in (await mcp.list_tools()).tools]

        # Paso 2: el loop. Haiku contesta; si pide una tool, la corremos y le devolvemos el resultado
        mensajes = [{"role": "user", "content": pregunta}]
        consultas = []  # cada llamada a calcular que salió bien: qué pidió y qué volvió (con el SQL)
        while True:
            respuesta = await claude.messages.create(model=MODELO, max_tokens=16000, system=SISTEMA,
                                                     tools=tools, messages=mensajes)
            mensajes.append({"role": "assistant", "content": respuesta.content})

            # Si no pidió ninguna tool, terminó: lo que escribió es la respuesta final
            if respuesta.stop_reason != "tool_use":
                texto = "".join(b.text for b in respuesta.content if b.type == "text")
                return {"pregunta": pregunta, "texto": texto, "consultas": consultas}

            # Paso 3: correr cada tool que pidió, vía MCP, y juntar los resultados en un solo mensaje
            resultados = []
            for bloque in respuesta.content:
                if bloque.type != "tool_use":
                    continue
                print(f"→ {bloque.name}({json.dumps(bloque.input, ensure_ascii=False)})")
                resultado = await mcp.call_tool(bloque.name, bloque.input)
                if bloque.name == "calcular" and not resultado.is_error:
                    consultas.append({"argumentos": bloque.input, "resultado": json.loads(resultado.content[0].text)})
                resultados.append({"type": "tool_result", "tool_use_id": bloque.id,
                                   "content": resultado.content[0].text, "is_error": resultado.is_error})
            mensajes.append({"role": "user", "content": resultados})


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('Uso: .venv/bin/python agente.py "¿pregunta?"')
    print(asyncio.run(responder(sys.argv[1]))["texto"])
