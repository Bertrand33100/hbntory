#!/usr/bin/env python3
"""Initialise la base du Backoffice HBntory avec des données de départ."""
import os

from argon2 import PasswordHasher

from app import app, db
from models import Branch, Stock, User

with app.app_context():
    db.create_all()

    if User.query.filter_by(username="admin").first():
        print("La base de données est déjà initialisée.")
    else:
        print("Initialisation de la base de données...")

        paris = Branch(name="Paris")
        lyon = Branch(name="Lyon")
        db.session.add_all([paris, lyon])
