# Authentification et autorisation du Backoffice

## 1. Stockage des mots de passe

Les mots de passe sont hachés avec **Argon2id** (bibliothèque `argon2-cffi`).
Aucun mot de passe n'est stocké en clair : la table `users` ne contient que le haché, dans `password_hash`.

**Hachage** : `PasswordHasher().hash(mot_de_passe)` tire un sel aléatoire, mélange le mot de passe
et le sel avec Argon2id, puis renvoie une chaîne qui contient l'algorithme, ses réglages, le sel et le résultat
(`$argon2id$v=19$m=65536,t=3,p=4$...`). Deux mots de passe identiques donnent donc deux hachés différents.

**Vérification** : à la connexion, `PasswordHasher().verify(haché, mot_de_passe_tapé)` lit le sel et
les réglages dans le haché enregistré, hache le mot de passe tapé de la même façon, puis compare les deux résultats.

**Pourquoi pas SHA256 seul ?**
- SHA256 est conçu pour être **rapide** : un attaquant qui vole la base peut tester des milliards
  de mots de passe par seconde sur une carte graphique.
- Sans sel, deux utilisateurs avec le même mot de passe ont le même haché, et des tables
  de hachés précalculés permettent de retrouver les mots de passe courants instantanément.
- Argon2id est au contraire **volontairement lent et gourmand en mémoire**, ce qui rend ces attaques
  très coûteuses, et il ajoute un sel automatiquement. C'est l'algorithme recommandé par l'OWASP
  pour le stockage des mots de passe.

## 2. Authentification : session et cookie

Nous utilisons une **authentification par session**, gérée par Flask.

1. `POST /api/login` vérifie le nom, le mot de passe et que le compte est actif (`is_active`).
2. En cas de succès, la session reçoit seulement l'id de l'utilisateur : `session["user_id"]`.
3. Flask place la session dans un cookie **signé** avec `SECRET_KEY` (variable d'environnement).
   Le cookie est lisible mais ne peut pas être modifié : une signature invalide vide la session.
   Il est marqué `HttpOnly`, donc illisible par le JavaScript de la page.
4. `POST /api/logout` vide la session.

Le même message, « Identifiants invalides », est renvoyé pour un nom inconnu, un mauvais mot de passe
ou un compte désactivé, afin de ne pas révéler quels comptes existent.

**Pourquoi une session plutôt qu'un jeton (token) ?**
Le Backoffice est une application web servie par le même serveur que son interface : le navigateur
gère le cookie automatiquement, sans code côté client pour stocker ou renvoyer un jeton.
La déconnexion est immédiate, et un compte désactivé est refusé dès la requête suivante,
puisque l'utilisateur est relu en base à chaque requête.

## 3. Autorisation par rôle, côté backend

Les règles sont appliquées dans le backend par deux décorateurs, placés au-dessus des routes.
Ils s'exécutent avant la route : en cas de refus, la route n'est jamais exécutée.

- `get_current_user()` lit `session["user_id"]`, puis relit l'utilisateur en base.
  Elle renvoie `None` si personne n'est connecté, ou si le compte n'existe plus ou a été désactivé.
- `@login_required` : refuse avec **401** si personne n'est connecté.
- `@role_required("admin")` / `@role_required("common_user")` : refuse avec **401** si personne
  n'est connecté, et avec **403** si le rôle ne correspond pas.

| Règle | Application |
| --- | --- |
| Routes de gestion des utilisateurs : admin uniquement | `@role_required("admin")` |
| Routes de stock : utilisateur standard uniquement (l'admin ne gère pas le stock) | `@role_required("common_user")` |
| Utilisateur standard : seulement le stock de son agence | l'agence est lue sur l'utilisateur connecté (`user.branch_id`), jamais dans la requête |

L'interface pourra masquer des boutons selon le rôle, mais la sécurité ne repose jamais sur elle.

## 4. Tests effectués

| Test | Résultat attendu | Résultat |
| --- | --- | --- |
| Connexion avec les bons identifiants | 200, cookie de session | ✅ |
| Mauvais mot de passe | 401, pas de cookie | ✅ |
| Compte désactivé, bon mot de passe | 401, pas de cookie | ✅ |
| `GET /api/me` sans connexion | 401 | ✅ |
| `GET /api/me` connecté | 200 | ✅ |
| `GET /api/users` par un utilisateur standard | 403 | ✅ |
| `GET /api/users` par l'admin | 200 | ✅ |
| `GET /api/stock` par un utilisateur standard | 200, stock de son agence uniquement | ✅ |
| `GET /api/stock` par l'admin | 403 | ✅ |
