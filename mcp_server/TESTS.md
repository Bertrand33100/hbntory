# Tests — Product MCP Server

## 1. Objectif

Vérifier que le serveur MCP communique correctement avec la Product API externe et gère les erreurs.

## 2. Tests automatisés

Commande utilisée :

`PYTHONPATH=mcp_server pytest -v mcp_server/tests/`

Résultat : 6 tests réussis.

| Test | Résultat |
|---|---|
| test_list_products_success | PASS |
| test_get_product_success | PASS |
| test_get_product_not_found | PASS |
| test_list_products_connection_error | PASS |
| test_list_products_timeout | PASS |
| test_list_products_server_error | PASS |

## 3. Tests manuels

| Vérification | Résultat |
|---|---|
| Liste réelle des produits | 40 produits récupérés |
| Récupération par ID | Réussie |
| Récupération par SKU | Réussie |
| Produit inexistant (999999) | HTTP 404 intercepté |
| Product API inaccessible | Erreur de connexion interceptée |
| Dépassement du délai | Timeout intercepté |
| Erreur serveur simulée | HTTP 503 intercepté |
| Initialisation MCP | Réussie |
| Découverte des outils | Deux outils exposés |
| Appel de list_products via MCP | Réussi |
| Appel de get_product via MCP | Réussi |

## 4. Gestion des erreurs

- HTTP 404 : produit introuvable.
- Autres erreurs HTTP : code HTTP retourné.
- Erreur de connexion : impossibilité de contacter la Product API.
- Timeout : délai d'attente dépassé.

## 5. Outils MCP exposés

- `list_products` : récupère la liste des produits.
- `get_product` : récupère les détails d'un produit à partir de son ID ou de son SKU.

Les données du catalogue ne sont pas enregistrées dans la base de données locale.

## 6. Conclusion

Les deux outils MCP ont été implémentés et testés.

Les six tests automatisés passent. Les vérifications manuelles de communication avec la Product API et le protocole MCP ont également été réalisées.
