# HBntory — Product API externe (fiche de référence)

Cette fiche résume ce que l'équipe a observé et lu sur la Product API fournie (étape 0). Elle sert de référence pour le Backoffice et pour le serveur MCP.

Sources : `README.md` et `docs/api_contract.md` du dépôt de la Product API, et tests réalisés avec `curl`.

---

## 1. Rôle de l'API

La Product API simule le **catalogue d'un fournisseur**. Elle est **en lecture seule** et ne doit pas être modifiée.

| La Product API fournit | HBntory gère lui-même |
| --- | --- |
| Identifiants, noms, descriptions, catégories, marques, tags, prix, fournisseurs, métadonnées | Les quantités de stock par agence, leur création, leur mise à jour et leur consultation |

Elle ne fournit **aucune quantité de stock**. La Product API dit *ce qu'est* un produit ; notre base dit *où il se trouve et en quelle quantité*.

---

## 2. Lancement

Depuis le dossier de la Product API :

```bash
docker compose up --build        # lancement avec les logs dans le terminal
docker compose up -d --build     # lancement en arrière-plan
docker compose down              # arrêt
```

| Contexte | Adresse |
| --- | --- |
| Depuis notre machine (terminal, navigateur) | `http://localhost:5001` |
| Depuis un autre conteneur du même réseau Compose (Backoffice, MCP) | `http://external-products-api:5000` |

Le port **5000** est celui de l'API dans son conteneur ; le port **5001** est celui exposé sur notre machine.

**Choix de l'équipe :** l'adresse de la Product API sera lue dans une variable d'environnement (par exemple `PRODUCT_API_URL`), et jamais écrite en dur dans le code.

**Vérification :**

```bash
curl http://localhost:5001/health
```

Réponse observée :

```json
{
  "status": "ok",
  "products": 40,
  "suppliers": 5
}
```

---

## 3. Routes utiles

| Méthode | Route | Rôle |
| --- | --- | --- |
| GET | `/health` | Vérifier que le service est joignable |
| GET | `/api/v1/products` | Lister les produits (filtres et pagination) |
| GET | `/api/v1/products/search?q=<texte>` | Rechercher par nom, SKU, description ou tag |
| GET | `/api/v1/products/{id_ou_sku}` | Détail d'un produit, par id numérique ou par SKU |
| GET | `/api/v1/categories` | Catégories et nombre de produits par catégorie |
| GET | `/api/v1/suppliers` | Métadonnées des fournisseurs |

---

## 4. Identifiant produit

Chaque produit possède **deux identifiants** :

| Champ | Exemple | Type |
| --- | --- | --- |
| `id` | `1` | Entier |
| `sku` | `HB-LAP-1001` | Texte |

La route de détail accepte les deux (testé : `/api/v1/products/1` et `/api/v1/products/HB-LAP-1001` renvoient le même produit).

**Choix de l'équipe : nous stockons l'`id` numérique** dans la table `stock`, dans une colonne de type **entier**.

- La route de détail l'accepte directement : `/api/v1/products/{id}`.
- Un entier est simple à stocker, à comparer et à valider (pas de problème de casse, d'espaces ou de format).
- Il est présent dans chaque produit renvoyé par la liste et par la recherche.

**Limite à garder en tête :** l'`id` est un numéro technique, moins lisible que le SKU (`1` au lieu de `HB-LAP-1001`). Le SKU reste disponible dans la réponse de l'API pour l'affichage si besoin.

**Alternative écartée :** le SKU (`HB-LAP-1001`), référence métier plus lisible, mais de type texte.

---

## 5. Liste des produits : pagination et filtres

La route `/api/v1/products` est **paginée**. Réponse observée sans paramètre :

```json
{
  "count": 39,
  "limit": 20,
  "offset": 0,
  "results": [ ... ]
}
```

| Champ | Signification |
| --- | --- |
| `count` | Nombre total de produits correspondant à la requête |
| `limit` | Nombre de produits par page (20 par défaut, **100 au maximum**) |
| `offset` | Position de départ dans les résultats |
| `results` | Les produits de la page |

**Paramètres disponibles :**

| Paramètre | Exemple | Rôle |
| --- | --- | --- |
| `q` | `q=keyboard` | Recherche dans le nom, le SKU, la description et les tags |
| `category` | `category=Accessories` | Filtre exact sur la catégorie |
| `supplier_id` | `supplier_id=SUP-HBT-001` | Filtre exact sur le fournisseur |
| `include_discontinued` | `include_discontinued=true` | Inclure les produits arrêtés (par défaut : `false`) |
| `min_price` / `max_price` | `min_price=50` | Fourchette de prix unitaire |
| `limit` | `limit=100` | Taille de la page (maximum 100) |
| `offset` | `offset=20` | Décalage des résultats |
| `sort` | `sort=-unit_price` | Tri par `name`, `sku`, `category`, `unit_price` ou `updated_at` (`-` = décroissant) |

**Points d'attention :**

- **39 produits listés pour 40 au catalogue :** la liste masque par défaut le produit **arrêté** (`discontinued: true`, produit que le fournisseur ne vend plus). Un produit arrêté peut pourtant encore être en stock dans une agence.
- **Pour obtenir tout le catalogue en une requête :** `/api/v1/products?limit=100&include_discontinued=true`.
- **Dans la liste**, l'objet `supplier` complet n'apparaît pas : il n'est présent que dans le **détail** d'un produit.
- **L'ordre des résultats** n'est pas celui des `id` : il ne faut pas s'appuyer dessus (utiliser `sort` si besoin).

---

## 6. Objet produit

```json
{
  "id": 1,
  "sku": "HB-LAP-1001",
  "name": "Holberton Student Laptop 14",
  "description": "Training catalog item for HBntory integration: holberton student laptop 14.",
  "category": "Laptops",
  "brand": "Holberton",
  "supplier_id": "SUP-HBT-001",
  "supplier_name": "Holberton Tools Co.",
  "unit_price": 799.0,
  "currency": "USD",
  "discontinued": false,
  "weight_kg": 1.35,
  "tags": ["student", "portable", "linux-ready"],
  "updated_at": "2026-05-22T12:00:00Z"
}
```

Le détail d'un produit contient en plus un objet `supplier` (identifiant, nom, e-mail de contact, pays, délai de livraison, score de fiabilité).

**Rappel :** aucun de ces champs n'est stocké dans notre base, à l'exception de l'`id`.

---

## 7. Erreurs

Format des réponses d'erreur :

```json
{
  "error": "not_found",
  "message": "Product not found."
}
```

**Comportements que notre application doit gérer** (exigés par le contrat de l'API) :

| Situation | Comment la provoquer | Ce que notre application doit faire |
| --- | --- | --- |
| Liste de produits vide | — | Afficher ou répondre qu'aucun produit n'est disponible, sans planter |
| Produit introuvable (`404`) | `/api/v1/products/INEXISTANT` | Message clair ; l'IA répond « information indisponible » |
| API lente | `?simulate_delay_ms=750` | Délai maximal (*timeout*) sur chaque appel, puis message d'erreur clair |
| API indisponible | `?force_error=true` | Message d'erreur clair, sans planter |
| Données fournisseur modifiées | — | Ne jamais modifier nos quantités de stock à partir des données du fournisseur |

Le code HTTP renvoyé avec `force_error=true` reste à vérifier.

---

## 8. Décisions prises à partir de cette fiche

| Sujet | Décision |
| --- | --- |
| Identifiant stocké | L'**`id`** numérique, colonne de type entier |
| Adresse de l'API | Variable d'environnement (`PRODUCT_API_URL`) : `http://localhost:5001` en local, `http://external-products-api:5000` dans Docker Compose |
| Récupération du catalogue complet | `limit=100&include_discontinued=true` |
| Appels à l'API | Toujours avec un délai maximal et une gestion des erreurs |
| Historique des mouvements de stock | Mentionné par le contrat de l'API, mais non exigé par le sujet : gardé en liste 2 du MVP |
