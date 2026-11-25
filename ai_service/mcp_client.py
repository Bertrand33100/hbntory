
#!/usr/bin/env python3
"""Client MCP du service AI Query Service de HBntory.

Ce module permet au service IA de découvrir les outils du serveur MCP
et de les exécuter pour récupérer les données du catalogue.
"""

import os

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


# Chargement de la configuration du service.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "http://localhost:8000/mcp"
)


async def list_mcp_tools():
    """Récupère les outils et leurs schémas depuis le serveur MCP.

    Returns:
        list[dict]: Liste des outils avec leur nom, description
            et schéma des paramètres.
    """
    async with streamable_http_client(MCP_SERVER_URL) as (
        read_stream,
        write_stream
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.list_tools()

            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema
                }
                for tool in result.tools
            ]


async def call_mcp_tool(
    tool_name: str,
    arguments: dict | None = None
):
    """Exécute un outil disponible sur le serveur MCP.

    Args:
        tool_name (str): Nom de l'outil à exécuter.
        arguments (dict | None): Arguments transmis à l'outil.

    Returns:
        list: Contenu retourné par le serveur MCP.

    Raises:
        RuntimeError: Si l'outil retourne une erreur.
    """
    async with streamable_http_client(MCP_SERVER_URL) as (
        read_stream,
        write_stream
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                tool_name,
                arguments=arguments or {}
            )

            if result.is_error:
                error_details = "\n".join(
                    getattr(item, "text", str(item))
                    for item in result.content
                )

                raise RuntimeError(
                    f"Erreur lors de l'exécution de {tool_name} : "
                    f"{error_details}"
                )

            return result.content
