# HBntory — Périmètre du MVP

Ce document distingue les **obligations du sujet** et **nos choix techniques**, afin de ne pas ajouter de fausses exigences.

---

## 1. Backoffice

### Administrateur (`admin`)

Le sujet prévoit un seul administrateur. Il est créé au démarrage de l'application, car aucune fonctionnalité ne permet de créer un autre administrateur.

Il doit pouvoir :

- Consulter la liste des utilisateurs.
- Créer des utilisateurs standards.
- Affecter un utilisateur à une agence.
- Modifier un utilisateur.
- Désactiver un utilisateur (soft delete).
- Modifier le mot de passe d'un utilisateur.
- Modifier l'agence d'un utilisateur.

Il ne doit pas gérer les stocks.

### Utilisateur standard (`common_user`)

Chaque utilisateur standard doit être affecté à exactement une agence.

Il doit pouvoir :

- Ajouter du stock.
- Retirer du stock.
- Consulter le stock.
- Lister les produits actuellement en stock dans son agence.

Il ne doit pas pouvoir gérer les utilisateurs ni intervenir sur les stocks d'une autre agence.

**Notre choix complémentaire :**

- Un utilisateur désactivé (soft delete) reste en base mais ne peut plus se connecter.

---

## 2. Gestion des stocks

La base de données doit enregistrer :

| Donnée | Description |
| --- | --- |
| `branch_id` | Identifiant de l'agence |
| `product_id` | Identifiant du produit dans l'API externe |
| `available_quantity` | Quantité disponible |

**Règles obligatoires :**

- Une quantité en stock ne peut jamais être négative.
- Les ajouts et retraits doivent être validés.

**Nos choix complémentaires :**

- Quantité demandée pour un ajout ou un retrait : entier strictement positif.
- Quantité en stock : entier supérieur ou égal à 0.
- Refus d'un retrait supérieur au stock disponible.
- Une seule ligne de stock par couple (`branch_id`, `product_id`).

---

## 3. Produits

Les informations des produits doivent provenir de l'API externe.

La base locale ne doit pas enregistrer :

- Les noms.
- Les descriptions.
- Les prix.
- Les images.
- Les métadonnées.

Seul l'identifiant du produit peut être enregistré pour faire le lien avec le stock.

---

## 4. Authentification et sécurité

**Obligations du sujet :**

- Connexion obligatoire au Backoffice.
- Contrôle des permissions dans le backend (pas seulement dans l'interface).
- Mots de passe hachés, jamais stockés en clair.
- Explication du mécanisme de hachage, de l'authentification et de la gestion des rôles.

Le SSL/TLS n'est pas obligatoire pour ce projet.

**Notre choix :**

- Hachage des mots de passe avec **Argon2id** : algorithme récent, conçu pour les mots de passe, avec sel intégré, et volontairement coûteux en temps et en mémoire pour résister aux attaques par force brute. (À valider.)

---

## 5. Client Web public

Une page Web accessible sans compte doit permettre aux clients de poser des questions en langage naturel.

Exemples prévus dans le sujet :

- Dans quelle agence trouver un produit ?
- Quels produits sont disponibles dans une agence ?
- Dans quelle(s) agence(s) trouver plusieurs produits en quantités données ?
- Quelles sont les caractéristiques d'un produit ?

Aucun historique de conversation n'est obligatoire. Chaque question est indépendante.

---

## 6. Service IA et serveurs MCP

**Composants obligatoires :**

| Composant | Responsabilité |
| --- | --- |
| Product MCP (« HBntory MCP Server ») | Interroger l'API Product externe : liste et détails des produits |
| AI Query Service | Traiter les questions en langage naturel avec un ou plusieurs agents IA |
| Client Web | Envoyer les questions et afficher les réponses |
| Backoffice | Gérer les utilisateurs et les stocks |
| PostgreSQL | Stocker les utilisateurs, les agences et les quantités de stock |

**Notre choix :**

- Nous **étendons notre propre serveur MCP** avec des outils de stock en lecture seule, pour permettre au service IA de consulter les stocks. C'est l'une des deux options proposées par le sujet. Un seul serveur MCP expose donc deux familles d'outils : produits (via l'API externe) et stock (via la base de données).
- Alternative envisagée : un serveur MCP séparé pour le stock (meilleure séparation des responsabilités, accès à la base limité à un seul composant). Écartée pour limiter le nombre de services à développer et à déployer.

**Obligation du sujet :**

- Le système IA doit signaler clairement les informations indisponibles au lieu de les inventer.

---

## Nos décisions techniques

| Sujet | Décision |
| --- | --- |
| Backoffice | REST + HTML/CSS/JavaScript |
| Client Web ↔ AI Query Service | REST |
| AI Query Service ↔ MCP | Streamable HTTP |
| Serveur MCP | Un seul serveur développé par notre équipe : outils produits + outils de stock (lecture seule) |
| Base de données | PostgreSQL |
| Accès à la base | SQLAlchemy |
| Hachage des mots de passe | Argon2id (à valider) |

---

## Priorisation

### Liste 1 — À implémenter en premier

Toutes les obligations ci-dessus (sections 1 à 6).

**Ordre d'implémentation**

L'ordre suit les dépendances entre composants : on construit d'abord ce dont les autres ont besoin. Les deux pistes avancent en parallèle.

| Étape | Piste A — Backoffice | Piste B — IA |
| --- | --- | --- |
| 0 | **Ensemble :** lancer la Product API (Docker), tester ses routes, noter le format des produits et des identifiants | |
| 1 | Base de données : tables `users`, `branches`, `stock` + création de l'admin au démarrage | Serveur MCP : outils produits (`list_products`, `get_product`) |
| 2 | Authentification et contrôle des rôles | Serveur MCP : outils stock (`get_stock_by_product`, `get_stock_by_branch`) |
| 3 | Gestion des utilisateurs par l'admin | AI Query Service : agent IA + route REST de questions |
| 4 | Gestion du stock par les utilisateurs standards | Client Web |
| 5 | **Ensemble :** intégration complète dans `docker-compose` et test des questions d'exemple du sujet | |

**Justification de l'ordre**

- **Étape 0 en premier :** le format de `product_id` fourni par la Product API détermine le type de la colonne dans la table `stock`.
- **Base de données avant tout le Backoffice :** toutes les fonctionnalités lisent ou écrivent dans la base.
- **Authentification avant les fonctionnalités :** chaque action doit savoir qui fait la demande (rôle, agence) pour appliquer les règles d'accès.
- **Gestion des utilisateurs avant le stock :** il faut un utilisateur standard affecté à une agence pour tester la gestion du stock.
- **Outils produits avant outils stock :** ils ne dépendent que de la Product API, déjà disponible.
- **Client Web en dernier :** il dépend de la route de l'AI Query Service.

**Points de rencontre entre les pistes**

- **B2 dépend de A1 :** le schéma de la table `stock` doit être figé et la base disponible.
- **Étape 5 :** les deux pistes sont branchées ensemble.

**Méthode dans chaque étape du Backoffice**

Pour chaque fonctionnalité : d'abord les routes de l'API REST, testées seules (`curl` ou Postman), puis l'interface JavaScript qui les appelle.

### Liste 2 — Pour plus tard

*À compléter.*

### Liste 3 — Seulement si le temps le permet

*À compléter.*
