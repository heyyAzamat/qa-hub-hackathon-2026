"""
Tests for PartCategory CRUD and custom actions.

Covers: CAT-001 – CAT-024 from api-manual-tests.md
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
from .helpers.schemas import PART_CATEGORY_SCHEMA, PART_CATEGORY_TREE_SCHEMA, PAGINATED_SCHEMA

fake = Faker()


# ---------------------------------------------------------------------------
# CAT-001 / CAT-002  List
# ---------------------------------------------------------------------------

@pytest.mark.smoke
@pytest.mark.positive
def test_list_categories_returns_paginated_envelope(anon_client):
    """GET /api/part/category/ — paginated response with correct structure."""
    r = anon_client.get("/api/part/category/")
    assert_status(r, 200)
    data = r.json()
    assert_paginated(data)


@pytest.mark.positive
@pytest.mark.schema
def test_list_categories_item_schema(auth_client, category_factory):
    """Each category in results matches PART_CATEGORY_SCHEMA."""
    category_factory()
    r = auth_client.get("/api/part/category/?page_size=1")
    assert_status(r, 200)
    results = r.json()["results"]
    assert len(results) >= 1
    assert_schema(results[0], PART_CATEGORY_SCHEMA)


# ---------------------------------------------------------------------------
# CAT-003  Create root category
# ---------------------------------------------------------------------------

@pytest.mark.smoke
@pytest.mark.positive
def test_create_root_category(auth_client, category_factory):
    """POST /api/part/category/ — creates root category with correct defaults."""
    cat = category_factory(name="RootCat Test", description="Root")
    assert isinstance(cat["id"], int)
    assert cat["name"] == "RootCat Test"
    assert cat["parent"] is None
    assert cat["children"] == []
    assert cat["part_count"] == 0


# ---------------------------------------------------------------------------
# CAT-004  Create child category
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_create_child_category(auth_client, category_factory):
    """Parent FK is stored correctly."""
    parent = category_factory()
    child = category_factory(parent=parent["id"])
    assert child["parent"] == parent["id"]


# ---------------------------------------------------------------------------
# CAT-005  Get by ID
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_get_category_by_id(anon_client, category_factory):
    """GET /api/part/category/{id}/ returns correct object."""
    cat = category_factory()
    r = anon_client.get(f"/api/part/category/{cat['id']}/")
    assert_status(r, 200)
    assert_schema(r.json(), PART_CATEGORY_SCHEMA)
    assert r.json()["id"] == cat["id"]


# ---------------------------------------------------------------------------
# CAT-006 / CAT-007  PUT / PATCH
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_put_category(auth_client, category_factory):
    """PUT replaces all updatable fields."""
    cat = category_factory()
    new_name = "Updated " + fake.word()
    payload = {"name": new_name, "description": "updated desc", "parent": None}
    r = auth_client.put(f"/api/part/category/{cat['id']}/", json=payload)
    assert_status(r, 200)
    assert r.json()["name"] == new_name


@pytest.mark.positive
def test_patch_category_name_only(auth_client, category_factory):
    """PATCH changes only specified field."""
    cat = category_factory(description="original desc")
    new_name = "Patched " + fake.word()
    r = auth_client.patch(f"/api/part/category/{cat['id']}/", json={"name": new_name})
    assert_status(r, 200)
    body = r.json()
    assert body["name"] == new_name
    assert body["description"] == "original desc"


# ---------------------------------------------------------------------------
# CAT-008 / CAT-009  Delete
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_delete_category(auth_client, category_factory):
    """DELETE returns 204; subsequent GET returns 404."""
    cat = category_factory()
    r = auth_client.delete(f"/api/part/category/{cat['id']}/")
    assert_status(r, 204)
    r2 = auth_client.get(f"/api/part/category/{cat['id']}/")
    assert_status(r2, 404)


# ---------------------------------------------------------------------------
# CAT-010  Root categories
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_root_categories_all_have_null_parent(auth_client, category_factory):
    """GET /api/part/category/root/ — all results have parent=null."""
    parent = category_factory()
    category_factory(parent=parent["id"])  # child — should NOT appear in root
    r = auth_client.get("/api/part/category/root/")
    assert_status(r, 200)
    data = r.json()
    assert_paginated(data)
    for item in data["results"]:
        assert item["parent"] is None, f"Non-root item in root endpoint: {item}"


# ---------------------------------------------------------------------------
# CAT-011  Category tree
# ---------------------------------------------------------------------------

@pytest.mark.positive
@pytest.mark.schema
def test_category_tree_structure(auth_client, category_factory):
    """GET /api/part/category/tree/ — returns array; each node has id, name, children."""
    parent = category_factory()
    category_factory(parent=parent["id"])
    r = auth_client.get("/api/part/category/tree/")
    assert_status(r, 200)
    tree = r.json()
    assert isinstance(tree, list)
    # Find our parent node
    nodes = [n for n in tree if n["id"] == parent["id"]]
    assert nodes, "Created category not found in tree response"
    assert_schema(nodes[0], PART_CATEGORY_TREE_SCHEMA)
    assert isinstance(nodes[0]["children"], list)


# ---------------------------------------------------------------------------
# CAT-012  Filter by parent
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_filter_by_parent(auth_client, category_factory):
    """?parent=<id> returns only direct children."""
    parent = category_factory()
    child1 = category_factory(parent=parent["id"])
    child2 = category_factory(parent=parent["id"])
    other = category_factory()  # unrelated — must not appear

    r = auth_client.get(f"/api/part/category/?parent={parent['id']}&page_size=100")
    assert_status(r, 200)
    ids = [item["id"] for item in r.json()["results"]]
    assert child1["id"] in ids
    assert child2["id"] in ids
    assert other["id"] not in ids


# ---------------------------------------------------------------------------
# CAT-013  Search
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_search_category_by_name(auth_client, category_factory):
    """?search=<term> matches category name."""
    unique_token = "SEARCHTOKEN" + fake.lexify("????").upper()
    cat = category_factory(name=f"{unique_token} Category")
    r = auth_client.get(f"/api/part/category/?search={unique_token}&page_size=100")
    assert_status(r, 200)
    ids = [item["id"] for item in r.json()["results"]]
    assert cat["id"] in ids, "Created category not found in search results"


# ---------------------------------------------------------------------------
# CAT-014  Ordering
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_ordering_by_name_desc(auth_client, category_factory):
    """?ordering=-name — results sorted descending by name."""
    category_factory(name="ZZZ Category")
    category_factory(name="AAA Category")
    r = auth_client.get("/api/part/category/?ordering=-name&page_size=100")
    assert_status(r, 200)
    names = [item["name"] for item in r.json()["results"]]
    assert names == sorted(names, reverse=True), f"Not sorted descending: {names}"


# ---------------------------------------------------------------------------
# CAT-015  part_count annotation
# ---------------------------------------------------------------------------

@pytest.mark.positive
@pytest.mark.business
def test_part_count_annotation(auth_client, category_factory, part_factory):
    """part_count reflects number of parts directly in the category."""
    cat = category_factory()
    part_factory(category_id=cat["id"])
    part_factory(category_id=cat["id"])
    r = auth_client.get(f"/api/part/category/{cat['id']}/")
    assert_status(r, 200)
    assert r.json()["part_count"] == 2


# ---------------------------------------------------------------------------
# CAT-016  Missing name
# ---------------------------------------------------------------------------

@pytest.mark.negative
def test_create_category_without_name(auth_client):
    """POST without name returns 400."""
    r = auth_client.post("/api/part/category/", json={"description": "No name"})
    assert_status(r, 400)
    assert_error_format(r, "BAD_REQUEST")


# ---------------------------------------------------------------------------
# CAT-017  Name too long
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.boundary
def test_create_category_name_too_long(auth_client):
    """POST with 101-char name returns 400."""
    r = auth_client.post("/api/part/category/", json={"name": "A" * 101, "description": "ok"})
    assert_status(r, 400)
    assert_error_format(r, "BAD_REQUEST")


# ---------------------------------------------------------------------------
# CAT-018  Circular parent (self)
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.business
def test_circular_parent_self(auth_client, category_factory):
    """PATCH setting parent=self returns 400 with cycle message."""
    cat = category_factory()
    r = auth_client.patch(f"/api/part/category/{cat['id']}/", json={"parent": cat["id"]})
    assert_status(r, 400)
    err = assert_error_format(r, "BAD_REQUEST")
    assert "parent" in err.get("details", {}), "Expected field error on 'parent'"


# ---------------------------------------------------------------------------
# CAT-019  Circular parent (indirect)
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.business
def test_circular_parent_indirect(auth_client, category_factory):
    """Setting grandparent's parent to its grandchild creates a cycle — blocked."""
    grandparent = category_factory()
    child = category_factory(parent=grandparent["id"])
    grandchild = category_factory(parent=child["id"])

    # Try to make grandchild a parent of grandparent → cycle
    r = auth_client.patch(
        f"/api/part/category/{grandparent['id']}/",
        json={"parent": grandchild["id"]},
    )
    assert_status(r, 400)
    assert_error_format(r, "BAD_REQUEST")


# ---------------------------------------------------------------------------
# CAT-020  Non-existent
# ---------------------------------------------------------------------------

@pytest.mark.negative
def test_get_nonexistent_category(anon_client):
    r = anon_client.get("/api/part/category/999999999/")
    assert_status(r, 404)
    assert_error_format(r, "NOT_FOUND")


# ---------------------------------------------------------------------------
# CAT-021  Delete without auth
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.auth
def test_delete_category_unauthenticated(anon_client, category_factory):
    cat = category_factory()
    r = anon_client.delete(f"/api/part/category/{cat['id']}/")
    assert r.status_code in (401, 403)
    assert_error_format(r)


# ---------------------------------------------------------------------------
# CAT-022 / CAT-023  Boundary: name length
# ---------------------------------------------------------------------------

@pytest.mark.boundary
def test_create_category_name_exactly_100_chars(auth_client, category_factory):
    """Name of 100 chars is accepted."""
    cat = category_factory(name="A" * 100)
    assert cat["name"] == "A" * 100


@pytest.mark.boundary
def test_create_category_name_101_chars_rejected(auth_client):
    """Name of 101 chars is rejected."""
    r = auth_client.post("/api/part/category/", json={"name": "A" * 101, "description": "ok"})
    assert_status(r, 400)


# ---------------------------------------------------------------------------
# CAT-024  Root endpoint when empty
# ---------------------------------------------------------------------------

@pytest.mark.boundary
def test_root_endpoint_no_categories(anon_client):
    """Root endpoint works even when no root categories exist (may have data from other tests)."""
    r = anon_client.get("/api/part/category/root/")
    assert_status(r, 200)
    data = r.json()
    assert_paginated(data)
    # All returned items must be root items
    for item in data["results"]:
        assert item["parent"] is None
