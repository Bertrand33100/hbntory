# Preuves de tests — HBntory

Ce document liste les scénarios critiques testés et leurs résultats.

- **Backoffice** : tests manuels avec `curl` sur `http://localhost:5000`.
- **Serveur MCP** : tests automatisés avec `pytest` (`mcp_server/tests/`).
- **Agent IA et Client Web** : tests manuels depuis l'interface.

## Préparation

Les commandes supposent que la base, la Product API et le Backoffice tournent,
et que la base a été remplie par le seed.

```bash
# Connexion utilisateur standard (cookie dans cookies.txt)
curl -s -c cookies.txt -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "common_user", "password": "<USER_PASSWORD>"}'

# Connexion admin (cookie dans cookies_admin.txt)
curl -s -c cookies_admin.txt -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "<ADMIN_PASSWORD>"}'
```

Les mots de passe sont ceux définis par `USER_PASSWORD` et `ADMIN_PASSWORD`
au moment du seed. Ils ne sont jamais écrits dans le dépôt.

## 1. Scénarios exigés par la consigne (Backoffice)

| # | Scénario | Commande | Attendu | Obtenu |
|---|---|---|---|---|
| 1 | Un utilisateur ajoute un stock valide | `POST /api/stock/add` `{"product_id": 34, "quantity": 2}` | 200, quantité 20 → 22 | ✅ |
| 2 | Un utilisateur retire un stock valide | `POST /api/stock/remove` `{"product_id": 34, "quantity": 2}` | 200, quantité diminuée de 2 | ✅ |
| 3 | Retrait supérieur au stock disponible | `POST /api/stock/remove` `{"product_id": 34, "quantity": 999}` | 409 « Stock insuffisant. », stock inchangé | ✅ |
| 4 | Pas d'action sur une autre agence | `POST /api/stock/add` `{"product_id": 34, "quantity": 1, "branch_id": 2}` | 200, l'ajout va dans l'agence de l'utilisateur : `branch_id` envoyé est ignoré | ✅ |
| 5 | L'admin crée un utilisateur standard | `POST /api/users` `{"username": "julie", "password": "...", "branch_id": 1}` (admin) | 201, rôle `common_user` | ✅ |
| 6 | L'admin désactive un utilisateur | `DELETE /api/users/<id>` (admin) | 200, `is_active` passe à `false` | ✅ |
| 7 | Un utilisateur désactivé ne peut plus se connecter | `POST /api/login` avec julie | 401 « Identifiants invalides. » | ✅ |
| 8 | L'admin ne peut pas gérer le stock | `POST /api/stock/add` (admin) | 403 « Accès interdit. » | ✅ |
| 9 | Les détails produits viennent de la Product API | `GET /api/stock/products` | noms et sku renvoyés, `product_api_available: true` | ✅ |

## 2. Scénarios supplémentaires (Backoffice)

| # | Scénario | Commande | Attendu | Obtenu |
|---|---|---|---|---|
| 10 | Accès sans être connecté | `GET /api/stock` sans cookie | 401 « Authentification requise. » | ✅ |
| 11 | Utilisateur standard sur une route admin | `GET /api/users` (common_user) | 403 « Accès interdit. » | ✅ |
| 12 | Quantité nulle ou négative | `POST /api/stock/add` `{"product_id": 34, "quantity": 0}` | 400 | ✅ |
| 13 | Quantité booléenne | `POST /api/stock/add` `{"product_id": 34, "quantity": true}` | 400 « Produit et quantité doivent être des entiers. » | ✅ |
| 14 | Produit inconnu de la Product API | `POST /api/stock/add` `{"product_id": 9999, "quantity": 1}` | 404 « Produit inconnu. » | ✅ |
| 15 | Ajout d'un produit pas encore en stock | `POST /api/stock/add` `{"product_id": 8, "quantity": 3}` | 200, ligne créée avec 3 | ✅ |
| 16 | Nom d'utilisateur déjà pris | `POST /api/users` avec un nom existant (admin) | 409 | ✅ |
| 17 | Product API arrêtée, consultation | `GET /api/stock/products` | 200, noms à `null`, `product_api_available: false` | ✅ |
| 18 | Product API arrêtée, ajout | `POST /api/stock/add` | 503 « Product API indisponible. » | ✅ |

Exemple de commande complète (scénario 3) :

```bash
curl -s -b cookies.txt -X POST http://localhost:5000/api/stock/remove \
  -H "Content-Type: application/json" \
  -d '{"product_id": 34, "quantity": 999}'
# {"error": "Stock insuffisant."}
```

### Garanties assurées par le code et la base

Certains cas sont difficiles à reproduire à la main. Ils sont garantis ainsi :

- **Deux retraits simultanés** : le retrait est une seule requête SQL
  (`UPDATE ... WHERE available_quantity >= quantité`). La base ne peut donc
  jamais passer sous zéro.
- **Deux ajouts simultanés d'un nouveau produit** : la contrainte unique
  `(branch_id, product_id)` refuse la deuxième ligne. La route rattrape
  l'`IntegrityError` et additionne la quantité sur la ligne existante.
- **Quantité négative en base** : la contrainte
  `CHECK (available_quantity >= 0)` l'interdit dans tous les cas.

## 3. Serveur MCP (tests automatisés)

```bash
pytest -v
```

_Sortie à coller par Bertrand._

## 4. Agent IA et Client Web

| # | Scénario | Question posée | Attendu | Obtenu |
|---|---|---|---|---|
| 19 | Où un produit est disponible | « Où trouver la Wireless Mouse ? » | les agences qui en ont, avec les quantités | ✅ |
| 20 | Produits disponibles dans une agence | « Quels produits sont disponibles à Paris ? » | la liste du stock de Paris | ✅ |
| 21 | Produit inconnu | « Où trouver le produit XYZ ? » | une réponse claire : produit inconnu | ✅ |
| 22 | Information indisponible | question posée avec la Product API arrêtée | une réponse claire : information indisponible | ✅ |
| 23 | Intégration complète | ajout de 5 souris dans le Backoffice, puis question au Client Web | l'IA cite les souris ajoutées | ✅ |
