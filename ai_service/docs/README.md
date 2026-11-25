
# HBntory - AI Query Service

## 1. Présentation

L'AI Query Service est un service indépendant permettant aux utilisateurs
du Client Web de poser des questions en langage naturel sur les produits
et les stocks disponibles dans les différentes agences de HBntory.

Le service utilise un agent IA connecté au HBntory MCP Server afin
d'obtenir des informations réelles provenant de la Product API et de
la base de données PostgreSQL.

L'objectif est de fournir des réponses fiables, basées sur les données
disponibles, sans inventer d'informations.

## 2. Architecture

```text
Client Web
    |
    | HTTP / JSON
    v
AI Query Service (Flask)
    |
    v
Agent IA (OpenAI)
    |
    v
Client MCP
    |
    | MCP
    v
HBntory MCP Server
    |
    +----------------------+
    |                      |
    v                      v
Product API           PostgreSQL
                       (lecture seule)
```

### Rôle des composants

- **Client Web** : transmet les questions des utilisateurs.
- **AI Query Service** : reçoit les requêtes et retourne les réponses.
- **Agent IA** : analyse les questions et décide quels outils utiliser.
- **Client MCP** : communique avec le serveur MCP.
- **HBntory MCP Server** : expose les outils autorisés à l'agent.
- **Product API** : fournit les informations du catalogue produits.
- **PostgreSQL** : fournit les informations de stock par agence.

L'agent IA n'accède jamais directement à PostgreSQL.
Toutes les consultations de stock passent par les outils MCP.

## 3. Communication avec le Client Web

Le service utilise une API REST (Representational State Transfer)
avec des échanges JSON (JavaScript Object Notation) sur HTTP
(Hypertext Transfer Protocol).

La communication entre le Client Web et l'AI Query Service utilise
des requêtes HTTP classiques, et non des WebSockets.

### Vérification du service

**Endpoint :**

```http
GET /health
```

Exemple de réponse :

```json
{
  "service": "HBntory AI Query Service",
  "status": "healthy"
}
```

### Envoyer une question

**Endpoint :**

```http
POST /ask
```

Exemple de requête :

```json
{
  "question": "Donne-moi les informations du produit ID 12."
}
```

Exemple de réponse :

```json
{
  "answer": "Voici les informations disponibles sur le produit..."
}
```

Le champ `question` doit contenir une chaîne de caractères non vide.

Une question invalide retourne une réponse HTTP 400.

Une erreur de traitement retourne une réponse HTTP 500.

## 4. Questions prises en charge

L'agent IA peut répondre aux questions concernant les produits et
les stocks.

### Catalogue des produits

- Consulter la liste des produits disponibles.
- Rechercher les informations d'un produit par son identifiant.
- Rechercher les informations d'un produit par son SKU.
- Consulter les caractéristiques disponibles d'un produit.
- Consulter les prix disponibles.
- Identifier le statut d'un produit lorsque cette information
  est fournie par la Product API.

### Consultation des stocks

- Consulter le stock d'un produit dans toutes les agences.
- Consulter les produits et leurs quantités dans une agence.
- Identifier les agences dans lesquelles un produit est disponible.
- Identifier les produits dont le stock est égal à zéro.
- Comparer les quantités disponibles entre plusieurs agences.

### Vérification de disponibilité d'une commande

- Vérifier une commande contenant plusieurs produits.
- Comparer les quantités demandées aux quantités disponibles.
- Déterminer si les quantités sont suffisantes.
- Vérifier si une commande peut être satisfaite en utilisant
  plusieurs agences.

L'agent ne confirme jamais une réservation ou une commande.
Il fournit uniquement une analyse basée sur les stocks consultés.

### Questions hors périmètre

L'agent répond clairement lorsqu'une question ne concerne pas
les produits ou les stocks de HBntory.

Il ne doit pas inventer de réponses à partir de connaissances
extérieures aux données disponibles.

## 5. Outils MCP utilisés

Le serveur MCP expose quatre outils autorisés à l'agent IA.

### list_products

Récupère la liste des produits depuis la Product API.

### get_product

Récupère les informations détaillées d'un produit à partir de son
identifiant ou de son SKU.

### get_stock_by_product

Récupère les quantités disponibles d'un produit dans toutes les agences.

Les informations retournées comprennent notamment :

- Identifiant de l'agence.
- Nom de l'agence.
- Identifiant du produit.
- Quantité disponible.

### get_stock_by_branch

Récupère les produits et leurs quantités disponibles dans une agence.

Les informations retournées comprennent notamment :

- Identifiant de l'agence.
- Nom de l'agence.
- Identifiant du produit.
- Quantité disponible.

## 6. Gestion des données et des accès

HBntory utilise deux sources de données distinctes.

### Product API

La Product API fournit les informations relatives aux produits :

- Identifiant.
- SKU.
- Nom.
- Caractéristiques.
- Prix.
- Autres informations disponibles dans le catalogue.

L'AI Query Service consulte ces informations par l'intermédiaire
des outils MCP.

### PostgreSQL

PostgreSQL stocke les informations nécessaires à la gestion des stocks :

- Utilisateurs.
- Agences.
- Identifiants des produits.
- Quantités disponibles par agence.

La base de données ne stocke pas les descriptions, les noms,
les prix ou les images des produits.

### Sécurité

L'accès de l'AI Query Service aux stocks est effectué en lecture seule.

L'utilisateur PostgreSQL utilisé par le serveur MCP dispose
des permissions nécessaires pour consulter les données,
mais pas pour modifier les stocks.

L'agent IA ne peut pas modifier les quantités disponibles.

La modification des stocks est réservée au Backoffice.

## 7. Fiabilité des réponses

L'agent IA doit respecter les règles suivantes :

- Utiliser les outils MCP pour obtenir les informations nécessaires.
- Bas­er ses réponses sur les données réellement retournées.
- Ne jamais inventer un nom, un prix, une caractéristique
  ou une quantité.
- Signaler lorsqu'un produit est introuvable.
- Signaler lorsqu'une agence est introuvable.
- Ne jamais confondre une absence de résultat avec un stock nul.
- Ne jamais transformer une erreur technique en quantité nulle.
- Signaler clairement les informations indisponibles.
- Répondre en français de manière claire et concise.

Une quantité égale à zéro signifie que le produit n'est pas disponible
dans l'agence concernée.

Une erreur technique ne permet pas de conclure que le stock est nul.

## 8. Gestion des erreurs

Le service prend en charge plusieurs situations :

| Situation | Comportement |
|---|---|
| Question vide | Réponse HTTP 400 |
| Produit inexistant | Message indiquant que le produit est introuvable |
| Agence inexistante | Message indiquant que l'agence est introuvable |
| Erreur Product API | Signalement de l'indisponibilité |
| Erreur PostgreSQL | Signalement de l'erreur de consultation |
| Question hors périmètre | Réponse expliquant les limites du service |

Les erreurs techniques ne doivent jamais être présentées comme
des résultats métier valides.

## 9. Configuration

Les variables d'environnement sont définies dans le fichier `.env`.

Variables nécessaires :

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=your_model_name
MCP_SERVER_URL=http://localhost:8000/mcp
```

Le serveur MCP utilise également ses propres variables :

```env
DATABASE_URL=postgresql+psycopg://utilisateur:mot_de_passe@localhost:5432/hbntory
PRODUCT_API_URL=http://localhost:5001
```

Les fichiers `.env` contenant des informations sensibles ne doivent
jamais être publiés sur GitHub.

Les valeurs d'exemple sont disponibles dans les fichiers
`.env.example`.

## 10. Technologies utilisées

- Python
- Flask
- OpenAI API
- MCP (Model Context Protocol)
- FastMCP
- HTTPX
- SQLAlchemy
- PostgreSQL
- Psycopg
- Pytest

## 11. Tests

Les tests du serveur MCP sont exécutés avec Pytest.

Depuis la racine du projet :

```bash
source mcp_server/venv/bin/activate

PYTHONPATH=mcp_server pytest -v mcp_server/tests/
```

Les tests couvrent notamment :

- La récupération du catalogue produits.
- La récupération des détails d'un produit.
- La gestion des erreurs de la Product API.
- La consultation du stock par produit.
- La consultation du stock par agence.
- La validation des identifiants.
- La gestion des erreurs PostgreSQL.

**Dernier résultat enregistré : 20 tests réussis sur 20.**

## 12. Démarrage du service

Depuis la racine du projet :

```bash
source ai_service/venv/bin/activate

python -m ai_service.app
```

Le service écoute par défaut sur le port 5002.

Le serveur MCP doit également être démarré et accessible à l'adresse
définie dans `MCP_SERVER_URL`.

## 13. État du projet

Les fonctionnalités suivantes ont été implémentées :

- Service AI Query Service indépendant.
- Endpoint REST pour le Client Web.
- Agent IA connecté au serveur MCP.
- Consultation du catalogue produits.
- Consultation des détails d'un produit.
- Consultation des stocks par produit.
- Consultation des stocks par agence.
- Accès PostgreSQL en lecture seule depuis le serveur MCP.
- Gestion des erreurs et des informations indisponibles.
- Tests automatisés du serveur MCP.

Les tests automatisés du serveur MCP affichent actuellement
20 réussites sur 20.

L'intégration complète avec Docker Compose et la validation
de l'ensemble des scénarios de bout en bout restent à finaliser.
