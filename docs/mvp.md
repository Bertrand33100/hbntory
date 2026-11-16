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
| Product MCP (« HBntory MCP Server ») | Interroger l'API Product externe : liste et détails des produits |
| AI Query Service | Traiter les questions en langage naturel avec un ou plusieurs agents IA |
| Client Web | Envoyer les questions et afficher les réponses |
| Backoffice | Gérer les utilisateurs et les stocks |
| PostgreSQL | Stocker les utilisateurs, les agences et les quantités de stock |

**Nos choix :**

- Le Product MCP est développé par notre équipe. Il permet d'interroger l'API Product externe pour obtenir la liste des produits et leurs détails.
- Le **Stock Query** est une fonction interne au service AI Query. Elle permet de consulter les quantités disponibles dans PostgreSQL en lecture seule.
- Le service AI Query peut donc interroger le Product MCP pour les informations produits et le Stock Query interne pour les informations de stock.
- La gestion et la modification des stocks restent exclusivement assurées par le Backoffice. Le Stock Query ne peut effectuer aucune modification dans la base de données.

**Alternatives envisagées et écartées :**

- **Un serveur MCP séparé pour le stock** : cette solution aurait permis une séparation supplémentaire des responsabilités, mais aurait ajouté un service à développer et à déployer.
- **L'extension du Product MCP avec des outils de stock** : cette solution aurait regroupé les outils produits et stock dans un même serveur MCP. Elle n'a pas été retenue afin de conserver une séparation entre l'accès à l'API externe et l'accès aux données internes.

**Obligation du sujet :**

- Le système IA doit signaler clairement les informations indisponibles au lieu de les inventer.

---

## Nos décisions techniques

| Sujet | Décision |
| --- | --- |
| Backoffice | REST + HTML/CSS/JavaScript |
| Client Web ↔ AI Query Service | REST |
| AI Query Service ↔ Product MCP | MCP Streamable HTTP |
| Product MCP | Serveur développé par notre équipe, dédié aux informations produits |
| Stock Query | Fonction interne au service AI Query, accès PostgreSQL en lecture seule |
| Base de données | PostgreSQL |
| Accès à la base du Backoffice | SQLAlchemy |
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
| 1 | Base de données : tables `users`, `branches`, `stock` + création de l'admin au démarrage | Product MCP : outils produits (`list_products`, `get_product`) |
| 2 | Authentification et contrôle des rôles | Stock Query interne : fonctions de consultation du stock en lecture seule |
| 3 | Gestion des utilisateurs par l'admin | AI Query Service : agent IA + route REST de questions, connexion au Product MCP et au Stock Query |
| 4 | Gestion du stock par les utilisateurs standards | Client Web |
| 5 | **Ensemble :** intégration complète dans `docker-compose` et test des questions d'exemple du sujet | |

**Justification de l'ordre**

- **Étape 0 en premier :** le format de `product_id` fourni par la Product API détermine le type de la colonne dans la table `stock`.
- **Base de données avant tout le Backoffice :** toutes les fonctionnalités lisent ou écrivent dans la base.
- **Authentification avant les fonctionnalités :** chaque action doit savoir qui fait la demande (rôle, agence) pour appliquer les règles d'accès.
- **Gestion des utilisateurs avant le stock :** il faut un utilisateur standard affecté à une agence pour tester la gestion du stock.
- **Product MCP avant AI Query :** le service IA doit pouvoir interroger les informations produits.
- **Stock Query après la base de données :** la structure de la table `stock` doit être disponible pour permettre les consultations.
- **Client Web en dernier :** il dépend de la route REST de l'AI Query Service.

**Points de rencontre entre les pistes**

- **B2 dépend de A1 :** le schéma de la table `stock` doit être défini et la base disponible.
- **B3 dépend de B1 et B2 :** le service AI Query doit pouvoir accéder aux informations produits et aux informations de stock.
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
