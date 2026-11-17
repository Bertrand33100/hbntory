#!/usr/bin/env python3
"""Modèles SQLAlchemy du Backoffice HBntory."""
from app import db


class Branch(db.Model):
    """Agence de l'enseigne (ex. Paris, Lyon)."""

    __tablename__ = "branches"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    users = db.relationship("User", back_populates="branch")
    stock_items = db.relationship("Stock", back_populates="branch")


class User(db.Model):
    """Utilisateur du Backoffice HBntory."""

    __tablename__ = "users"
    __table_args__ = (
        db.CheckConstraint(
            "role IN ('admin', 'common_user')",
            name="ck_users_role",
        ),
        db.CheckConstraint(
            "(role = 'admin' AND branch_id IS NULL) OR "
            "(role = 'common_user' AND branch_id IS NOT NULL)",
            name="ck_users_role_branch",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    branch_id = db.Column(
        db.Integer, db.ForeignKey("branches.id"), nullable=True
    )
    created_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.now()
    )
    updated_at = db.Column(
        db.DateTime, nullable=False,
        server_default=db.func.now(), onupdate=db.func.now()
    )
    branch = db.relationship("Branch", back_populates="users")


class Stock(db.Model):
    """Stock d'une agence."""

    __tablename__ = "stock"
    __table_args__ = (
        db.CheckConstraint(
            "available_quantity >= 0",
            name="ck_stock_quantity_positive",
        ),
        db.UniqueConstraint(
            "branch_id", "product_id",
            name="uq_stock_branch_product",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(
        db.Integer, db.ForeignKey("branches.id"), nullable=False
    )
    product_id = db.Column(db.Integer, nullable=False)
    available_quantity = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.now()
    )
    updated_at = db.Column(
        db.DateTime, nullable=False,
        server_default=db.func.now(), onupdate=db.func.now()
    )
    branch = db.relationship("Branch", back_populates="stock_items")
