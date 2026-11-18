
# HBntory - AI Query Service

## 1. Présentation

L'AI Query Service est un service indépendant permettant au Client Web
de transmettre des questions en langage naturel.

Le service utilise un agent IA connecté au Product MCP Server afin
de récupérer des informations réelles sur les produits.

## 2. Architecture

Client Web
    |
    v
AI Query Service (Flask)
    |
    v
Agent IA (OpenAI)
    |
    v
Client MCP
    |
    v
HBntory MCP Server
    |
    v
Product API

## 3. Communication avec le Client Web

Le service utilise une API REST (Representational State Transfer)
avec des échanges JSON sur HTTP.

### Vérification du service

GET /health

### Envoyer une question

POST /ask

Exemple de requête :

{
  "question": "Donne les informations du produit ID 12."
}

Exemple de réponse :

{
  "answer": "Voici les informations disponibles sur le produit..."
}

## 4. Questions actuellement prises en charge

- Obtenir les informations d'un produit par son identifiant.
- Obtenir les informations d'un produit par son SKU.
- Consulter le catalogue des produits.
- Consulter les caractéristiques et les prix disponibles.
- Identifier le statut d'un produit (actif ou abandonné).

## 5. Outils MCP utilisés

### list_products

Récupère la liste des produits depuis la Product API.

### get_product

Récupère les informations d'un produit à partir de son identifiant
ou de son SKU.

## 6. Fiabilité des réponses

L'agent doit utiliser les outils MCP pour récupérer les informations.

Il ne doit pas inventer de nom, de prix ou de caractéristique.

Lorsqu'une information n'est pas disponible, il doit le signaler.

## 7. Gestion du stock

Les fonctionnalités de consultation du stock ne sont pas encore
intégrées à l'AI Query Service.

Les outils prévus sont :

- get_stock_by_product
- get_stock_by_branch

Ils seront intégrés lorsque la partie stock sera disponible.

## 8. Configuration

Les variables d'environnement sont définies dans le fichier `.env`.

Variables nécessaires :

- OPENAI_API_KEY
- OPENAI_MODEL
- MCP_SERVER_URL

## 9. Démarrage

Depuis la racine du projet :

```bash
source ai_service/venv/bin/activate
python -m ai_service.app
```

Le service écoute par défaut sur le port 5002.

## 10. État du projet

Le service Flask et la connexion aux outils produits MCP ont été
testés.

L'intégration des outils de stock et la validation complète des
réponses de l'agent restent à effectuer.
