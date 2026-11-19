
#!/usr/bin/env python3
"""Agent IA du service AI Query Service de HBntory."""

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

Ton rôle est de répondre aux questions concernant :
- le catalogue des produits ;
- les caractéristiques des produits ;
- les stocks disponibles dans les agences ;
- la disponibilité des produits dans une ou plusieurs agences.

Règles obligatoires :

1. Utilise les outils MCP pour obtenir les informations nécessaires.
2. Utilise list_products pour consulter le catalogue.
3. Utilise get_product pour obtenir les détails d'un produit.
4. Utilise get_stock_by_product pour consulter le stock d'un
   produit dans toutes les agences.
5. Utilise get_stock_by_branch pour consulter les produits
   et leurs quantités dans une agence.
6. Pour vérifier une commande contenant plusieurs produits,
   consulte les stocks de chaque produit et compare les quantités
   demandées aux quantités disponibles.
7. Une commande peut être satisfaite par plusieurs agences.
8. N'invente jamais un nom, un prix, une caractéristique,
   une quantité ou une disponibilité.
9. Si un produit n'existe pas dans le catalogue, indique-le.
10. Si une agence ou une information est indisponible,
    indique-le clairement.
11. Une quantité égale à zéro signifie que le produit
    n'est pas disponible dans cette agence.
12. Ne confonds jamais une absence de résultat avec un stock nul.
13. Si un outil retourne une erreur, analyse son message.
    Si le message indique qu'un produit est introuvable,
    informe clairement l'utilisateur.
14. Ne transforme jamais une erreur technique en quantité nulle.
15. Pour les questions hors périmètre, explique clairement
    que tu ne peux pas y répondre.
16. Réponds en français de manière claire et concise.
17. Base tes réponses uniquement sur les données retournées
    par les outils disponibles.

Pour les questions de disponibilité :
- Présente les quantités par agence.
- Indique si les quantités demandées sont suffisantes.
- Ne prétends jamais qu'une commande est réservée ou confirmée.
"""


OUTILS_AUTORISES = {
    "list_products",
    "get_product",
    "get_stock_by_product",
    "get_stock_by_branch"
}


async def get_agent_context():
    """Récupère les outils autorisés disponibles sur MCP."""
    tools = await list_mcp_tools()

    outils_autorises = [
        tool for tool in tools
        if tool["name"] in OUTILS_AUTORISES
    ]

    outils_disponibles = {
        tool["name"] for tool in outils_autorises
    }

    outils_manquants = OUTILS_AUTORISES - outils_disponibles

    if outils_manquants:
        logger.warning(
            "Outils MCP non disponibles : %s",
            ", ".join(sorted(outils_manquants))
        )

    return outils_autorises


async def build_openai_tools():
    """Convertit les outils MCP au format OpenAI."""
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


async def execute_mcp_tool(tool_name, arguments=None):
    """Exécute un outil MCP autorisé."""
    if tool_name not in OUTILS_AUTORISES:
        raise ValueError("Cet outil MCP n'est pas autorisé.")

    logger.info(
        "Exécution de l'outil MCP : %s avec les arguments : %s",
        tool_name,
        arguments
    )

    result = await call_mcp_tool(tool_name, arguments)

    logger.info(
        "Résultat reçu de l'outil MCP : %s",
        tool_name
    )

    return result


def format_tool_result(result):
    """Convertit le résultat MCP en texte JSON."""
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


def extract_error_messages(error):
    """Extrait les messages des exceptions, y compris les groupes."""
    messages = []

    if isinstance(error, BaseExceptionGroup):
        for nested_error in error.exceptions:
            messages.extend(
                extract_error_messages(nested_error)
            )
    else:
        messages.append(str(error))

    return messages


async def ask_agent(question):
    """Interroge l'agent et lui permet d'utiliser les outils MCP."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("La question ne peut pas être vide.")

    try:
        client = create_openai_client()
        tools = await build_openai_tools()

        logger.info(
            "Nombre d'outils transmis à OpenAI : %s",
            len(tools)
        )

        response = client.responses.create(
            model=get_openai_model(),
            instructions=INSTRUCTIONS_AGENT,
            input=question.strip(),
            tools=tools
        )

        for round_number in range(MAX_TOOL_ROUNDS + 1):

            logger.info(
                "Cycle OpenAI numéro : %s",
                round_number + 1
            )

            logger.info(
                "Diagnostic OpenAI - statut : %s",
                response.status
            )

            logger.info(
                "Diagnostic OpenAI - types de sortie : %s",
                [item.type for item in response.output]
            )

            logger.info(
                "Diagnostic OpenAI - texte : %r",
                response.output_text
            )

            tool_calls = [
                item for item in response.output
                if item.type == "function_call"
            ]

            if not tool_calls:
                if not response.output_text:
                    raise RuntimeError(
                        "L'agent IA n'a retourné aucun texte."
                    )

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

                logger.info(
                    "Appel demandé par OpenAI : %s, arguments : %s",
                    tool_call.name,
                    arguments
                )

                try:
                    result = await execute_mcp_tool(
                        tool_call.name,
                        arguments
                    )

                    output = format_tool_result(result)

                except Exception as tool_error:
                    error_messages = extract_error_messages(
                        tool_error
                    )

                    logger.warning(
                        "Erreur de l'outil MCP %s : %s",
                        tool_call.name,
                        error_messages
                    )

                    output = json.dumps(
                        {
                            "tool": tool_call.name,
                            "error": error_messages
                        },
                        ensure_ascii=False
                    )

                tool_outputs.append({
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": output
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
