
#!/usr/bin/env python3
"""Gestion des communications entre HBntory et l'API OpenAI."""

import os

from dotenv import load_dotenv
from openai import OpenAI


# Chargement de la configuration du service.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def create_openai_client():
    """Initialise le client OpenAI.

    Returns:
        OpenAI: Client configuré pour communiquer avec OpenAI.

    Raises:
        ValueError: Si la clé API est absente.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "La variable OPENAI_API_KEY n'est pas configurée."
        )

    return OpenAI(api_key=api_key)


def get_openai_model():
    """Récupère le nom du modèle OpenAI configuré.

    Returns:
        str: Nom du modèle à utiliser.

    Raises:
        ValueError: Si aucun modèle n'est configuré.
    """
    model = os.getenv("OPENAI_MODEL")

    if not model:
        raise ValueError(
            "La variable OPENAI_MODEL n'est pas configurée."
        )

    return model


def ask_openai(question):
    """Envoie une question simple à OpenAI.

    Args:
        question (str): Question formulée par l'utilisateur.

    Returns:
        str: Réponse textuelle du modèle.

    Raises:
        ValueError: Si la question est vide.
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("La question ne peut pas être vide.")

    client = create_openai_client()

    response = client.responses.create(
        model=get_openai_model(),
        input=question.strip()
    )

    return response.output_text
