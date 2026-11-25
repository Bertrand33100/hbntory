# HBntory — Registre des décisions

Ce document justifie les décisions de communication demandées par le sujet, ainsi que le choix d'accès de l'IA au stock. Pour chaque décision : l'option retenue, son bénéfice principal, sa limite principale et l'alternative écartée.

Le sujet précise qu'il n'est pas attendu de choisir l'option la plus complexe, mais celle qui correspond aux exigences du projet et aux capacités de l'équipe. Nos choix suivent ce principe.

---

## 1. Backoffice : REST + HTML/CSS/JS

**Option retenue :** une API REST qui renvoie du JSON, et une interface HTML/CSS/JavaScript qui appelle cette API et construit l'affichage dans le navigateur.

**Bénéfice principal :** séparation claire entre l'interface et la logique métier. L'interface est plus fluide (pas de rechargement complet de la page après chaque action) et l'API peut être testée indépendamment de l'interface.

**Limite principale :** deux parties à écrire et à faire communiquer (l'API et le JavaScript), avec un contrat (routes, format JSON, codes d'erreur) à définir et à respecter des deux côtés.

**Alternative écartée :** le rendu côté serveur (SSR), plus simple à mettre en place, mais qui recharge la page à chaque action et ne sépare pas l'interface de la logique.

**Conséquences :**
- l'authentification reste gérée par une session et un cookie, l'interface et l'API étant servies par la même application ;
- les contrôles de rôles sont appliqués dans l'API, sur chaque route ;
- les erreurs (quantité insuffisante, accès refusé…) sont renvoyées en JSON avec le code HTTP adapté (400, 401, 403…).

---

## 2. Client Web ↔ AI Query Service : REST

**Option retenue :** chaque question est envoyée par une requête HTTP (`POST`), et la réponse complète revient dans la réponse HTTP.

**Bénéfice principal :** adapté au besoin, puisque chaque question est indépendante et qu'aucun historique de conversation n'est demandé. Simple à implémenter et à tester (navigateur, `curl`, Postman).

**Limite principale :** pas de réponse en streaming. Le visiteur attend la réponse complète de l'agent, qui peut prendre plusieurs secondes. Un indicateur « Recherche en cours… » est affiché pendant l'attente.

**Alternative écartée :** WebSocket, utile pour le streaming ou une conversation continue, mais qui ajoute la gestion d'une connexion permanente (ouverture, fermeture, déconnexions) sans besoin réel ici.

---

## 3. AI Query Service ↔ MCP : Streamable HTTP

**Option retenue :** le serveur MCP tourne dans son propre conteneur et expose une adresse HTTP. L'AI Query Service s'y connecte par le réseau Docker.

**Bénéfice principal :** le serveur MCP est un composant indépendant, testable seul (avec un inspecteur MCP) avant même que l'agent IA existe. C'est cohérent avec notre architecture, où chaque service a son conteneur.

**Limite principale :** un service de plus dans `docker-compose`, et une adresse à configurer entre l'AI Query Service et le serveur MCP.

**Alternative écartée :** stdio, où l'AI Query Service lance le serveur MCP comme un sous-processus. Plus simple à configurer, mais le MCP n'est plus un composant séparé et devient plus difficile à tester seul.

---

## 4. Accès de l'IA au stock : extension de notre propre serveur MCP

**Option retenue :** un seul serveur MCP, développé par l'équipe, qui expose deux familles d'outils en lecture seule :
- produits, via la Product API (`list_products`, `get_product`) ;
- stock, via la base de données (`get_stock_by_product`, `get_stock_by_branch`).

La modification des stocks reste exclusivement assurée par le Backoffice.

**Bénéfice principal :** c'est l'une des deux options explicitement proposées par la section « MCP Requirements » du sujet. L'IA a un point d'accès unique aux données : elle ne peut exécuter que les requêtes prévues dans nos outils, en lecture seule, et n'accède jamais directement à la base.

**Limite principale :** le serveur MCP regroupe deux responsabilités (appeler l'API externe et lire la base), et l'IA est limitée aux questions prévues par nos outils, qui doivent donc couvrir les questions d'exemple du sujet.

**Alternatives écartées :**
- **Une fonction interne au service AI Query (« Stock Query »)** lisant directement PostgreSQL : autorisée par la section « AI Query Service » du sujet (« depuis la base relationnelle ou via une intégration MCP »), et plus nette en séparation des responsabilités. Écartée pour rester dans les options de la section « MCP Requirements » et pour que le service IA n'ait aucun accès direct à la base.
- **Un second serveur MCP dédié au stock** : meilleure séparation, mais un service de plus à développer et à déployer.
- **MCP Toolbox for Databases** (MCP tiers) : outil standard configurable en YAML, mais un service et un outil de plus à apprendre, et l'agent devrait se connecter à deux serveurs MCP.

---

## 5. Framework du Backoffice : Flask

**Option retenue :** Flask, avec l'extension Flask-SQLAlchemy.

**Bénéfice principal :** framework simple et très répandu, déjà connu de l'équipe. Les routes, les réponses JSON et les sessions avec cookie (utilisées pour l'authentification) sont intégrées.

**Limite principale :** Flask est minimaliste : certaines fonctionnalités (validation automatique des données reçues, documentation de l'API) doivent être écrites à la main ou ajoutées par des extensions.

**Alternative écartée :** FastAPI, plus moderne et pensé pour les API (validation et documentation automatiques), mais moins connu de l'équipe, et moins direct pour la gestion des sessions avec cookie.

---

## 6. Création des tables : `db.create_all()` + script d'initialisation

**Option retenue :** les tables sont créées par `db.create_all()` à partir des modèles SQLAlchemy, puis un script d'initialisation (`backoffice/seed.py`) ajoute les données de départ : l'admin, au moins deux agences et du stock d'exemple.

**Bénéfice principal :** simple et rapide à mettre en place, et suffisant pour un schéma stable. Le sujet accepte explicitement « un script d'initialisation ou une stratégie de migration ». Le script est fiable : s'il a déjà été exécuté (l'admin existe), il ne modifie rien, et toutes les données sont enregistrées en une seule transaction (tout ou rien).

**Limite principale :** `create_all()` crée les tables manquantes mais ne modifie pas une table existante. Pour changer le schéma, il faut recréer la base de développement.

**Alternative écartée :** les migrations avec Alembic (Flask-Migrate), qui versionnent chaque évolution du schéma. Plus adaptées à une base en production qui évolue, mais une notion supplémentaire à apprendre pour un projet de deux semaines. Ce serait le choix à faire en production.

---

## 7. Hachage des mots de passe : Argon2id

**Option retenue :** Argon2id, avec la bibliothèque `argon2-cffi`.

**Bénéfice principal :** algorithme conçu pour le stockage des mots de passe et recommandé aujourd'hui. Il intègre un sel aléatoire (deux mots de passe identiques donnent deux hashs différents), et il est volontairement coûteux en temps et en mémoire, ce qui freine fortement les attaques par force brute.

**Limite principale :** une bibliothèque externe de plus, et un hachage volontairement lent (quelques dizaines de millisecondes par connexion), ce qui est négligeable pour un Backoffice interne.

**Alternative écartée :** le hachage intégré à Flask (`werkzeug.security`), sans dépendance supplémentaire, mais moins facile à justifier précisément.

---

## Autres choix techniques

| Sujet | Choix | Raison |
| --- | --- | --- |
| Base de données | PostgreSQL | Base relationnelle robuste, disponible en conteneur Docker, accessible par le Backoffice et le serveur MCP |
| Accès à la base | SQLAlchemy (via Flask-SQLAlchemy) | Imposé par le sujet pour le Backoffice |
| Identifiant produit stocké | `id` numérique de la Product API | Accepté directement par la route de détail ; détails dans `product-api.md` |
| Configuration sensible | Variables d'environnement (`DATABASE_URL`, mot de passe initial de l'admin, `PRODUCT_API_URL`) | Aucun mot de passe ni adresse sensible dans le code ou sur GitHub |
| Historique des mouvements de stock | Non implémenté dans le MVP (liste 2) | Mentionné par le contrat de la Product API, mais non exigé par le sujet |
