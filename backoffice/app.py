#!/usr/bin/env python3
"""Point d'entrée du Backoffice HBntory."""
import os
from functools import wraps

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Flask, request, session
import requests
from sqlalchemy import update

from database import db
from models import Branch, Stock, User

app = Flask(__name__)
# Les secrets viennent de l'environnement, jamais du code
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

db.init_app(app)

password_hasher = PasswordHasher()
PRODUCT_API_URL = os.environ.get("PRODUCT_API_URL", "http://localhost:5001")


def get_current_user():
    """Renvoie l'utilisateur connecté et actif ou None."""
    # La session ne contient que l'id : le reste est relu en base, à jour
    user_id = session.get("user_id")
    if user_id is None:
        return None
    user = db.session.get(User, user_id)
    if user is None or not user.is_active:
        session.clear()
        return None
    return user


def login_required(view):
    """Refuse l'accès si aucun utilisateur n'est connecté."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if get_current_user() is None:
            return {"error": "Authentification requise."}, 401
        return view(*args, **kwargs)
    return wrapper


def role_required(role):
    """Refuse l'accès si l'utilisateur n'a pas le rôle demandé."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if user is None:
                return {"error": "Authentification requise."}, 401
            # Connecté, mais sans le bon rôle : 403 (accès interdit)
            if user.role != role:
                return {"error": "Accès interdit."}, 403
            return view(*args, **kwargs)
        return wrapper
    return decorator


def fetch_products():
    """Récupère le catalogue de la Product API, indexé par id, ou None."""
    try:
        response = requests.get(
            f"{PRODUCT_API_URL}/api/v1/products",
            params={"limit": 100, "include_discontinued": "true"},
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException:
        return None
    products = response.json()["results"]
    return {product["id"]: product for product in products}


@app.route("/api/login", methods=["POST"])
def login():
    """Connecte un utilisateur du Backoffice."""
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return {"error": "Nom d'utilisateur et mot de passe requis."}, 400

    user = User.query.filter_by(username=username).first()

    # Même message pour chaque échec, pour ne pas révéler les comptes
    if user is None:
        return {"error": "Identifiants invalides."}, 401

    try:
        password_hasher.verify(user.password_hash, password)
    except VerifyMismatchError:
        return {"error": "Identifiants invalides."}, 401

    if not user.is_active:
        return {"error": "Identifiants invalides."}, 401

    session.clear()
    session["user_id"] = user.id
    return {"message": "Connexion réussie.", "role": user.role}, 200


@app.route("/api/logout", methods=["POST"])
def logout():
    """Déconnecte l'utilisateur en vidant sa session."""
    session.clear()
    return {"message": "Déconnexion réussie."}, 200


@app.route("/api/me", methods=["GET"])
@login_required
def me():
    """Renvoie les informations de l'utilisateur connecté."""
    user = get_current_user()
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "branch_id": user.branch_id,
    }, 200


@app.route("/api/users", methods=["GET"])
@role_required("admin")
def list_users():
    """Liste tous les utilisateurs. Route réservée à l'admin."""
    users = User.query.order_by(User.id).all()
    # Jamais de password_hash dans une réponse
    return [
        {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "branch_id": user.branch_id,
            "is_active": user.is_active,
        }
        for user in users
    ], 200


@app.route("/api/stock", methods=["GET"])
@role_required("common_user")
def list_stock():
    """Liste le stock de l'agence de l'utilisateur connecté."""
    user = get_current_user()
    # L'agence vient de l'utilisateur connecté, jamais de la requête
    stock_items = Stock.query.filter_by(branch_id=user.branch_id).all()
    return [
        {
            "product_id": item.product_id,
            "available_quantity": item.available_quantity,
        }
        for item in stock_items
    ], 200


@app.route("/api/users", methods=["POST"])
@role_required("admin")
def create_user():
    """Crée un utilisateur standard. Route réservée à l'admin."""
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    branch_id = data.get("branch_id")

    if not username or not password or branch_id is None:
        return {"error": "Nom, mot de passe et agence requis."}, 400
    if len(password) < 8:
        return {"error": "Mot de passe : 8 caractères minimum."}, 400
    if not isinstance(branch_id, int):
        return {"error": "L'identifiant de l'agence doit être un entier."}, 400

    if db.session.get(Branch, branch_id) is None:
        return {"error": "Agence inexistante."}, 400
    if User.query.filter_by(username=username).first() is not None:
        return {"error": "Nom d'utilisateur déjà utilisé."}, 409

    user = User(
        username=username,
        password_hash=password_hasher.hash(password),
        role="common_user",
        branch_id=branch_id,
    )
    db.session.add(user)
    db.session.commit()

    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "branch_id": user.branch_id,
        "is_active": user.is_active,
    }, 201


@app.route("/api/users/<int:user_id>/password", methods=["PUT"])
@role_required("admin")
def change_password(user_id):
    """Change le mot de passe d'un utilisateur standard (admin)."""
    user = db.session.get(User, user_id)
    if user is None:
        return {"error": "Utilisateur introuvable."}, 404
    if user.role != "common_user":
        return {"error": "Utilisateur non modifiable."}, 400

    data = request.get_json(silent=True) or {}
    password = data.get("password")
    if not password or len(password) < 8:
        return {"error": "Mot de passe : 8 caractères minimum."}, 400

    user.password_hash = password_hasher.hash(password)
    db.session.commit()
    return {"message": "Mot de passe modifié."}, 200


@app.route("/api/users/<int:user_id>/branch", methods=["PUT"])
@role_required("admin")
def change_branch(user_id):
    """Change l'agence d'un utilisateur standard (admin)."""
    user = db.session.get(User, user_id)
    if user is None:
        return {"error": "Utilisateur introuvable."}, 404
    if user.role != "common_user":
        return {"error": "Utilisateur non modifiable."}, 400

    data = request.get_json(silent=True) or {}
    branch_id = data.get("branch_id")
    if not isinstance(branch_id, int):
        return {"error": "L'agence doit être un identifiant numérique."}, 400
    if db.session.get(Branch, branch_id) is None:
        return {"error": "Agence inexistante."}, 400

    user.branch_id = branch_id
    db.session.commit()
    return {"message": "Agence modifiée.", "branch_id": branch_id}, 200


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
@role_required("admin")
def deactivate_user(user_id):
    """Désactive un utilisateur standard (suppression douce, admin)."""
    user = db.session.get(User, user_id)
    if user is None:
        return {"error": "Utilisateur introuvable."}, 404
    if user.role != "common_user":
        return {"error": "Utilisateur non modifiable."}, 400

    user.is_active = False
    db.session.commit()
    return {"message": "Utilisateur désactivé."}, 200


@app.route("/api/stock/<int:product_id>", methods=["GET"])
@role_required("common_user")
def get_stock(product_id):
    """Renvoie la quantité d'un produit dans l'agence de l'utilisateur."""
    user = get_current_user()
    item = Stock.query.filter_by(
        branch_id=user.branch_id, product_id=product_id
    ).first()
    quantity = item.available_quantity if item else 0
    return {
        "branch_id": user.branch_id,
        "product_id": product_id,
        "available_quantity": quantity,
    }, 200


@app.route("/api/stock/add", methods=["POST"])
@role_required("common_user")
def add_stock():
    """Ajoute une quantité d'un produit au stock de l'agence."""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    quantity = data.get("quantity")

    if not isinstance(product_id, int) or not isinstance(quantity, int):
        return {"error": "Produit et quantité doivent être des entiers."}, 400
    if quantity <= 0:
        return {"error": "La quantité doit être positive."}, 400

    # Le produit doit exister dans la Product API
    catalog = fetch_products()
    if catalog is None:
        return {"error": "Product API indisponible."}, 503
    if product_id not in catalog:
        return {"error": "Produit inconnu."}, 404

    item = Stock.query.filter_by(
        branch_id=user.branch_id, product_id=product_id
    ).first()
    if item is None:
        item = Stock(
            branch_id=user.branch_id,
            product_id=product_id,
            available_quantity=quantity,
        )
        db.session.add(item)
    else:
        # L'addition est faite par la base elle-même, en une seule opération
        item.available_quantity = Stock.available_quantity + quantity
    db.session.commit()

    return {
        "branch_id": user.branch_id,
        "product_id": product_id,
        "available_quantity": item.available_quantity,
    }, 200


@app.route("/api/stock/remove", methods=["POST"])
@role_required("common_user")
def remove_stock():
    """Retire une quantité d'un produit du stock de l'agence."""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    quantity = data.get("quantity")

    if not isinstance(product_id, int) or not isinstance(quantity, int):
        return {"error": "Produit et quantité doivent être des entiers."}, 400
    if quantity <= 0:
        return {"error": "La quantité doit être positive."}, 400

    # Vérification et retrait en une seule opération (atomique)
    result = db.session.execute(
        update(Stock)
        .where(
            Stock.branch_id == user.branch_id,
            Stock.product_id == product_id,
            Stock.available_quantity >= quantity,
        )
        .values(available_quantity=Stock.available_quantity - quantity)
    )
    if result.rowcount == 0:
        db.session.rollback()
        return {"error": "Stock insuffisant."}, 409
    db.session.commit()

    item = Stock.query.filter_by(
        branch_id=user.branch_id, product_id=product_id
    ).first()
    return {
        "branch_id": user.branch_id,
        "product_id": product_id,
        "available_quantity": item.available_quantity,
    }, 200


@app.route("/api/stock/products", methods=["GET"])
@role_required("common_user")
def list_products_in_stock():
    """Liste les produits en stock de l'agence, avec leurs détails."""
    user = get_current_user()
    stock_items = Stock.query.filter(
        Stock.branch_id == user.branch_id,
        Stock.available_quantity > 0,
    ).all()

    # Les détails des produits viennent de la Product API, jamais de la base
    catalog = fetch_products()

    products = []
    for item in stock_items:
        product = catalog.get(item.product_id) if catalog else None
        products.append({
            "product_id": item.product_id,
            "name": product["name"] if product else None,
            "sku": product["sku"] if product else None,
            "available_quantity": item.available_quantity,
        })

    return {
        "branch_id": user.branch_id,
        "product_api_available": catalog is not None,
        "products": products,
    }, 200


@app.route("/api/products", methods=["GET"])
@role_required("common_user")
def list_catalog():
    """Liste le catalogue de la Product API, pour le sélecteur."""
    catalog = fetch_products()
    if catalog is None:
        return {"error": "Product API indisponible."}, 503
    return [
        {
            "product_id": product["id"],
            "sku": product["sku"],
            "name": product["name"],
            "discontinued": product["discontinued"],
        }
        for product in catalog.values()
    ], 200


@app.route("/", methods=["GET"])
def index():
    """Sert la page de l'interface du Backoffice."""
    return app.send_static_file("index.html")


@app.route("/api/branches", methods=["GET"])
@login_required
def list_branches():
    """Liste les agences, pour les menus et le bandeau."""
    branches = Branch.query.order_by(Branch.id).all()
    return [{"id": branch.id, "name": branch.name} for branch in branches], 200
