# Backoffice : fonctionnalités et approche interface / backend

## 1. Approche choisie : API REST + interface HTML/CSS/JS

Le Backoffice est une **API REST** écrite avec Flask, accompagnée d'une **interface légère
en HTML, CSS et JavaScript**, sans framework.

- Flask sert la page (`GET /` → `backoffice/static/index.html`) **et** les routes de l'API (`/api/...`).
  La page et l'API ayant la même origine, le navigateur envoie automatiquement le cookie de session.
- Le JavaScript (`static/app.js`) lit les formulaires, appelle les routes avec `fetch` en JSON,
  puis affiche les réponses. Les données sont affichées avec `textContent`, jamais interprétées comme du HTML.
- Le style reprend le thème « Midnight Tech » du client web, pour une identité visuelle commune.

**Pourquoi ce choix plutôt que le rendu côté serveur (SSR) ?**
Les mêmes routes JSON servent à l'interface et aux tests (`curl`), et la logique reste entièrement
dans le backend : l'interface ne fait qu'afficher et envoyer des demandes.

**Toutes les règles sont appliquées par le backend.** L'interface masque les sections selon le rôle,
mais chaque route vérifie elle-même la connexion, le rôle et l'agence (voir `docs/auth.md`).

## 2. Routes du Backoffice

| Méthode et route | Rôle requis | Ce qu'elle fait |
| --- | --- | --- |
| `POST /api/login` | — | Connexion, ouverture de la session |
| `POST /api/logout` | — | Déconnexion |
| `GET /api/me` | connecté | Utilisateur connecté (rôle, agence) |
| `GET /api/branches` | connecté | Liste des agences |
| `GET /api/users` | admin | Liste des utilisateurs |
| `POST /api/users` | admin | Crée un utilisateur standard et l'attribue à une agence |
| `PUT /api/users/<id>/password` | admin | Change le mot de passe d'un utilisateur standard |
| `PUT /api/users/<id>/branch` | admin | Change l'agence d'un utilisateur standard |
| `DELETE /api/users/<id>` | admin | Désactive un utilisateur (suppression douce) |
| `GET /api/stock` | utilisateur standard | Stock de son agence (numéros et quantités) |
| `GET /api/stock/products` | utilisateur standard | Produits en stock de son agence, avec leurs détails (Product API) |
| `GET /api/stock/<product_id>` | utilisateur standard | Quantité d'un produit dans son agence |
| `POST /api/stock/add` | utilisateur standard | Ajoute du stock dans son agence |
| `POST /api/stock/remove` | utilisateur standard | Retire du stock de son agence (opération atomique) |
| `GET /api/products` | utilisateur standard | Catalogue de la Product API, pour le sélecteur de produits |

## 3. Règles métier

**Agence.** Les routes de stock lisent l'agence sur l'utilisateur connecté (`user.branch_id`),
jamais dans la requête : un utilisateur standard ne peut agir que sur son agence.

**Validation des quantités.** La quantité doit être un entier strictement positif (sinon 400).

**Stock jamais négatif.** Le retrait est une seule requête `UPDATE ... WHERE available_quantity >= quantité`.
Si aucune ligne n'est modifiée, le stock est insuffisant (409). L'ajout est fait par la base elle-même
(`available_quantity = available_quantity + quantité`). La contrainte `ck_stock_quantity_positive`
reste un filet de sécurité (voir `docs/database.md`).

**Gestion des utilisateurs.** L'admin ne crée que des utilisateurs standards (rôle imposé par le backend),
et ne peut ni modifier ni désactiver le compte admin. La suppression est douce (`is_active = false`) :
l'utilisateur ne peut plus se connecter, et le stock de l'agence n'est pas touché.

## 4. Intégration de la Product API

Les détails des produits (nom, SKU, état) viennent **uniquement** de la Product API.
La base ne stocke que l'identifiant numérique du produit.

- `fetch_products()` récupère le catalogue (`GET /api/v1/products`, produits arrêtés inclus),
  avec un délai maximal de 5 secondes, et le range par identifiant.
- **Sélecteur de produits** : `GET /api/products` remplit la liste déroulante de l'interface.
- **Vérification à l'ajout** : un produit absent du catalogue est refusé (404).
- **API indisponible** : la liste du stock reste affichée, sans les noms
  (`product_api_available: false`, message dans l'interface) ; le catalogue et l'ajout renvoient 503.
- L'adresse de l'API vient de la variable `PRODUCT_API_URL` (par défaut `http://localhost:5001`).

## 5. Tests effectués

| Test | Résultat |
| --- | --- |
| Création d'utilisateur / nom déjà pris / agence inconnue | 201 / 409 / 400 |
| Changement de mot de passe : ancien refusé, nouveau accepté | 401 / 200 |
| Changement d'agence, puis stock vu par l'utilisateur | celui de la nouvelle agence |
| Désactivation : connexion refusée ; désactivation de l'admin | 401 ; 400 |
| Ajout de stock : produit existant / nouveau / quantité négative / produit inconnu | 200 / 200 / 400 / 404 |
| Retrait : normal / quantité trop grande / produit absent | 200 / 409 / 409 |
| Produits en stock avec la Product API allumée / éteinte | noms affichés / `product_api_available: false` |
| Interface : connexion admin et utilisateur, chaque formulaire | fonctionnel |
