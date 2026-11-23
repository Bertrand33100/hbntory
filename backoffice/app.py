#!/usr/bin/env python3
"""Point d'entrée du Backoffice HBntory."""
import os
from functools import wraps

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from flask import Flask, request, session

from database import db
from models import Stock, User

app = Flask(__name__)

# Les secrets viennent de l'environnement, jamais du code
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
# Protection du cookie de session (SameSite limite le CSRF)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("COOKIE_SECURE") == "1"

db.init_app(app)
password_hasher = PasswordHasher()


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
    except (InvalidHashError, VerificationError):
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
