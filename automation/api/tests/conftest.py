"""
Pytest fixtures for InvenTree Parts API test suite.

Session-scoped: base_url, auth_client, anon_client
Function-scoped: category_factory, part_factory, bom_item_factory, stock_item_factory
                 + convenience fixtures: assembly_part, component_part, template_part, inactive_part

Usage:
    BASE_URL=http://localhost:8000 pytest tests/
    TEST_USER=admin TEST_PASSWORD=admin pytest tests/
"""
import os
import pytest
from faker import Faker
from dotenv import load_dotenv

from .helpers.api_client import APIClient

load_dotenv()

fake = Faker()

# ---------------------------------------------------------------------------
# Pytest options
# ---------------------------------------------------------------------------

def pytest_addoption(parser):
    parser.addoption(
        "--base-url",
        action="store",
        default=None,
        help="Base URL for the API server (overrides BASE_URL env var)",
    )


# ---------------------------------------------------------------------------
# Session-scoped: connectivity + auth
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def base_url(request) -> str:
    url = (
        request.config.getoption("--base-url")
        or os.environ.get("BASE_URL", "http://localhost:8001")
    )
    return url.rstrip("/")


@pytest.fixture(scope="session")
def auth_credentials() -> tuple:
    return (
        os.environ.get("TEST_USER", "admin"),
        os.environ.get("TEST_PASSWORD", "admin"),
    )


@pytest.fixture(scope="session")
def auth_client(base_url, auth_credentials) -> APIClient:
    return APIClient(base_url, auth=auth_credentials)


@pytest.fixture(scope="session")
def anon_client(base_url) -> APIClient:
    return APIClient(base_url)


@pytest.fixture(autouse=True, scope="session")
def check_server_health(auth_client):
    if not auth_client.check_health():
        pytest.skip(
            "API server is not reachable. "
            "Start the server with: docker compose up\n"
            f"Expected at: {auth_client.base_url}"
        )


# ---------------------------------------------------------------------------
# Function-scoped: category factory
# ---------------------------------------------------------------------------

@pytest.fixture
def category_factory(auth_client):
    created_ids = []

    def make_category(**overrides) -> dict:
        payload = {
            "name": fake.unique.word().capitalize() + " Category",
            "description": fake.sentence(),
        }
        payload.update(overrides)
        r = auth_client.post("/api/part/category/", json=payload)
        assert r.status_code == 201, f"category_factory failed: {r.text}"
        data = r.json()
        created_ids.append(data["id"])
        return data

    yield make_category

    # Cleanup: reverse insertion order (children before parents)
    for cat_id in reversed(created_ids):
        auth_client.delete(f"/api/part/category/{cat_id}/")


# ---------------------------------------------------------------------------
# Function-scoped: part factory
# ---------------------------------------------------------------------------

@pytest.fixture
def part_factory(auth_client):
    created_ids = []

    def make_part(**overrides) -> dict:
        payload = {
            "name": fake.unique.catch_phrase(),
            "description": fake.sentence(),
            "active": True,
            "virtual": False,
            "template": False,
            "assembly": False,
            "component": True,
        }
        payload.update(overrides)
        r = auth_client.post("/api/part/", json=payload)
        assert r.status_code == 201, f"part_factory failed: {r.text}"
        data = r.json()
        created_ids.append(data["id"])
        return data

    yield make_part

    for part_id in reversed(created_ids):
        auth_client.delete(f"/api/part/{part_id}/")


# ---------------------------------------------------------------------------
# Function-scoped: BOM item factory
# ---------------------------------------------------------------------------

@pytest.fixture
def bom_item_factory(auth_client):
    created_ids = []

    def make_bom_item(assembly_id: int, sub_part_id: int, **overrides) -> dict:
        payload = {
            "assembly": assembly_id,
            "sub_part": sub_part_id,
            "quantity": 1,
        }
        payload.update(overrides)
        r = auth_client.post("/api/part/bom/", json=payload)
        assert r.status_code == 201, f"bom_item_factory failed: {r.text}"
        data = r.json()
        created_ids.append(data["id"])
        return data

    yield make_bom_item

    for bom_id in reversed(created_ids):
        auth_client.delete(f"/api/part/bom/{bom_id}/")


# ---------------------------------------------------------------------------
# Function-scoped: stock item factory
# ---------------------------------------------------------------------------

@pytest.fixture
def stock_item_factory(auth_client):
    created_ids = []

    def make_stock_item(part_id: int, **overrides) -> dict:
        payload = {
            "part": part_id,
            "quantity": 10,
        }
        payload.update(overrides)
        r = auth_client.post("/api/part/stock/", json=payload)
        assert r.status_code == 201, f"stock_item_factory failed: {r.text}"
        data = r.json()
        created_ids.append(data["id"])
        return data

    yield make_stock_item

    for stock_id in reversed(created_ids):
        auth_client.delete(f"/api/part/stock/{stock_id}/")


# ---------------------------------------------------------------------------
# Convenience part fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def assembly_part(part_factory) -> dict:
    """An active part with assembly=True, component=False."""
    return part_factory(assembly=True, component=False)


@pytest.fixture
def component_part(part_factory) -> dict:
    """An active part with component=True."""
    return part_factory(component=True)


@pytest.fixture
def template_part(part_factory) -> dict:
    """An active part with template=True."""
    return part_factory(template=True)


@pytest.fixture
def inactive_part(part_factory, auth_client) -> dict:
    """A part that has been deactivated after creation."""
    part = part_factory()
    r = auth_client.patch(f"/api/part/{part['id']}/", json={"active": False})
    assert r.status_code == 200, f"Failed to deactivate part: {r.text}"
    return r.json()
