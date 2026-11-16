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

**Bénéfice principal :** accès contrôlé. L'IA ne peut exécuter que les requêtes prévues dans nos outils, en lecture seule. Un seul serveur MCP à développer, déployer et maintenir.

**Limite principale :** plus de code à écrire qu'avec un outil existant, et l'IA est limitée aux questions prévues par nos outils. Ils doivent donc couvrir les questions d'exemple du sujet.

**Alternatives écartées :**
- **MCP Toolbox for Databases** (MCP tiers) : outil standard, configurable en YAML avec des requêtes prédéfinies. Écarté car il ajoute un service et un outil à apprendre, et l'agent devrait se connecter à deux serveurs MCP.
- **Un second serveur MCP dédié au stock** : meilleure séparation des responsabilités, et accès à la base limité au seul composant qui en a besoin. Écarté pour limiter le nombre de services à développer et à déployer.
- **Une fonction interne au service AI Query (« Stock Query »)** qui lit directement PostgreSQL en lecture seule : autorisée par la section « AI Query Service » du sujet (« depuis la base relationnelle ou via une intégration MCP »). Écartée pour rester dans les deux options proposées par la section « MCP Requirements », et pour que le service IA n'ait aucun accès direct à la base : toutes les données passent par les outils MCP.

---

## Autres choix techniques

| Sujet | Choix | Raison |
| --- | --- | --- |
| Base de données | PostgreSQL | Base relationnelle robuste, disponible en conteneur Docker |
| Accès à la base | SQLAlchemy | Imposé par le sujet pour le Backoffice |
| Hachage des mots de passe | À définir (tâche 2) | Sera choisi et justifié avec l'authentification |
