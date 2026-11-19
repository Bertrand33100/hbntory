
#!/usr/bin/env python3
"""Serveur MCP HBntory connecté à la Product API et PostgreSQL."""

import os

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

mcp = FastMCP("HBntory MCP Server")

PRODUCT_API_URL = os.getenv(
    "PRODUCT_API_URL",
    "http://localhost:5001"
)

DATABASE_URL = os.getenv("DATABASE_URL")


def get_database_connection():
    """Crée une connexion à PostgreSQL."""
    if not DATABASE_URL:
        raise ValueError(
            "La variable DATABASE_URL n'est pas configurée."
        )

    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )


@mcp.tool
async def list_products() -> dict:
    """Récupère la liste complète des produits depuis la Product API."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{PRODUCT_API_URL}/api/v1/products",
                params={
                    "limit": 100,
                    "include_discontinued": "true",
                }
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as error:
        raise ValueError(
            f"Erreur Product API : HTTP {error.response.status_code}"
        ) from error

    except httpx.TimeoutException as error:
        raise ValueError(
            "Délai d'attente dépassé lors de la récupération des produits."
        ) from error

    except httpx.RequestError as error:
        raise ValueError(
            f"Impossible de contacter la Product API : {error}"
        ) from error


@mcp.tool
async def get_product(product_id: str) -> dict:
    """Récupère les détails d'un produit par son ID ou son SKU."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{PRODUCT_API_URL}/api/v1/products/{product_id}"
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as error:
        if error.response.status_code == 404:
            raise ValueError(
                f"Produit introuvable : {product_id}"
            ) from error

        raise ValueError(
            f"Erreur Product API : HTTP {error.response.status_code}"
        ) from error

    except httpx.TimeoutException as error:
        raise ValueError(
            "Délai d'attente dépassé lors de la connexion à la Product API."
        ) from error

    except httpx.RequestError as error:
        raise ValueError(
            f"Impossible de contacter la Product API : {error}"
        ) from error


@mcp.tool
def get_stock_by_product(product_id: int) -> dict:
    """Récupère le stock d'un produit dans toutes les agences."""
    if not isinstance(product_id, int) or isinstance(product_id, bool):
        raise ValueError("L'identifiant du produit doit être un entier.")

    if product_id <= 0:
        raise ValueError("L'identifiant du produit doit être positif.")

    engine = get_database_connection()

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT
                        branches.id AS branch_id,
                        branches.name AS branch_name,
                        stock.product_id,
                        stock.available_quantity
                    FROM stock
                    JOIN branches
                        ON stock.branch_id = branches.id
                    WHERE stock.product_id = :product_id
                    ORDER BY branches.name
                """),
                {"product_id": product_id}
            )

            stocks = [
                dict(row)
                for row in result.mappings().all()
            ]

            return {
                "product_id": product_id,
                "stocks": stocks
            }

    except SQLAlchemyError as error:
        raise RuntimeError(
            "Impossible de récupérer le stock dans PostgreSQL."
        ) from error

    finally:
        engine.dispose()


@mcp.tool
def get_stock_by_branch(branch_id: int) -> dict:
    """Récupère tous les produits et leurs stocks dans une agence."""
    if not isinstance(branch_id, int) or isinstance(branch_id, bool):
        raise ValueError("L'identifiant de l'agence doit être un entier.")

    if branch_id <= 0:
        raise ValueError("L'identifiant de l'agence doit être positif.")

    engine = get_database_connection()

    try:
        with engine.connect() as connection:
            branch = connection.execute(
                text("""
                    SELECT id, name
                    FROM branches
                    WHERE id = :branch_id
                """),
                {"branch_id": branch_id}
            ).mappings().first()

            if branch is None:
                raise ValueError(
                    f"Agence introuvable : {branch_id}"
                )

            result = connection.execute(
                text("""
                    SELECT product_id, available_quantity
                    FROM stock
                    WHERE branch_id = :branch_id
                    ORDER BY product_id
                """),
                {"branch_id": branch_id}
            )

            products = [
                dict(row)
                for row in result.mappings().all()
            ]

            return {
                "branch": dict(branch),
                "products": products
            }

    except SQLAlchemyError as error:
        raise RuntimeError(
            "Impossible de récupérer le stock dans PostgreSQL."
        ) from error

    finally:
        engine.dispose()


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000
    )
