
import os
import httpx

from fastmcp import FastMCP

mcp = FastMCP("HBntory MCP Server")

PRODUCT_API_URL = os.getenv("PRODUCT_API_URL", "http://localhost:5001")



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
    """
    Récupère les détails d'un produit à partir de son ID ou de son SKU.
    """
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

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000
    )