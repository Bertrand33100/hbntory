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

- Hachage des mots de passe avec **Argon2id** : algorithme conçu pour les mots de passe, avec sel intégré et volontairement coûteux en temps et en mémoire pour résister aux attaques par force brute. (À valider.)

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
| HBntory MCP Server | Interroger l'API Product externe (liste et détails des produits) et consulter le stock en lecture seule |
| AI Query Service | Traiter les questions en langage naturel avec un ou plusieurs agents IA |
| Client Web | Envoyer les questions et afficher les réponses |
| Backoffice | Gérer les utilisateurs et les stocks |
| PostgreSQL | Stocker les utilisateurs, les agences et les quantités de stock |

**Nos choix :**

- Nous **étendons notre propre serveur MCP** (« HBntory MCP Server ») avec des outils de stock en lecture seule. C'est l'une des deux options proposées par la section « MCP Requirements » du sujet.
- Un seul serveur MCP expose donc deux familles d'outils :
  - **produits**, via l'API Product externe : `list_products`, `get_product` ;
  - **stock**, via PostgreSQL en lecture seule : `get_stock_by_product`, `get_stock_by_branch`.
- Le service AI Query n'accède jamais directement à la base : toutes les données passent par les outils MCP.
- La gestion et la modification des stocks restent exclusivement assurées par le Backoffice. Les outils de stock du MCP ne peuvent effectuer aucune modification.

**Alternatives envisagées et écartées :**

- **Un serveur MCP séparé pour le stock** : séparation supplémentaire des responsabilités, mais un service de plus à développer et à déployer.
- **Une fonction interne au service AI Query (« Stock Query »)** lisant directement PostgreSQL : autorisée par la section « AI Query Service » du sujet, mais écartée pour rester dans les options de la section « MCP Requirements » et pour que le service IA n'ait aucun accès direct à la base.

**Obligation du sujet :**

- Le système IA doit signaler clairement les informations indisponibles au lieu de les inventer.

---

## Nos décisions techniques

| Sujet | Décision |
| --- | --- |
| Backoffice | REST + HTML/CSS/JavaScript |
| Client Web ↔ AI Query Service | REST |
| AI Query Service ↔ MCP | MCP Streamable HTTP |
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
| 2 | Authentification et contrôle des rôles | Serveur MCP : outils stock en lecture seule (`get_stock_by_product`, `get_stock_by_branch`) |
| 3 | Gestion des utilisateurs par l'admin | AI Query Service : agent IA + route REST de questions, connexion au serveur MCP |
| 4 | Gestion du stock par les utilisateurs standards | Client Web |
| 5 | **Ensemble :** intégration complète dans `docker-compose` et test des questions d'exemple du sujet | |

**Justification de l'ordre**

- **Étape 0 en premier :** le format de `product_id` fourni par la Product API détermine le type de la colonne dans la table `stock`.
- **Base de données avant tout le Backoffice :** toutes les fonctionnalités lisent ou écrivent dans la base.
- **Authentification avant les fonctionnalités :** chaque action doit savoir qui fait la demande (rôle, agence) pour appliquer les règles d'accès.
- **Gestion des utilisateurs avant le stock :** il faut un utilisateur standard affecté à une agence pour tester la gestion du stock.
- **Outils produits avant outils stock :** ils ne dépendent que de la Product API, déjà disponible.
- **Outils stock après la base de données :** la structure de la table `stock` doit être disponible pour permettre les consultations.
- **Serveur MCP avant AI Query :** l'agent IA a besoin des outils produits et stock pour répondre.
- **Client Web en dernier :** il dépend de la route REST de l'AI Query Service.

**Points de rencontre entre les pistes**

- **B2 dépend de A1 :** le schéma de la table `stock` doit être défini et la base disponible.
- **B3 dépend de B1 et B2 :** l'agent IA doit disposer des outils produits et stock du serveur MCP.
- **Étape 5 :** les deux pistes sont intégrées et testées ensemble.

**Méthode dans chaque étape du Backoffice**

Pour chaque fonctionnalité : d'abord les routes de l'API REST, testées seules (`curl` ou Postman), puis l'interface JavaScript qui les appelle.

### Liste 2 — Améliorations possibles après le MVP

Ces fonctionnalités pourront être envisagées après la réalisation et la validation de toutes les obligations du sujet.

- **Historique des mouvements de stock :** conserver les entrées et sorties de stock avec la date, la quantité et l'utilisateur concerné.
- **Journal d'activité du Backoffice :** consulter les principales actions réalisées par les utilisateurs.
- **Recherche et filtres avancés :** faciliter la recherche d'utilisateurs, de produits et de stocks.
- **Tableau de bord administrateur :** afficher des indicateurs généraux sur les agences et les stocks.
- **Amélioration de l'interface :** améliorer l'ergonomie du Backoffice et la présentation des réponses du Client Web.

### Liste 3 — Seulement si le temps le permet

Ces fonctionnalités sont des bonus. Elles ne seront envisagées que si le MVP est entièrement terminé, fonctionnel et testé.

- **Historique des conversations du Client Web :** permettre de retrouver les questions précédemment posées.
- **Indicateurs visuels de disponibilité :** afficher plus clairement les niveaux de stock disponibles.
- **Notifications de stock faible :** signaler les produits dont la quantité passe sous un seuil défini.
- **Interface responsive :** améliorer l'utilisation du Backoffice et du Client Web sur mobile et tablette.
- **Tests automatisés complémentaires :** augmenter la couverture des tests au-delà des scénarios obligatoires.

**Règle de priorité :** aucune fonctionnalité des listes 2 et 3 ne doit retarder ou compromettre la réalisation des obligations de la liste 1.
