
import pytest
import httpx

import server

from sqlalchemy.exc import SQLAlchemyError


# ============================================================
# FAUSSE CONNEXION POSTGRESQL POUR LES TESTS
# ============================================================

class FakeResult:
    """Simule le résultat d'une requête SQL."""

    def __init__(self, rows):
        self.rows = rows

    def mappings(self):
        return self

    def all(self):
        return self.rows

    def first(self):
        if self.rows:
            return self.rows[0]
        return None


class FakeConnection:
    """Simule une connexion à PostgreSQL."""

    def __init__(self, results=None, error=None):
        self.results = results or []
        self.error = error
        self.call_number = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, parameters=None):
        if self.error:
            raise self.error

        result = self.results[self.call_number]
        self.call_number += 1

        return FakeResult(result)


class FakeEngine:
    """Simule le moteur de connexion SQLAlchemy."""

    def __init__(self, results=None, error=None):
        self.connection = FakeConnection(results, error)
        self.disposed = False

    def connect(self):
        return self.connection

    def dispose(self):
        self.disposed = True


# ============================================================
# TESTS PRODUCT API
# ============================================================

@pytest.mark.asyncio
async def test_list_products_success(monkeypatch):
    """Vérifie la récupération de la liste des produits."""

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

    result = await server.list_products()

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

    result = await server.get_product("1")

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

    with pytest.raises(
        ValueError,
        match="Produit introuvable : 999999"
    ):
        await server.get_product("999999")


@pytest.mark.asyncio
async def test_list_products_connection_error(monkeypatch):
    """Vérifie la gestion d'une erreur de connexion."""

    async def mock_get(self, url, params=None):
        request = httpx.Request("GET", url)

        raise httpx.ConnectError(
            "Connexion impossible",
            request=request
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    with pytest.raises(
        ValueError,
        match="Impossible de contacter la Product API"
    ):
        await server.list_products()


@pytest.mark.asyncio
async def test_list_products_timeout(monkeypatch):
    """Vérifie la gestion d'un dépassement du délai."""

    async def mock_get(self, url, params=None):
        request = httpx.Request("GET", url)

        raise httpx.ReadTimeout(
            "Délai dépassé",
            request=request
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    with pytest.raises(
        ValueError,
        match="Délai d'attente dépassé"
    ):
        await server.list_products()


@pytest.mark.asyncio
async def test_list_products_server_error(monkeypatch):
    """Vérifie la gestion d'une erreur HTTP 503."""

    async def mock_get(self, url, params=None):
        request = httpx.Request("GET", url)

        return httpx.Response(
            503,
            request=request,
            json={"error": "supplier_unavailable"}
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    with pytest.raises(
        ValueError,
        match="Erreur Product API : HTTP 503"
    ):
        await server.list_products()


# ============================================================
# TESTS STOCK PAR PRODUIT
# ============================================================

def test_get_stock_by_product_success(monkeypatch):
    """Vérifie la récupération du stock dans toutes les agences."""

    rows = [
        {
            "branch_id": 1,
            "branch_name": "Paris",
            "product_id": 12,
            "available_quantity": 8
        },
        {
            "branch_id": 2,
            "branch_name": "Lyon",
            "product_id": 12,
            "available_quantity": 0
        }
    ]

    engine = FakeEngine(results=[rows])

    monkeypatch.setattr(
        server,
        "get_database_connection",
        lambda: engine
    )

    result = server.get_stock_by_product(12)

    assert result["product_id"] == 12
    assert len(result["stocks"]) == 2
    assert result["stocks"][0]["branch_name"] == "Paris"
    assert result["stocks"][0]["available_quantity"] == 8
    assert result["stocks"][1]["branch_name"] == "Lyon"
    assert result["stocks"][1]["available_quantity"] == 0
    assert engine.disposed is True


def test_get_stock_by_product_no_stock(monkeypatch):
    """Vérifie le résultat lorsqu'aucun stock n'est enregistré."""

    engine = FakeEngine(results=[[]])

    monkeypatch.setattr(
        server,
        "get_database_connection",
        lambda: engine
    )

    result = server.get_stock_by_product(999)

    assert result["product_id"] == 999
    assert result["stocks"] == []
    assert engine.disposed is True


@pytest.mark.parametrize("product_id", [0, -1, "12", True])
def test_get_stock_by_product_invalid_id(product_id):
    """Vérifie le rejet des identifiants de produit invalides."""

    with pytest.raises(ValueError):
        server.get_stock_by_product(product_id)


def test_get_stock_by_product_database_error(monkeypatch):
    """Vérifie la gestion d'une erreur PostgreSQL."""

    engine = FakeEngine(error=SQLAlchemyError("Erreur SQL"))

    monkeypatch.setattr(
        server,
        "get_database_connection",
        lambda: engine
    )

    with pytest.raises(
        RuntimeError,
        match="Impossible de récupérer le stock dans PostgreSQL"
    ):
        server.get_stock_by_product(12)

    assert engine.disposed is True


# ============================================================
# TESTS STOCK PAR AGENCE
# ============================================================

def test_get_stock_by_branch_success(monkeypatch):
    """Vérifie la récupération des produits d'une agence."""

    branch = {
        "id": 1,
        "name": "Paris"
    }

    products = [
        {
            "product_id": 12,
            "available_quantity": 8
        },
        {
            "product_id": 34,
            "available_quantity": 15
        }
    ]

    engine = FakeEngine(results=[
        [branch],
        products
    ])

    monkeypatch.setattr(
        server,
        "get_database_connection",
        lambda: engine
    )

    result = server.get_stock_by_branch(1)

    assert result["branch"]["id"] == 1
    assert result["branch"]["name"] == "Paris"
    assert len(result["products"]) == 2
    assert result["products"][0]["product_id"] == 12
    assert result["products"][0]["available_quantity"] == 8
    assert engine.disposed is True


def test_get_stock_by_branch_not_found(monkeypatch):
    """Vérifie la gestion d'une agence inexistante."""

    engine = FakeEngine(results=[[]])

    monkeypatch.setattr(
        server,
        "get_database_connection",
        lambda: engine
    )

    with pytest.raises(
        ValueError,
        match="Agence introuvable : 999"
    ):
        server.get_stock_by_branch(999)

    assert engine.disposed is True


@pytest.mark.parametrize("branch_id", [0, -1, "1", True])
def test_get_stock_by_branch_invalid_id(branch_id):
    """Vérifie le rejet des identifiants d'agence invalides."""

    with pytest.raises(ValueError):
        server.get_stock_by_branch(branch_id)


def test_get_stock_by_branch_database_error(monkeypatch):
    """Vérifie la gestion d'une erreur PostgreSQL."""

    engine = FakeEngine(error=SQLAlchemyError("Erreur SQL"))

    monkeypatch.setattr(
        server,
        "get_database_connection",
        lambda: engine
    )

    with pytest.raises(
        RuntimeError,
        match="Impossible de récupérer le stock dans PostgreSQL"
    ):
        server.get_stock_by_branch(1)

    assert engine.disposed is True
