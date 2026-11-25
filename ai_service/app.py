
#!/usr/bin/env python3
"""Point d'entrée du service AI Query Service de HBntory."""

import asyncio
import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS


# Active les journaux INFO pour tous les modules.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s : %(message)s"
)

from ai_service.agent import ask_agent


# Chargement de la configuration du service.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)

# Autorise le client web Live Server à appeler la route /ask.
CORS(
    app,
    resources={
        r"/ask": {
            "origins": "http://localhost:5500"
        }
    }
)

app.logger.setLevel("INFO")


@app.route("/health", methods=["GET"])
def health_check():
    """Vérifie que le service AI Query Service fonctionne.

    Returns:
        Response: État du service au format JSON.
    """
    return jsonify({
        "service": "HBntory AI Query Service",
        "status": "healthy"
    }), 200


@app.route("/ask", methods=["POST"])
def ask():
    """Reçoit une question et transmet son traitement à l'agent.

    Returns:
        Response: Réponse de l'agent ou message d'erreur.
    """
    data = request.get_json(silent=True) or {}
    question = data.get("question")

    if not isinstance(question, str) or not question.strip():
        return jsonify({
            "error": "Une question valide est obligatoire."
        }), 400

    try:
        answer = asyncio.run(ask_agent(question))
        return jsonify({"answer": answer}), 200

    except Exception:
        app.logger.exception(
            "Erreur lors du traitement de la question."
        )
        return jsonify({
            "error": "Impossible de traiter la question."
        }), 500


if __name__ == "__main__":
    """Démarre le serveur Flask en mode développement."""

    port = int(os.getenv("AI_SERVICE_PORT", 5002))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
