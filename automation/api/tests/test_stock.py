"""
Tests for StockItem CRUD and business rules.

Covers: STK-001 – STK-024 from api-manual-tests.md
"""
import pytest
from faker import Faker

from .helpers.assertions import (
    assert_status,
    assert_schema,
    assert_paginated,
    assert_error_format,
    assert_field_error,
)
from .helpers.schemas import STOCK_ITEM_SCHEMA

fake = Faker()


# ---------------------------------------------------------------------------
# STK-001  Empty list
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_list_stock_items_empty(anon_client):
    r = anon_client.get("/api/part/stock/")
    assert_status(r, 200)
    assert_paginated(r.json())


# ---------------------------------------------------------------------------
# STK-002  Create stock item
# ---------------------------------------------------------------------------

@pytest.mark.smoke
@pytest.mark.positive
@pytest.mark.schema
def test_create_stock_item(stock_item_factory, part_factory):
    part = part_factory()
    stock = stock_item_factory(part["id"], quantity=100)
    assert_schema(stock, STOCK_ITEM_SCHEMA)
    assert stock["part"] == part["id"]
    assert stock["part_name"] == part["name"]
    assert float(stock["quantity"]) == 100.0
    assert "created" in stock


# ---------------------------------------------------------------------------
# STK-003  Location and batch
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_create_stock_with_location_and_batch(stock_item_factory, part_factory):
    part = part_factory()
    stock = stock_item_factory(part["id"], quantity=50, location="Shelf A-1", batch="LOT-2026-001")
    assert stock["location"] == "Shelf A-1"
    assert stock["batch"] == "LOT-2026-001"


# ---------------------------------------------------------------------------
# STK-004  Quantity=0 is allowed
# ---------------------------------------------------------------------------

@pytest.mark.positive
@pytest.mark.boundary
def test_create_stock_zero_quantity(stock_item_factory, part_factory):
    """Zero quantity is valid (not negative check, not zero check in model)."""
    part = part_factory()
    stock = stock_item_factory(part["id"], quantity=0)
    assert float(stock["quantity"]) == 0.0


# ---------------------------------------------------------------------------
# STK-005  Get by ID
# ---------------------------------------------------------------------------

@pytest.mark.positive
@pytest.mark.schema
def test_get_stock_item_by_id(anon_client, stock_item_factory, part_factory):
    part = part_factory()
    stock = stock_item_factory(part["id"])
    r = anon_client.get(f"/api/part/stock/{stock['id']}/")
    assert_status(r, 200)
    assert_schema(r.json(), STOCK_ITEM_SCHEMA)


# ---------------------------------------------------------------------------
# STK-006  PATCH quantity
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_patch_stock_quantity(auth_client, stock_item_factory, part_factory):
    part = part_factory()
    stock = stock_item_factory(part["id"])
    r = auth_client.patch(f"/api/part/stock/{stock['id']}/", json={"quantity": 200})
    assert_status(r, 200)
    assert float(r.json()["quantity"]) == 200.0


# ---------------------------------------------------------------------------
# STK-007  PUT full update
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_put_stock_item(auth_client, stock_item_factory, part_factory):
    part = part_factory()
    stock = stock_item_factory(part["id"], quantity=10)
    payload = {"part": part["id"], "quantity": 75, "location": "B-2", "batch": None}
    r = auth_client.put(f"/api/part/stock/{stock['id']}/", json=payload)
    assert_status(r, 200)
    body = r.json()
    assert float(body["quantity"]) == 75.0
    assert body["location"] == "B-2"
    assert body["batch"] is None


# ---------------------------------------------------------------------------
# STK-008  Delete
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_delete_stock_item(auth_client, part_factory):
    part = part_factory()
    r = auth_client.post("/api/part/stock/", json={"part": part["id"], "quantity": 1})
    assert_status(r, 201)
    stock_id = r.json()["id"]

    r_del = auth_client.delete(f"/api/part/stock/{stock_id}/")
    assert_status(r_del, 204)

    r_get = auth_client.get(f"/api/part/stock/{stock_id}/")
    assert_status(r_get, 404)


# ---------------------------------------------------------------------------
# STK-009  Filter by part
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_filter_stock_by_part(auth_client, stock_item_factory, part_factory):
    part = part_factory()
    stock = stock_item_factory(part["id"])
    r = auth_client.get(f"/api/part/stock/?part={part['id']}&page_size=100")
    assert_status(r, 200)
    ids = [item["id"] for item in r.json()["results"]]
    assert stock["id"] in ids


# ---------------------------------------------------------------------------
# STK-010 / STK-011  Filter by location and batch
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_filter_stock_by_location(auth_client, stock_item_factory, part_factory):
    part = part_factory()
    stock = stock_item_factory(part["id"], location="UNIQUELOC-XYZ")
    r = auth_client.get("/api/part/stock/?location=UNIQUELOC-XYZ&page_size=100")
    assert_status(r, 200)
    ids = [item["id"] for item in r.json()["results"]]
    assert stock["id"] in ids


@pytest.mark.positive
def test_filter_stock_by_batch(auth_client, stock_item_factory, part_factory):
    part = part_factory()
    stock = stock_item_factory(part["id"], batch="BATCH-UNIQUETEST-001")
    r = auth_client.get("/api/part/stock/?batch=BATCH-UNIQUETEST-001&page_size=100")
    assert_status(r, 200)
    ids = [item["id"] for item in r.json()["results"]]
    assert stock["id"] in ids


# ---------------------------------------------------------------------------
# STK-012  Ordering
# ---------------------------------------------------------------------------

@pytest.mark.positive
@pytest.mark.parametrize("ordering", ["quantity", "-quantity", "created", "-created"])
def test_stock_ordering(auth_client, ordering):
    r = auth_client.get(f"/api/part/stock/?ordering={ordering}&page_size=5")
    assert_status(r, 200)


# ---------------------------------------------------------------------------
# STK-013  Template part blocked
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.business
def test_create_stock_for_template_part(auth_client, template_part):
    """Template parts cannot have stock items."""
    r = auth_client.post("/api/part/stock/", json={"part": template_part["id"], "quantity": 10})
    assert_status(r, 400)
    assert_field_error(r, "part")


# ---------------------------------------------------------------------------
# STK-014  Negative quantity
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.parametrize("qty", [-1, -0.5, -0.00001])
def test_create_stock_negative_quantity(auth_client, part_factory, qty):
    part = part_factory()
    r = auth_client.post("/api/part/stock/", json={"part": part["id"], "quantity": qty})
    assert_status(r, 400)
    assert_error_format(r, "BAD_REQUEST")
    assert_field_error(r, "quantity")


# ---------------------------------------------------------------------------
# STK-015  Missing part field
# ---------------------------------------------------------------------------

@pytest.mark.negative
def test_create_stock_without_part(auth_client):
    r = auth_client.post("/api/part/stock/", json={"quantity": 10})
    assert_status(r, 400)
    assert_field_error(r, "part")


# ---------------------------------------------------------------------------
# STK-016  Non-existent part
# ---------------------------------------------------------------------------

@pytest.mark.negative
def test_create_stock_nonexistent_part(auth_client):
    r = auth_client.post("/api/part/stock/", json={"part": 999999999, "quantity": 10})
    assert_status(r, 400)
    assert_error_format(r, "BAD_REQUEST")


# ---------------------------------------------------------------------------
# STK-017  Non-existent stock item
# ---------------------------------------------------------------------------

@pytest.mark.negative
def test_get_nonexistent_stock_item(anon_client):
    r = anon_client.get("/api/part/stock/999999999/")
    assert_status(r, 404)
    assert_error_format(r, "NOT_FOUND")


# ---------------------------------------------------------------------------
# STK-018  Unauthenticated
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.auth
def test_create_stock_unauthenticated(anon_client, part_factory):
    part = part_factory()
    r = anon_client.post("/api/part/stock/", json={"part": part["id"], "quantity": 10})
    assert r.status_code in (401, 403)
    assert_error_format(r)


# ---------------------------------------------------------------------------
# STK-019 / STK-020  Decimal quantity boundaries
# ---------------------------------------------------------------------------

@pytest.mark.boundary
@pytest.mark.parametrize("qty", [0, 0.00001, 1, 1000.12345])
def test_create_stock_valid_quantities(auth_client, part_factory, qty):
    part = part_factory()
    r = auth_client.post("/api/part/stock/", json={"part": part["id"], "quantity": qty})
    assert_status(r, 201)
    assert abs(float(r.json()["quantity"]) - qty) < 0.000001
    auth_client.delete(f"/api/part/stock/{r.json()['id']}/")


@pytest.mark.boundary
def test_create_stock_quantity_too_many_decimals(auth_client, part_factory):
    part = part_factory()
    r = auth_client.post("/api/part/stock/", json={"part": part["id"], "quantity": 1.123456})
    assert_status(r, 400)


# ---------------------------------------------------------------------------
# STK-021 / STK-022  location max_length
# ---------------------------------------------------------------------------

@pytest.mark.boundary
def test_create_stock_location_max_length(auth_client, stock_item_factory, part_factory):
    part = part_factory()
    stock = stock_item_factory(part["id"], location="A" * 200)
    assert stock["location"] == "A" * 200


@pytest.mark.boundary
def test_create_stock_location_too_long(auth_client, part_factory):
    part = part_factory()
    r = auth_client.post(
        "/api/part/stock/",
        json={"part": part["id"], "quantity": 1, "location": "A" * 201},
    )
    assert_status(r, 400)


# ---------------------------------------------------------------------------
# STK-023 / STK-024  batch max_length
# ---------------------------------------------------------------------------

@pytest.mark.boundary
def test_create_stock_batch_max_length(auth_client, stock_item_factory, part_factory):
    part = part_factory()
    stock = stock_item_factory(part["id"], batch="B" * 100)
    assert stock["batch"] == "B" * 100


@pytest.mark.boundary
def test_create_stock_batch_too_long(auth_client, part_factory):
    part = part_factory()
    r = auth_client.post(
        "/api/part/stock/",
        json={"part": part["id"], "quantity": 1, "batch": "B" * 101},
    )
    assert_status(r, 400)
