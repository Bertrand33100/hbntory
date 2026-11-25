# HBntory — Plan et preuves de tests

Ce document rassemble les scénarios de validation du Backoffice, les vérifications complémentaires et les essais d'intégration de l'AI Query Service et du Client Web.

> **Statut des preuves :** les résultats des scénarios Backoffice, IA et Client Web sont repris des documents du projet et des validations d'intégration consignées. La section 3 contient la sortie réelle de l'exécution de la suite de tests MCP effectuée le 25 novembre 2026.

## 1. Backoffice — 9 scénarios fonctionnels de la consigne

Les neuf scénarios couvrent les principales fonctions décrites dans le périmètre du MVP, l'authentification et le README du Backoffice.

| N° | Rôle | Scénario | Résultat attendu | Résultat documenté |
|---:|---|---|---|---|
| 1 | Admin et utilisateur standard | Se connecter avec des identifiants valides | Connexion acceptée et session ouverte avec le rôle correspondant | Validé dans `docs/auth.md` |
| 2 | Admin | Consulter la liste des utilisateurs | Liste retournée avec rôle, agence et état du compte ; aucun haché de mot de passe exposé | Route et contrôle documentés |
| 3 | Admin | Créer un utilisateur standard et l'affecter à une agence | Utilisateur créé avec le rôle `common_user` et l'agence demandée | Création documentée dans `backoffice/README.md` |
| 4 | Admin | Modifier le mot de passe d'un utilisateur standard | Nouveau mot de passe accepté ; ancien mot de passe refusé | Validé : ancien refusé (401), nouveau accepté (200) |
| 5 | Admin | Modifier l'agence d'un utilisateur standard | L'utilisateur consulte ensuite le stock de sa nouvelle agence | Validé dans `backoffice/README.md` |
| 6 | Admin | Désactiver un utilisateur standard | Compte désactivé ; nouvelle connexion refusée ; stock conservé | Validé : connexion refusée (401) |
| 7 | Utilisateur standard | Consulter le stock de son agence | Seules les quantités de l'agence liée au compte sont retournées | Validé dans `docs/auth.md` |
| 8 | Utilisateur standard | Ajouter du stock | Quantité ajoutée à l'agence de l'utilisateur et quantité finale retournée | Ajout normal documenté : 200 |
| 9 | Utilisateur standard | Retirer du stock | Retrait accepté si le stock est suffisant ; le stock ne devient jamais négatif | Retrait normal et insuffisant documentés : 200 / 409 |

## 2. Backoffice — 9 scénarios supplémentaires

Ces scénarios complètent les fonctions principales avec des cas limites et des contrôles de sécurité. Les codes HTTP sont ceux consignés dans le README du Backoffice et dans `docs/auth.md`.

| N° | Scénario complémentaire | Résultat attendu / documenté | État |
|---:|---|---|---|
| 1 | Création d'un utilisateur avec un nom déjà utilisé | `409 Conflict` | Validé |
| 2 | Création ou réaffectation avec un identifiant d'agence inconnu | `400 Bad Request` | Validé |
| 3 | Changement de mot de passe : essai avec l'ancien puis le nouveau | Ancien refusé (`401`), nouveau accepté (`200`) | Validé |
| 4 | Changement d'agence d'un utilisateur | Le stock affiché correspond à la nouvelle agence | Validé |
| 5 | Désactivation d'un utilisateur standard et tentative de désactivation de l'admin | Connexion de l'utilisateur désactivé refusée (`401`) ; désactivation de l'admin refusée (`400`) | Validé |
| 6 | Ajout d'un produit déjà présent ou absent du stock de l'agence | Ajout accepté dans les deux cas (`200`) | Validé |
| 7 | Ajout avec quantité négative ou identifiant de produit absent du catalogue | Quantité invalide refusée (`400`) ; produit inconnu refusé (`404`) | Validé |
| 8 | Retrait normal, retrait supérieur au stock ou retrait d'un produit absent | Retrait normal accepté (`200`) ; stock insuffisant refusé (`409`) | Validé |
| 9 | Indisponibilité de la Product API pendant la consultation et la gestion du stock | Stock consultable sans noms ; catalogue et ajout refusés avec `503` | Validé |

### Contrôles d'autorisation supplémentaires

- Un utilisateur non connecté ne peut pas consulter `GET /api/me` : `401`.
- Un utilisateur `common_user` ne peut pas consulter la liste des utilisateurs : `403`.
- Un administrateur ne peut pas consulter le stock : `403`.
- Les routes contrôlent le rôle et l'agence côté backend. Le masquage d'un bouton dans l'interface ne constitue pas une mesure de sécurité.

## 3. Serveur MCP — tests automatisés

### Commande exécutée

Depuis la racine du dépôt, avec l'environnement virtuel du serveur MCP :

```bash
PYTHONPATH=mcp_server mcp_server/venv/bin/python -m pytest -v mcp_server/tests/
```

La suite automatisée est définie dans `mcp_server/tests/test_server.py`.

Elle couvre les groupes de tests suivants :

| Domaine | Cas couverts |
|---|---|
| Product API | Liste des produits ; détail d'un produit ; produit inexistant ; erreur de connexion ; dépassement du délai ; erreur HTTP serveur |
| Stock par produit | Résultat dans plusieurs agences ; absence de stock ; identifiants invalides (0, négatif, chaîne, booléen) ; erreur PostgreSQL |
| Stock par agence | Résultat avec produits ; agence inexistante ; identifiants invalides (0, négatif, chaîne, booléen) ; erreur PostgreSQL |

### Sortie réelle de `pytest -v`

**Résultat de l'exécution du 25 novembre 2026 : 20 tests réussis, aucun échec, en 1,14 seconde.**

```text
=========================================================================== test session starts ===========================================================================
platform linux -- Python 3.14.4, pytest-9.2.0, pluggy-1.7.0 -- /home/kheang/projects/hbntory/mcp_server/venv/bin/python
cachedir: .pytest_cache
rootdir: /home/kheang/projects/hbntory
configfile: pytest.ini
plugins: asyncio-1.5.0, platformdirs-4.16.0, anyio-4.16.0
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
mcp_server/tests/test_server.py::test_get_stock_by_product_invalid_id[12] PASSED                                                                                     [ 55%]
mcp_server/tests/test_server.py::test_get_stock_by_product_invalid_id[True] PASSED                                                                                  [ 60%]
mcp_server/tests/test_server.py::test_get_stock_by_product_database_error PASSED                                                                                    [ 65%]
mcp_server/tests/test_server.py::test_get_stock_by_branch_success PASSED                                                                                            [ 70%]
mcp_server/tests/test_server.py::test_get_stock_by_branch_not_found PASSED                                                                                          [ 75%]
mcp_server/tests/test_server.py::test_get_stock_by_branch_invalid_id[0] PASSED                                                                                      [ 80%]
mcp_server/tests/test_server.py::test_get_stock_by_branch_invalid_id[-1] PASSED                                                                                     [ 85%]
mcp_server/tests/test_server.py::test_get_stock_by_branch_invalid_id[1] PASSED                                                                                      [ 90%]
mcp_server/tests/test_server.py::test_get_stock_by_branch_invalid_id[True] PASSED                                                                                    [ 95%]
mcp_server/tests/test_server.py::test_get_stock_by_branch_database_error PASSED                                                                                     [100%]

=========================================================================== 20 passed in 1.14s ============================================================================
```

## 4. Intégration — AI Query Service et Client Web

Les scénarios suivants reprennent les exemples d'utilisation et les validations d'intégration consignés dans le README du projet, ainsi que le comportement du code de l'agent et du Client Web.

| N° | Composant | Scénario | Résultat attendu / documenté | État documentaire |
|---:|---|---|---|---|
| 1 | Client Web → AI Query Service | Envoyer une question en langage naturel | La question est transmise à `POST /ask` et la réponse de l'assistant est affichée | Intégration documentée |
| 2 | IA → MCP → Product API | Demander la liste des produits du catalogue | L'assistant présente le catalogue et distingue les produits arrêtés | Exemple documenté dans le README |
| 3 | IA → MCP → Product API | Demander les caractéristiques d'un produit par SKU, par exemple `HB-SEC-1402` | Les caractéristiques fournies par la Product API sont restituées | Exemple documenté dans le README |
| 4 | IA → MCP → PostgreSQL | Demander le stock d'un produit dans toutes les agences | Les quantités sont présentées par agence | Exemple documenté dans le README |
| 5 | IA → MCP → PostgreSQL | Demander les produits disponibles dans une agence, par exemple Paris | L'agent retrouve l'identifiant avec `list_branches`, puis consulte le stock de l'agence | Scénario décrit dans les instructions de l'agent |
| 6 | IA → MCP → Product API et PostgreSQL | Demander une recommandation d'équipement pour une salle informatique | Recommandations fondées sur le catalogue ; elles ne sont pas présentées comme une réservation ni comme une confirmation de stock | Exemple documenté dans le README |
| 7 | Client Web | Envoyer une question vide | Message demandant de saisir une question ; aucune requête n'est envoyée | Contrôle présent dans `client_web/js/app.js` |
| 8 | Client Web | Envoyer une question pendant le traitement | Indicateur de chargement affiché ; bouton et champ désactivés, puis réactivés après traitement | Comportement implémenté dans `client_web/js/app.js` |
| 9 | Client Web | Arrêter volontairement l'AI Query Service puis envoyer une question | Message : « Impossible de contacter l'assistant. Veuillez réessayer. » | Essai explicitement décrit dans le README |

### Règles de fiabilité des réponses IA

- Les informations de catalogue et de stock doivent provenir des outils MCP autorisés.
- Les outils accessibles à l'agent sont `list_products`, `get_product`, `list_branches`, `get_stock_by_product` et `get_stock_by_branch`.
- L'IA ne modifie pas le stock : les ajouts et retraits sont réservés au Backoffice.
- Une information absente, une quantité nulle et une erreur technique doivent rester distinguées.
- L'assistant ne doit pas inventer une quantité, une caractéristique, un prix ou une disponibilité.

## 5. Références

- [Périmètre du MVP](mvp.md)
- [Authentification et autorisation](auth.md)
- [Documentation du Backoffice](../backoffice/README.md)
- [Tests existants du serveur MCP](../mcp_server/TESTS.md)
- [Suite automatisée MCP](../mcp_server/tests/test_server.py)
- [README et scénarios d'intégration](../README.md)
