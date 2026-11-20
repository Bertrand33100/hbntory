# HBntory — Assistant intelligent de gestion de stock

## Présentation

HBntory est une plateforme de gestion de stock destinée à une enseigne fictive possédant plusieurs agences.

Le projet comporte deux interfaces :

- **Backoffice** : application interne réservée aux employés connectés pour gérer les utilisateurs et les stocks.
- **Client Web** : interface publique permettant aux visiteurs de poser des questions en langage naturel à un assistant intelligent.

L'assistant IA permet notamment de consulter le catalogue des produits, d'obtenir les caractéristiques d'un produit, de connaître les quantités disponibles dans les agences et de recevoir des recommandations d'équipement.

## Architecture générale

Le projet repose sur plusieurs composants qui communiquent entre eux.

| Composant | Responsabilité |
|---|---|
| Client Web | Interface publique HTML, CSS et JavaScript |
| AI Query Service | Réception des questions et orchestration de l'agent IA |
| HBntory MCP Server | Exposition des outils de consultation des données |
| Product API | Fourniture des informations sur les produits |
| PostgreSQL | Stockage des agences et des quantités de stock |
| Backoffice | Gestion interne des utilisateurs et des stocks |

### Communication entre les composants

```text
Utilisateur
    |
    v
Client Web
    |
    | HTTP / REST
    v
AI Query Service
    |
    | MCP / Streamable HTTP
    v
HBntory MCP Server
    |
    +----------------------+
    |                      |
    v                      v
Product API            PostgreSQL
    |                      |
    v                      v
Informations          Quantités de stock
produits              et agences
```

L'agent IA accède aux informations des produits et des stocks uniquement à travers les outils exposés par le serveur MCP.

## Technologies utilisées

- HTML5
- CSS3
- JavaScript
- Python
- Flask
- Flask-Cors
- OpenAI API
- MCP (Model Context Protocol)
- FastMCP
- PostgreSQL
- SQLAlchemy
- Docker

## Structure du projet

```text
hbntory/
├── ai_service/
│   ├── .env.example
│   ├── agent.py
│   ├── app.py
│   ├── mcp_client.py
│   ├── openai_client.py
│   └── requirements.txt
│
├── backoffice/
│   ├── app.py
│   ├── models.py
│   ├── seed.py
│   └── requirements.txt
│
├── client_web/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
│
├── docs/
│   ├── architecture.md
│   ├── architecture.png
│   ├── database.md
│   ├── decisions.md
│   ├── mvp.md
│   └── HBntory_Architecture_Generale.drawio
│
├── mcp_server/
│   ├── .env.example
│   ├── requirements.txt
│   └── server.py
│
├── .gitignore
└── README.md
```

## Configuration et installation

### Prérequis

- Python
- Git
- Docker
- PostgreSQL
- Un compte OpenAI et une clé API
- Visual Studio Code
- L'extension Live Server pour lancer le Client Web

### 1. Récupérer le projet

```bash
git clone https://github.com/Bertrand33100/hbntory.git
cd hbntory
```

### 2. Configurer le serveur MCP

Créer le fichier d'environnement :

```bash
cp mcp_server/.env.example mcp_server/.env
```

Configurer les variables dans `mcp_server/.env` :

```env
DATABASE_URL=postgresql+psycopg://utilisateur:mot_de_passe@localhost:5432/hbntory
PRODUCT_API_URL=http://localhost:5001
```

Installer les dépendances :

```bash
cd mcp_server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Démarrer le serveur depuis la racine du projet :

```bash
python mcp_server/server.py
```

Le serveur MCP est accessible à l'adresse :

`http://localhost:8000/mcp`

### 3. Configurer l'AI Query Service

Créer le fichier d'environnement :

```bash
cp ai_service/.env.example ai_service/.env
```

Configurer les variables dans `ai_service/.env` :

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=your_model_name
MCP_SERVER_URL=http://localhost:8000/mcp
```

Remplacer les valeurs fictives par les informations de configuration réelles.

Installer les dépendances :

```bash
cd ai_service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Démarrer le service depuis la racine du projet :

```bash
python -m ai_service.app
```

L'AI Query Service est accessible à l'adresse :

`http://127.0.0.1:5002`

Vérifier son état :

```bash
curl http://127.0.0.1:5002/health
```

### 4. Démarrer la Product API

La Product API est fournie dans un dépôt GitHub séparé :

https://github.com/hbtn-edu/hbntory-products-api

Après avoir récupéré ce dépôt et configuré son environnement :

```bash
docker compose up --build
```

La Product API est accessible sur :

`http://localhost:5001`

Vérifier son état :

```bash
curl http://localhost:5001/health
```

### 5. Démarrer PostgreSQL

Le projet utilise PostgreSQL pour stocker les agences et les quantités de stock.

Dans notre environnement local, le conteneur PostgreSQL est nommé `hbntory-db`.

Pour le démarrer :

```bash
docker start hbntory-db
```

Vérifier son état :

```bash
docker ps
```

### 6. Lancer le Client Web

Ouvrir le dossier `client_web` dans Visual Studio Code.

Avec l'extension Live Server :

1. Ouvrir `client_web/index.html`.
2. Cliquer sur **Open with Live Server**.
3. Accéder à l'interface dans le navigateur.

Adresse locale utilisée :

`http://localhost:5500`

## Fonctionnalités du Client Web

L'interface publique permet :

- De saisir une question en langage naturel.
- D'envoyer la question à l'AI Query Service.
- D'afficher la réponse de l'assistant.
- D'afficher un message d'attente pendant le traitement.
- De désactiver temporairement le bouton d'envoi.
- D'afficher un message clair en cas d'indisponibilité du service.
- De s'adapter aux écrans mobiles.

Le thème graphique utilisé est **Midnight Tech**, avec une palette bleu nuit et cyan.

## Exemples de questions

Voici des exemples de questions testées avec l'assistant HBntory.

### Consultation du catalogue

**Question :**

> Quels produits sont disponibles dans le catalogue ?

L'assistant présente le catalogue et distingue les produits non arrêtés des produits arrêtés.

### Consultation des caractéristiques d'un produit

**Question :**

> Donne-moi les caractéristiques du produit HB-SEC-1402.

L'assistant retourne notamment le nom, la catégorie, la marque, le prix, le poids et le fournisseur.

### Consultation des stocks par produit

**Question :**

> Quel est le stock du produit 34 dans toutes les agences ?

L'assistant consulte les quantités disponibles dans les différentes agences.

### Consultation des stocks par agence

**Question :**

> Quels produits sont disponibles dans l'agence de Paris et en quelles quantités ?

L'assistant identifie l'agence et présente les produits avec leurs quantités.

### Recommandation d'équipements

**Question :**

> Je prépare une salle informatique pour 10 étudiants. Quels produits du catalogue me recommandes-tu pour équiper cette salle ?

L'assistant propose une liste d'équipements, les quantités recommandées et les prix du catalogue.

Les recommandations ne constituent pas une confirmation des stocks disponibles.

## Gestion des erreurs

Le Client Web prévoit plusieurs contrôles :

- Vérification d'une question vide.
- Vérification du statut HTTP de la réponse.
- Vérification de la présence d'une réponse valide.
- Affichage d'un message d'erreur si le service IA est inaccessible.
- Réactivation du bouton après le traitement, même en cas d'erreur.

Un test a été effectué en arrêtant volontairement l'AI Query Service.

Message affiché :

> Impossible de contacter l'assistant. Veuillez réessayer.

## Sécurité et accès aux données

- Le Client Web est public et ne nécessite pas d'authentification.
- Les clés API et les mots de passe doivent rester dans les fichiers `.env`.
- Les fichiers `.env` ne doivent pas être publiés sur GitHub.
- L'agent IA utilise uniquement les outils autorisés du serveur MCP.
- Les outils de consultation des données sont en lecture seule pour l'agent IA.
- L'agent ne doit pas inventer une quantité lorsque les données de stock sont absentes.

## Ports utilisés en développement local

| Service | Port |
|---|---:|
| Client Web | 5500 |
| Product API | 5001 |
| AI Query Service | 5002 |
| HBntory MCP Server | 8000 |
| PostgreSQL | 5432 |

## État de développement

La tâche Client Web Interface comprend :

- La création de l'interface publique.
- La connexion à l'AI Query Service.
- L'affichage des réponses de l'assistant.
- La gestion du chargement.
- La gestion des erreurs.
- Les tests de consultation du catalogue et des produits.
- Les tests de consultation des stocks par produit et par agence.
- Les tests de recommandations d'équipements.

La documentation des tests et la validation finale de la tâche sont à compléter selon l'avancement de l'équipe.

## Auteur et dépôt

**Projet :** HBntory

**GitHub :** https://github.com/Bertrand33100/hbntory
