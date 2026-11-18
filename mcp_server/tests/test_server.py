import pytest
import httpx

from server import list_products
from server import get_product


@pytest.mark.asyncio
async def test_list_products_success(monkeypatch):
    """Vérifie que la liste des produits est correctement récupérée."""

    async def mock_get(self, url, params=None):
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            request=request,
            json={
                "count": 40,
                "results": [{"id": 1}, {"id": 2}]
            }
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await list_products()

    assert result["count"] == 40
    assert len(result["results"]) == 2

@pytest.mark.asyncio
async def test_get_product_success(monkeypatch):
    """Vérifie la récupération des détails d'un produit."""

    async def mock_get(self, url, params=None):
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            request=request,
            json={
                "id": 1,
                "sku": "HB-LAP-1001",
                "name": "Ordinateur portable"
            }
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await get_product("1")

    assert result["id"] == 1
    assert result["sku"] == "HB-LAP-1001"

@pytest.mark.asyncio
async def test_get_product_not_found(monkeypatch):
    """Vérifie la gestion d'un produit inexistant."""

    async def mock_get(self, url, params=None):
        request = httpx.Request("GET", url)
        return httpx.Response(
            404,
            request=request,
            json={"error": "not_found"}
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    with pytest.raises(ValueError, match="Produit introuvable : 999999"):
        await get_product("999999")

@pytest.mark.asyncio
async def test_list_products_connection_error(monkeypatch):
    """Vérifie la gestion d'une erreur de connexion."""

    async def mock_get(self, url, params=None):
        request = httpx.Request("GET", url)
        raise httpx.ConnectError("Connexion impossible", request=request)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    with pytest.raises(ValueError, match="Impossible de contacter la Product API"):
        await list_products()

@pytest.mark.asyncio
async def test_list_products_timeout(monkeypatch):
    """Vérifie la gestion d'un dépassement du délai d'attente."""

    async def mock_get(self, url, params=None):
        request = httpx.Request("GET", url)
        raise httpx.ReadTimeout("Délai dépassé", request=request)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    with pytest.raises(ValueError, match="Délai d'attente dépassé"):
        await list_products()

@pytest.mark.asyncio
async def test_list_products_server_error(monkeypatch):
    """Vérifie la gestion d'une erreur serveur HTTP 503."""

    async def mock_get(self, url, params=None):
        request = httpx.Request("GET", url)
        return httpx.Response(
            503,
            request=request,
            json={"error": "supplier_unavailable"}
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    with pytest.raises(ValueError, match="Erreur Product API : HTTP 503"):
        await list_products()