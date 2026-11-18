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

        admin_password = os.environ["ADMIN_PASSWORD"]

        password_hasher = PasswordHasher()

        admin = User(
            username="admin",
            password_hash=password_hasher.hash(admin_password),
            role="admin",
        )
        db.session.add(admin)

        user_password = os.environ["USER_PASSWORD"]

        common_user = User(
            username="common_user",
            password_hash=password_hasher.hash(user_password),
            role="common_user",
            branch=paris,
        )
        db.session.add(common_user)

        db.session.add_all([
            Stock(branch=paris, product_id=34, available_quantity=15),
            Stock(branch=paris, product_id=12, available_quantity=8),
            Stock(branch=lyon, product_id=34, available_quantity=3),
            Stock(branch=lyon, product_id=12, available_quantity=0),
        ])
        db.session.commit()
        print("Base de données initialisée avec succès.")
