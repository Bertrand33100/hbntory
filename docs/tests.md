# HBntory — Preuves de tests

Ce document rassemble les scénarios de validation du Backoffice, les tests automatisés du serveur MCP et les scénarios d'intégration de l'agent IA et du Client Web.

Les scénarios Backoffice et IA / Client Web ci-dessous reprennent les validations consignées pendant l'intégration du projet.

## Préparation

Les commandes supposent que PostgreSQL, la Product API et le Backoffice sont démarrés et que la base contient les données initialisées par le script seed.

### Connexion utilisateur standard

```bash
curl -s -c cookies.txt -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "common_user", "password": "<USER_PASSWORD>"}'
```

### Connexion administrateur

```bash
curl -s -c cookies_admin.txt -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "<ADMIN_PASSWORD>"}'
```

Les mots de passe sont ceux définis par `USER_PASSWORD` et `ADMIN_PASSWORD` au moment du seed. Ils ne sont pas enregistrés en clair dans le dépôt.

# 1. Scénarios exigés par la consigne — Backoffice

| N° | Scénario | Requête | Résultat attendu | Résultat obtenu |
|---:|---|---|---|---|
| 1 | Ajouter un stock valide | `POST /api/stock/add` avec `product_id: 34`, `quantity: 2` | HTTP 200, quantité de 20 à 22 | ✅ |
| 2 | Retirer un stock valide | `POST /api/stock/remove` avec `product_id: 34`, `quantity: 2` | HTTP 200, quantité diminuée de 2 | ✅ |
| 3 | Retrait supérieur au stock disponible | `POST /api/stock/remove` avec `product_id: 34`, `quantity: 999` | HTTP 409, « Stock insuffisant », stock inchangé | ✅ |
| 4 | Empêcher une action sur une autre agence | `POST /api/stock/add` avec `branch_id: 2` dans la requête | HTTP 200, ajout dans l'agence de l'utilisateur ; le `branch_id` fourni est ignoré | ✅ |
| 5 | Créer un utilisateur standard | `POST /api/users` avec le compte administrateur | HTTP 201, rôle `common_user` et agence attribuée | ✅ |
| 6 | Désactiver un utilisateur | `DELETE /api/users/<id>` avec le compte administrateur | HTTP 200, `is_active` passe à `false` | ✅ |
| 7 | Empêcher la connexion d'un utilisateur désactivé | `POST /api/login` avec le compte désactivé | HTTP 401, « Identifiants invalides » | ✅ |
| 8 | Empêcher l'administrateur de gérer le stock | `POST /api/stock/add` avec le compte administrateur | HTTP 403, « Accès interdit » | ✅ |
| 9 | Récupérer les détails des produits depuis la Product API | `GET /api/stock/products` | Noms et SKU retournés, `product_api_available: true` | ✅ |

# 2. Scénarios supplémentaires — Backoffice

| N° | Scénario | Requête | Résultat attendu | Résultat obtenu |
|---:|---|---|---|---|
| 10 | Accès sans authentification | `GET /api/stock` sans cookie | HTTP 401, authentification requise | ✅ |
| 11 | Utilisateur standard sur une route administrateur | `GET /api/users` avec `common_user` | HTTP 403, accès interdit | ✅ |
| 12 | Quantité nulle ou négative | `POST /api/stock/add` avec une quantité de 0 ou négative | HTTP 400 | ✅ |
| 13 | Quantité booléenne | `POST /api/stock/add` avec `quantity: true` | HTTP 400, les quantités doivent être des entiers | ✅ |
| 14 | Produit inconnu de la Product API | `POST /api/stock/add` avec `product_id: 9999` | HTTP 404, produit inconnu | ✅ |
| 15 | Ajout d'un produit absent du stock | `POST /api/stock/add` avec `product_id: 8`, `quantity: 3` | HTTP 200, création d'une ligne avec quantité 3 | ✅ |
| 16 | Nom d'utilisateur déjà utilisé | `POST /api/users` avec un nom existant | HTTP 409 | ✅ |
| 17 | Product API arrêtée pendant une consultation | `GET /api/stock/products` | HTTP 200, noms à `null`, `product_api_available: false` | ✅ |
| 18 | Product API arrêtée pendant un ajout | `POST /api/stock/add` | HTTP 503, Product API indisponible | ✅ |

### Exemple : retrait supérieur au stock

```bash
curl -s -b cookies.txt -X POST http://localhost:5000/api/stock/remove \
  -H "Content-Type: application/json" \
  -d '{"product_id": 34, "quantity": 999}'

# Résultat attendu :
# {"error": "Stock insuffisant."}
```

### Garanties complémentaires assurées par le code et la base

- **Deux retraits simultanés :** le retrait utilise une requête atomique `UPDATE ... WHERE available_quantity >= quantité`. La quantité ne peut pas devenir négative.
- **Deux ajouts simultanés d'un nouveau produit :** la contrainte unique sur `(branch_id, product_id)` empêche la création de deux lignes. La gestion de l'`IntegrityError` permet de reporter l'ajout sur la ligne existante.
- **Quantité négative en base :** la contrainte `CHECK (available_quantity >= 0)` protège également les données au niveau PostgreSQL.

# 3. Serveur MCP — tests automatisés

Les tests vérifient le fonctionnement des outils du serveur MCP (Model Context Protocol), les échanges avec la Product API et les consultations de stock dans PostgreSQL.

### Commande exécutée

Depuis la racine du dépôt :

```bash
PYTHONPATH=mcp_server mcp_server/venv/bin/python -m pytest -v mcp_server/tests/
```

### Résumé de l'exécution

- Date : 25 novembre 2026
- Python : 3.14.4
- Pytest : 9.2.0
- Tests collectés : 20
- Tests réussis : 20
- Échecs : 0
- Durée : 1,14 seconde

### Sortie réelle du terminal

La sortie suivante est celle de l'exécution effectuée dans l'environnement local du projet.

```text
=========================================================================== test session starts ===========================================================================
platform linux -- Python 3.14.4, pytest-9.2.0, pluggy-1.7.0 -- /home/kheang/projects/hbntory/mcp_server/venv/bin/python
cachedir: .pytest_cache
rootdir: /home/kheang/projects/hbntory
configfile: pytest.ini
plugins: asyncio-1.5.0, platformdirs-4.14.5, anyio-4.16.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 20 items

mcp_server/tests/test_server.py::test_list_products_success PASSED                                                                                                  [  5%]
mcp_server/tests/test_server.py::test_get_product_success PASSED                                                                                                    [ 10%]
mcp_server/tests/test_server.py::test_get_product_not_found PASSED                                                                                                  [ 15%]
mcp_server/tests/test_server.py::test_list_products_connection_error PASSED                                                                                         [ 20%]
mcp_server/tests/test_server.py::test_list_products_timeout PASSED                                                                                                  [ 25%]
mcp_server/tests/test_server.py::test_list_products_server_error PASSED                                                                                             [ 30%]
mcp_server/tests/test_server.py::test_get_stock_by_product_success PASSED                                                                                           [ 35%]
mcp_server/tests/test_server.py::test_get_stock_by_product_no_stock PASSED                                                                                          [ 40%]
mcp_server/tests/test_server.py::test_get_stock_by_product_invalid_id[0] PASSED                                                                                     [ 45%]
mcp_server/tests/test_server.py::test_get_stock_by_product_invalid_id[-1] PASSED                                                                                    [ 50%]
mcp_server/tests/test_server.py::test_get_stock_by_product_invalid_id[12] PASSED                                                                                    [ 55%]
mcp_server/tests/test_server.py::test_get_stock_by_product_invalid_id[True] PASSED                                                                                  [ 60%]
mcp_server/tests/test_server.py::test_get_stock_by_product_database_error PASSED                                                                                   [ 65%]
mcp_server/tests/test_server.py::test_get_stock_by_branch_success PASSED                                                                                            [ 70%]
mcp_server/tests/test_server.py::test_get_stock_by_branch_not_found PASSED                                                                                          [ 75%]
mcp_server/tests/test_server.py::test_get_stock_by_branch_invalid_id[0] PASSED                                                                                     [ 80%]
mcp_server/tests/test_server.py::test_get_stock_by_branch_invalid_id[-1] PASSED                                                                                    [ 85%]
mcp_server/tests/test_server.py::test_get_stock_by_branch_invalid_id[1] PASSED                                                                                     [ 90%]
mcp_server/tests/test_server.py::test_get_stock_by_branch_invalid_id[True] PASSED                                                                                   [ 95%]
mcp_server/tests/test_server.py::test_get_stock_by_branch_database_error PASSED                                                                                     [100%]

=========================================================================== 20 passed in 1.14s ============================================================================
```

### Couverture des tests MCP

| Domaine | Vérifications |
|---|---|
| Product API | Liste des produits, détail, produit inexistant, erreur de connexion, timeout et erreur HTTP 503 |
| Stock par produit | Consultation dans plusieurs agences, absence de stock, identifiants invalides et erreur PostgreSQL |
| Stock par agence | Consultation des produits, agence inexistante, identifiants invalides et erreur PostgreSQL |

La suite automatisée correspond au fichier `mcp_server/tests/test_server.py`.

# 4. Agent IA et Client Web — intégration

Les scénarios suivants ont été consignés comme validés pendant l'intégration du Client Web et de l'agent IA.

| N° | Scénario | Question ou action | Résultat attendu | Résultat obtenu |
|---:|---|---|---|---|
| 19 | Disponibilité d'un produit | « Où trouver la Wireless Mouse ? » | L'assistant indique les agences qui possèdent le produit et les quantités disponibles | ✅ |
| 20 | Produits disponibles dans une agence | « Quels produits sont disponibles à Paris ? » | L'assistant présente les produits et les quantités de l'agence de Paris | ✅ |
| 21 | Produit inconnu | « Où trouver le produit XYZ ? » | L'assistant indique clairement que le produit est inconnu | ✅ |
| 22 | Information indisponible | Poser une question lorsque la Product API est arrêtée | L'assistant indique que l'information est indisponible, sans inventer de quantité | ✅ |
| 23 | Intégration complète Backoffice et Client Web | Ajouter 5 souris dans le Backoffice, puis interroger le Client Web | L'assistant retrouve et cite les quantités actualisées | ✅ |

### Règles de fiabilité des réponses IA

- Les informations sur le catalogue et les stocks proviennent des outils MCP autorisés.
- L'agent utilise `list_products`, `get_product`, `list_branches`, `get_stock_by_product` et `get_stock_by_branch`.
- L'IA consulte les stocks mais ne les modifie pas.
- Les ajouts et retraits de stock sont exclusivement effectués depuis le Backoffice.
- Une donnée absente, une quantité égale à zéro et une erreur technique doivent être distinguées.
- L'assistant ne doit jamais inventer une quantité, un prix, une caractéristique ou une disponibilité.

# 5. Références

- [README du projet](../README.md)
- [Périmètre du MVP](mvp.md)
- [Authentification et autorisation](auth.md)
- [Documentation du Backoffice](../backoffice/README.md)
- [Documentation des tests MCP](../mcp_server/TESTS.md)
- [Suite automatisée MCP](../mcp_server/tests/test_server.py)
