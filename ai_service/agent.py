
#!/usr/bin/env python3
"""Agent IA du service AI Query Service de HBntory.

Ce module coordonne OpenAI et les outils MCP pour répondre
aux questions à partir des données disponibles du catalogue.
"""

import json
import logging

from ai_service.mcp_client import list_mcp_tools, call_mcp_tool
from ai_service.openai_client import (
    create_openai_client,
    get_openai_model
)


logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 3

INSTRUCTIONS_AGENT = """
Tu es l'assistant du système HBntory.

Ton rôle est de répondre aux questions concernant le catalogue
des produits de l'entreprise.

Règles obligatoires :

1. Utilise les outils MCP pour obtenir les données produits.
2. N'invente jamais un nom, un prix ou une caractéristique.
3. Si une information est indisponible, indique-le clairement.
4. Si la question est hors périmètre, explique-le clairement.
5. Réponds en français de manière claire et concise.
6. Base tes réponses uniquement sur les données disponibles.
7. Ne prétends jamais connaître les stocks : les outils de stock
   ne sont pas encore disponibles.
"""


OUTILS_AUTORISES = {
    "get_product",
    "list_products"
}


async def get_agent_context():
    """Récupère les outils disponibles sur le serveur MCP.

    Returns:
        list[dict]: Liste des outils et de leurs paramètres.
    """
    tools = await list_mcp_tools()

    return [
        tool for tool in tools
        if tool["name"] in OUTILS_AUTORISES
    ]


async def build_openai_tools():
    """Convertit les outils MCP au format attendu par OpenAI.

    Returns:
        list[dict]: Définitions des outils compatibles avec OpenAI.
    """
    mcp_tools = await get_agent_context()

    return [
        {
            "type": "function",
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["input_schema"],
            "strict": False
        }
        for tool in mcp_tools
    ]


async def execute_product_tool(tool_name, arguments=None):
    """Exécute un outil produit autorisé sur le serveur MCP.

    Args:
        tool_name (str): Nom de l'outil à exécuter.
        arguments (dict | None): Arguments transmis à l'outil.

    Returns:
        list: Données retournées par le serveur MCP.

    Raises:
        ValueError: Si l'outil demandé n'est pas autorisé.
    """
    if tool_name not in OUTILS_AUTORISES:
        raise ValueError("Cet outil n'est pas autorisé.")

    logger.info(
        "Exécution de l'outil MCP : %s",
        tool_name
    )

    return await call_mcp_tool(tool_name, arguments)


def format_tool_result(result):
    """Convertit le résultat MCP en texte JSON.

    Args:
        result (list): Contenu retourné par l'outil MCP.

    Returns:
        str: Résultat sérialisé au format JSON.
    """
    formatted_result = []

    for item in result:
        item_text = getattr(item, "text", None)

        if item_text is not None:
            try:
                formatted_result.append(json.loads(item_text))
            except json.JSONDecodeError:
                formatted_result.append(item_text)
        else:
            formatted_result.append(str(item))

    return json.dumps(
        formatted_result,
        ensure_ascii=False
    )


async def ask_agent(question):
    """Interroge l'agent et lui permet d'utiliser les outils MCP.

    Args:
        question (str): Question formulée par l'utilisateur.

    Returns:
        str: Réponse finale de l'agent.

    Raises:
        ValueError: Si la question est vide ou invalide.
        RuntimeError: Si une erreur survient pendant le traitement.
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("La question ne peut pas être vide.")

    try:
        client = create_openai_client()
        tools = await build_openai_tools()

        response = client.responses.create(
            model=get_openai_model(),
            instructions=INSTRUCTIONS_AGENT,
            input=question.strip(),
            tools=tools
        )

        for round_number in range(MAX_TOOL_ROUNDS + 1):
            tool_calls = [
                item for item in response.output
                if item.type == "function_call"
            ]

            if not tool_calls:
                return response.output_text

            if round_number >= MAX_TOOL_ROUNDS:
                raise RuntimeError(
                    "Nombre maximal de cycles d'outils atteint."
                )

            tool_outputs = []

            for tool_call in tool_calls:
                if tool_call.name not in OUTILS_AUTORISES:
                    raise ValueError(
                        f"Outil non autorisé : {tool_call.name}"
                    )

                arguments = json.loads(tool_call.arguments)

                result = await execute_product_tool(
                    tool_call.name,
                    arguments
                )

                tool_outputs.append({
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": format_tool_result(result)
                })

            response = client.responses.create(
                model=get_openai_model(),
                instructions=INSTRUCTIONS_AGENT,
                previous_response_id=response.id,
                input=tool_outputs
            )

        raise RuntimeError(
            "L'agent n'a pas produit de réponse finale."
        )

    except Exception as error:
        logger.exception(
            "Erreur pendant le traitement de la question."
        )
        raise RuntimeError(
            "Erreur pendant le traitement de la question."
        ) from error
