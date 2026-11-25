# HBntory — Plan et preuves de tests

Ce document rassemble les scénarios de validation du Backoffice, les vérifications complémentaires et les essais d'intégration de l'AI Query Service et du Client Web.

> **Statut des preuves :** les résultats présentés comme « documentés » sont repris des README et documents du dépôt sur la branche `develop`. Ils ne constituent pas une nouvelle exécution de tests réalisée lors de la rédaction de ce fichier. La sortie complète de `pytest -v` demandée en section 3 reste à coller depuis le terminal après exécution.

## 1. Backoffice — 9 scénarios fonctionnels de la consigne

Les neuf scénarios ci-dessous couvrent les fonctions principales décrites dans [le périmètre du MVP](mvp.md), [l'authentification](auth.md) et le [README du Backoffice](../backoffice/README.md).

| N° | Rôle | Scénario | Résultat attendu | Résultat documenté |
|---:|---|---|---|---|
| 1 | Admin et utilisateur standard | Se connecter avec des identifiants valides | Connexion acceptée et session ouverte avec le rôle correspondant | Validé dans `docs/auth.md` |
| 2 | Admin | Consulter la liste des utilisateurs | Liste retournée avec rôle, agence et état du compte ; aucun haché de mot de passe exposé | Route et contrôle documentés |
| 3 | Admin | Créer un utilisateur standard et l'affecter à une agence | Utilisateur créé avec le rôle `common_user` et l'agence demandée | Création et cas d'erreur documentés dans `backoffice/README.md` |
| 4 | Admin | Modifier le mot de passe d'un utilisateur standard | Nouveau mot de passe accepté ; ancien mot de passe refusé | Validé : ancien refusé (401), nouveau accepté (200) |
| 5 | Admin | Modifier l'agence d'un utilisateur standard | L'utilisateur consulte ensuite le stock de sa nouvelle agence | Validé dans `backoffice/README.md` |
| 6 | Admin | Désactiver un utilisateur standard | Compte désactivé ; nouvelle connexion refusée ; stock conservé | Validé : connexion refusée (401) |
| 7 | Utilisateur standard | Consulter le stock de son agence | Seules les quantités de l'agence liée au compte sont retournées | Validé dans `docs/auth.md` |
| 8 | Utilisateur standard | Ajouter du stock | Quantité ajoutée à l'agence de l'utilisateur et quantité finale retournée | Ajout normal documenté : 200 |
| 9 | Utilisateur standard | Retirer du stock | Retrait accepté si le stock est suffisant ; le stock ne devient jamais négatif | Retrait normal et insuffisant documentés : 200 / 409 |

## 2. Backoffice — 9 scénarios supplémentaires

Ces scénarios complètent les fonctions principales avec des cas limites et des contrôles de sécurité. Les codes HTTP sont ceux consignés dans le [README du Backoffice](../backoffice/README.md) et dans [docs/auth.md](auth.md).

| N° | Scénario complémentaire | Résultat attendu / documenté | État |
|---:|---|---|---|
| 1 | Création d'un utilisateur avec un nom déjà utilisé | `409 Conflict` | Validé dans le README Backoffice |
| 2 | Création ou réaffectation avec un identifiant d'agence inconnu | `400 Bad Request` | Validé dans le README Backoffice |
| 3 | Changement de mot de passe : essai avec l'ancien puis le nouveau | Ancien refusé (`401`), nouveau accepté (`200`) | Validé dans le README Backoffice |
| 4 | Changement d'agence d'un utilisateur | Le stock affiché correspond à la nouvelle agence | Validé dans le README Backoffice |
| 5 | Désactivation d'un utilisateur standard et tentative de désactivation de l'admin | Connexion de l'utilisateur désactivé refusée (`401`) ; désactivation de l'admin refusée (`400`) | Validé dans le README Backoffice |
| 6 | Ajout d'un produit déjà présent ou absent du stock de l'agence | Ajout accepté dans les deux cas (`200`) | Validé dans le README Backoffice |
| 7 | Ajout avec quantité négative ou identifiant de produit absent du catalogue | Quantité invalide refusée (`400`) ; produit inconnu refusé (`404`) | Validé dans le README Backoffice |
| 8 | Retrait normal, retrait supérieur au stock ou retrait d'un produit absent | Retrait normal accepté (`200`) ; stock insuffisant refusé (`409`) | Validé dans le README Backoffice |
| 9 | Indisponibilité de la Product API pendant la consultation et la gestion du stock | Stock consultable sans noms ; catalogue et ajout refusés avec `503` | Validé dans le README Backoffice |

### Contrôles d'autorisation supplémentaires

Les contrôles suivants sont également consignés dans [docs/auth.md](auth.md) :

- Un utilisateur non connecté ne peut pas consulter `GET /api/me` : `401`.
- Un utilisateur `common_user` ne peut pas consulter la liste des utilisateurs : `403`.
- Un administrateur ne peut pas consulter le stock : `403`.
- Les routes contrôlent le rôle et l'agence côté backend. Le masquage d'un bouton dans l'interface n'est pas considéré comme une mesure de sécurité.

## 3. Serveur MCP — tests automatisés

### Commande à exécuter

Depuis la racine du dépôt :

```bash
PYTHONPATH=mcp_server pytest -v mcp_server/tests/
```

La suite automatisée est définie dans [mcp_server/tests/test_server.py](../mcp_server/tests/test_server.py). Elle couvre les groupes suivants :

| Domaine | Cas couverts dans le code des tests |
|---|---|
| Product API | Liste des produits ; détail d'un produit ; produit inexistant ; erreur de connexion ; dépassement du délai ; erreur HTTP serveur |
| Stock par produit | Résultat dans plusieurs agences ; absence de stock ; identifiants invalides (0, négatif, chaîne, booléen) ; erreur PostgreSQL |
| Stock par agence | Résultat avec produits ; agence inexistante ; identifiants invalides (0, négatif, chaîne, booléen) ; erreur PostgreSQL |

Les cas paramétrés génèrent plusieurs tests distincts. Le nombre exact de tests exécutés doit être repris du résumé réel de `pytest`.

### Sortie réelle de `pytest -v`

**À compléter après exécution.** Coller ci-dessous la sortie intégrale du terminal, depuis la collecte des tests jusqu'au résumé final (`passed`, `failed`, durée). Ne pas reconstituer cette sortie à partir du nombre de scénarios ou d'une ancienne documentation.

```text
[EN ATTENTE DE LA SORTIE RÉELLE DE PYTEST -V]
```

## 4. Intégration — AI Query Service et Client Web

Les scénarios suivants sont repris des exemples d'utilisation et de la section sur la gestion des erreurs du [README du projet](../README.md), ainsi que du code de l'agent et du Client Web.

| N° | Composant | Scénario | Résultat attendu / documenté | État documentaire |
|---:|---|---|---|---|
| 1 | Client Web → AI Query Service | Envoyer une question en langage naturel | La question est transmise à `POST /ask` et la réponse de l'assistant est affichée | Intégration décrite dans le README |
| 2 | IA → MCP → Product API | Demander la liste des produits du catalogue | L'assistant présente le catalogue et distingue les produits arrêtés | Exemple documenté dans le README |
| 3 | IA → MCP → Product API | Demander les caractéristiques d'un produit par SKU, par exemple `HB-SEC-1402` | Les caractéristiques fournies par la Product API sont restituées | Exemple documenté dans le README |
| 4 | IA → MCP → PostgreSQL | Demander le stock d'un produit dans toutes les agences | Les quantités sont présentées par agence | Exemple documenté dans le README |
| 5 | IA → MCP → PostgreSQL | Demander les produits disponibles dans une agence, par exemple Paris | L'agent retrouve l'identifiant avec `list_branches`, puis consulte le stock de l'agence | Scénario décrit dans les instructions de l'agent |
| 6 | IA → MCP → Product API et PostgreSQL | Demander une recommandation d'équipement pour une salle informatique | Recommandations fondées sur le catalogue ; elles ne sont pas présentées comme une réservation ni comme une confirmation de stock | Exemple documenté dans le README |
| 7 | Client Web | Envoyer une question vide | Message demandant de saisir une question ; aucune requête n'est envoyée | Vérifié par le contrôle présent dans `client_web/js/app.js` |
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
