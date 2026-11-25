# HBntory — Assistant intelligent de gestion de stock

## Présentation

HBntory est une plateforme de gestion de stock destinée à une enseigne fictive possédant plusieurs agences.

Le projet comporte deux interfaces :

- **Backoffice** : application interne réservée aux employés connectés pour gérer les utilisateurs et les stocks.
- **Client Web** : interface publique permettant aux visiteurs de poser des questions en langage naturel à un assistant intelligent.

L'assistant IA permet notamment de consulter le catalogue des produits, d'obtenir les caractéristiques d'un produit, de connaître les quantités disponibles dans les agences et de recevoir des recommandations d'équipement.

## Équipe

| Membre | Responsabilités principales |
|---|---|
| Thomas | Base de données, Backoffice (authentification, rôles, gestion du stock et des utilisateurs, interface) |
| Bertrand | Serveur MCP, AI Query Service, Client Web |

L'intégration, les tests et la documentation ont été réalisés ensemble.

## Architecture générale

Le projet repose sur plusieurs composants qui communiquent entre eux.

| Composant | Responsabilité |
|---|---|
| Client Web | Interface publique HTML, CSS et JavaScript |
| AI Query Service | Réception des questions et orchestration de l'agent IA |
| HBntory MCP Server | Exposition des outils de consultation des données |
| Product API | Fourniture des informations sur les produits |
| PostgreSQL | Stockage des agences, des utilisateurs et des quantités de stock |
| Backoffice | Gestion interne des utilisateurs et des stocks (API REST Flask + interface HTML/CSS/JS) |

### Communication entre les composants

```text
 Visiteur                                Employé / Admin
    |                                          |
    v                                          v
Client Web                                Backoffice
    |                                      |        |
    | HTTP / REST                          |        | HTTP
    v                                      |        v
AI Query Service ---> OpenAI               |    Product API
    |                                      |   (vérification
    | MCP / Streamable HTTP                |    des produits)
    v                                      |
HBntory MCP Server                         | lecture / écriture
    |                                      |
    +----------------------+               |
    |                      |               |
    v                      v               v
Product API            PostgreSQL <--------+
(informations          (agences, utilisateurs,
 produits)              quantités de stock)
```

- Le **Backoffice** est le seul composant qui modifie la base (stock et utilisateurs).
- L'**agent IA** accède aux informations des produits et des stocks uniquement à travers les outils du serveur MCP, en lecture seule.
- Les **détails des produits** (nom, SKU, prix…) ne sont jamais copiés en base : ils viennent toujours de la Product API.

Documentation détaillée : `docs/architecture.md`, `docs/database.md`, `docs/auth.md`, `backoffice/README.md`.

## Technologies utilisées

- HTML5, CSS3, JavaScript
- Python, Flask, Flask-Cors
- SQLAlchemy, Flask-SQLAlchemy, psycopg 3
- PostgreSQL
- argon2-cffi (hachage des mots de passe)
- OpenAI API
- MCP (Model Context Protocol), FastMCP
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
│   ├── .env.example
│   ├── app.py
│   ├── database.py
│   ├── models.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── README.md
│   └── static/
│       ├── index.html
│       ├── style.css
│       └── app.js
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
│   ├── auth.md
│   ├── database.md
│   ├── decisions.md
│   ├── mvp.md
│   ├── tests.md
│   └── HBntory_Architecture_Generale.drawio
│
├── mcp_server/
│   ├── .env.example
│   ├── requirements.txt
│   ├── server.py
│   └── tests/
│
├── .gitignore
└── README.md
```

## Installation et lancement

Les services se lancent dans cet ordre : base de données → Product API → serveur MCP → AI Query Service → Backoffice → Client Web.

### Prérequis

- Python 3
- Git
- Docker
- Un compte OpenAI et une clé API
- Visual Studio Code et l'extension Live Server (pour le Client Web)

### 1. Récupérer le projet

```bash
git clone https://github.com/Bertrand33100/hbntory.git
cd hbntory
```

### 2. Initialiser la base de données

PostgreSQL tourne dans un conteneur Docker nommé `hbntory-db`.

**Première fois** : créer le conteneur.

```bash
docker run -d --name hbntory-db \
  -e POSTGRES_USER=hbntory \
  -e POSTGRES_PASSWORD=devpassword \
  -e POSTGRES_DB=hbntory \
  -p 5432:5432 \
  postgres:16
```

**Les fois suivantes** : simplement le démarrer.

```bash
docker start hbntory-db
```

**Remplir la base** (agences, compte admin, utilisateur standard, stock de départ) avec le script `seed.py`.
Les mots de passe sont choisis au lancement et ne sont jamais écrits dans le code :

```bash
cd backoffice
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="postgresql://hbntory:devpassword@localhost:5432/hbntory"
export ADMIN_PASSWORD="choisir-un-mot-de-passe-admin"
export USER_PASSWORD="choisir-un-mot-de-passe-utilisateur"
python seed.py
```

Le seed crée deux comptes : `admin` (rôle admin) et `common_user` (rôle utilisateur standard, agence de Paris).
Les mots de passe sont ceux de `ADMIN_PASSWORD` et `USER_PASSWORD`.

### 3. Démarrer la Product API

La Product API est fournie dans un dépôt GitHub séparé :

https://github.com/hbtn-edu/hbntory-products-api

Après avoir récupéré ce dépôt et configuré son environnement, depuis son dossier :

```bash
docker compose up -d --build
```

Vérifier son état :

```bash
curl http://localhost:5001/health
```

### 4. Configurer et démarrer le serveur MCP

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
cd ..
```

Démarrer le serveur depuis la racine du projet :

```bash
python mcp_server/server.py
```

Le serveur MCP est accessible à l'adresse `http://localhost:8000/mcp`.

### 5. Configurer et démarrer l'AI Query Service

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
cd ..
```

Démarrer le service depuis la racine du projet :

```bash
python -m ai_service.app
```

Vérifier son état :

```bash
curl http://127.0.0.1:5002/health
```

### 6. Démarrer le Backoffice

Dans un nouveau terminal :

```bash
cd backoffice
source .venv/bin/activate
export DATABASE_URL="postgresql://hbntory:devpassword@localhost:5432/hbntory"
export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
flask --app app run
```

Variables d'environnement du Backoffice (modèle dans `backoffice/.env.example`) :

| Variable | Obligatoire | Rôle |
|---|---|---|
| `DATABASE_URL` | oui | Adresse de la base PostgreSQL |
| `SECRET_KEY` | oui | Clé de signature du cookie de session |
| `PRODUCT_API_URL` | non | Adresse de la Product API (par défaut `http://localhost:5001`) |
| `COOKIE_SECURE` | non | `1` en production (HTTPS) pour n'envoyer le cookie qu'en HTTPS |

### 7. Lancer le Client Web

Ouvrir le dossier `client_web` dans Visual Studio Code, puis :

1. Ouvrir `client_web/index.html`.
2. Cliquer sur **Open with Live Server**.
3. Accéder à l'interface dans le navigateur : `http://localhost:5500`.

## Utiliser le Backoffice

Ouvrir `http://localhost:5000` et se connecter.

**Avec le compte `common_user`** (utilisateur standard) :

- voir le stock de son agence, avec le nom et le SKU de chaque produit ;
- ajouter ou retirer une quantité d'un produit ;
- consulter la quantité disponible d'un produit.

**Avec le compte `admin`** :

- voir la liste des utilisateurs ;
- créer un utilisateur standard et l'attribuer à une agence ;
- changer le mot de passe ou l'agence d'un utilisateur standard ;
- désactiver un utilisateur (il ne peut plus se connecter).

L'admin ne gère pas le stock, et un utilisateur standard n'a pas accès à la gestion des utilisateurs.
La liste complète des routes est dans `backoffice/README.md`.

## Utiliser le Client Web

L'interface publique permet :

- De saisir une question en langage naturel.
- D'envoyer la question à l'AI Query Service.
- D'afficher la réponse de l'assistant.
- D'afficher un message d'attente pendant le traitement.
- De désactiver temporairement le bouton d'envoi.
- D'afficher un message clair en cas d'indisponibilité du service.
- De s'adapter aux écrans mobiles.

Le thème graphique utilisé est **Midnight Tech**, avec une palette bleu nuit et cyan. Le Backoffice reprend le même thème.

### Exemples de questions

**Consultation du catalogue**

> Quels produits sont disponibles dans le catalogue ?

L'assistant présente le catalogue et distingue les produits non arrêtés des produits arrêtés.

**Caractéristiques d'un produit**

> Donne-moi les caractéristiques du produit HB-SEC-1402.

L'assistant retourne notamment le nom, la catégorie, la marque, le prix, le poids et le fournisseur.

**Stock d'un produit dans les agences**

> Quel est le stock du produit 34 dans toutes les agences ?

L'assistant consulte les quantités disponibles dans les différentes agences.

**Stock d'une agence**

> Quels produits sont disponibles dans l'agence de Paris et en quelles quantités ?

L'assistant identifie l'agence et présente les produits avec leurs quantités.

**Recommandation d'équipements**

> Je prépare une salle informatique pour 10 étudiants. Quels produits du catalogue me recommandes-tu pour équiper cette salle ?

L'assistant propose une liste d'équipements, les quantités recommandées et les prix du catalogue.
Les recommandations ne constituent pas une confirmation des stocks disponibles.

### Gestion des erreurs du Client Web

- Vérification d'une question vide.
- Vérification du statut HTTP de la réponse.
- Vérification de la présence d'une réponse valide.
- Affichage d'un message d'erreur si le service IA est inaccessible.
- Réactivation du bouton après le traitement, même en cas d'erreur.

Un test a été effectué en arrêtant volontairement l'AI Query Service. Message affiché :

> Impossible de contacter l'assistant. Veuillez réessayer.

## Principales décisions techniques

Le détail et les justifications sont dans `docs/decisions.md` et `docs/auth.md`.

- **Mots de passe hachés avec Argon2id**, jamais stockés en clair ni renvoyés dans une réponse. Argon2id est lent volontairement et utilise beaucoup de mémoire, ce qui rend les attaques par force brute coûteuses.
- **Session dans un cookie signé** (`SECRET_KEY`), qui ne contient que l'identifiant de l'utilisateur. Le cookie est `HttpOnly` et `SameSite=Lax`, ce qui limite le vol par JavaScript et les attaques CSRF.
- **Autorisations vérifiées dans le backend** par deux décorateurs, `login_required` et `role_required`. L'interface masque des sections, mais c'est le serveur qui décide.
- **L'agence vient toujours de l'utilisateur connecté**, jamais de la requête : un utilisateur ne peut pas agir sur une autre agence.
- **Retrait de stock atomique** : une seule requête `UPDATE ... WHERE available_quantity >= quantité`. Deux retraits simultanés ne peuvent pas rendre le stock négatif. Une contrainte `CHECK` en base sert de filet de sécurité.
- **Suppression douce** des utilisateurs (`is_active = false`) : l'historique reste cohérent et le compte ne peut plus se connecter.
- **Pas de copie des produits en base** : la base ne stocke que l'identifiant du produit. Les détails viennent de la Product API, avec un mode dégradé si elle est indisponible.
- **L'agent IA passe uniquement par le serveur MCP**, avec des outils en lecture seule : il ne peut ni modifier les données ni accéder directement à la base.
- **Secrets dans des variables d'environnement** (`.env` non commités, `.env.example` avec des valeurs fictives).

## Limites connues

- Les services se lancent séparément, chacun dans son terminal : il n'y a pas de `docker compose` commun à tout le projet.
- Le Backoffice tourne en HTTP en développement (`COOKIE_SECURE=0`). En production, il faudrait du HTTPS et `COOKIE_SECURE=1`.
- Le catalogue est récupéré en une seule requête de 100 produits maximum, sans pagination. C'est suffisant pour les 40 produits actuels.
- Il n'y a pas d'historique des mouvements de stock : seule la quantité actuelle est connue.
- Les réponses de l'IA dépendent de la disponibilité de l'API OpenAI, et chaque question a un coût.
- Le Backoffice est testé manuellement (`docs/tests.md`) ; seuls les outils du serveur MCP ont des tests automatisés.
- Si `SECRET_KEY` change au redémarrage, les utilisateurs connectés doivent se reconnecter.

## Fonctionnalités optionnelles réalisées

- Interface web complète pour le Backoffice (en plus de l'API REST), avec le même thème que le Client Web.
- Recommandations d'équipement par l'assistant IA à partir du catalogue.
- Mode dégradé du Backoffice lorsque la Product API est indisponible.

## Tests

Les preuves de tests sont dans `docs/tests.md` :

- les scénarios critiques du Backoffice (stock, rôles, utilisateurs, Product API) ;
- les tests automatisés du serveur MCP (`pytest -v` depuis la racine) ;
- les scénarios de l'assistant IA et du Client Web, validés pendant l'intégration.

## Ports utilisés en développement local

| Service | Port |
|---|---:|
| Backoffice | 5000 |
| Product API | 5001 |
| AI Query Service | 5002 |
| Client Web | 5500 |
| HBntory MCP Server | 8000 |
| PostgreSQL | 5432 |

## Sécurité et accès aux données

- Le Client Web est public et ne nécessite pas d'authentification.
- Le Backoffice est réservé aux comptes connectés, avec deux rôles : `admin` et `common_user`.
- Les clés API et les mots de passe doivent rester dans les fichiers `.env`.
- Les fichiers `.env` ne doivent pas être publiés sur GitHub.
- L'agent IA utilise uniquement les outils autorisés du serveur MCP.
- Les outils de consultation des données sont en lecture seule pour l'agent IA.
- L'agent ne doit pas inventer une quantité lorsque les données de stock sont absentes.

## Dépôt

**Projet :** HBntory

**GitHub :** https://github.com/Bertrand33100/hbntory
