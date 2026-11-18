#!/usr/bin/env python3
"""Point d'entrée du Backoffice HBntory."""
import os

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Flask, request, session

from database import db
from models import User

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

db.init_app(app)
password_hasher = PasswordHasher()


@app.route("/api/login", methods=["POST"])
def login():
    """Connecte un utilisateur du Backoffice."""
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return {"error": "Nom d'utilisateur et mot de passe requis."}, 400

    user = User.query.filter_by(username=username).first()

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
