"""
Tests for Part CRUD, filtering, search and ordering.

Covers: PART-001 – PART-033 from api-manual-tests.md
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
from .helpers.schemas import PART_SCHEMA, PAGINATED_SCHEMA

fake = Faker()


# ---------------------------------------------------------------------------
# PART-001  Empty list
# ---------------------------------------------------------------------------

@pytest.mark.smoke
@pytest.mark.positive
def test_list_parts_returns_paginated(anon_client):
    """GET /api/part/ returns paginated envelope."""
    r = anon_client.get("/api/part/")
    assert_status(r, 200)
    assert_paginated(r.json())


# ---------------------------------------------------------------------------
# PART-002  Create minimal part
# ---------------------------------------------------------------------------

@pytest.mark.smoke
@pytest.mark.positive
@pytest.mark.schema
def test_create_minimal_part(part_factory):
    """POST with name+description returns 201 with correct defaults."""
    part = part_factory(name="Resistor 10k", description="10k ohm resistor")
    assert_schema(part, PART_SCHEMA)
    assert part["active"] is True
    assert part["virtual"] is False
    assert part["template"] is False
    assert part["assembly"] is False
    assert part["component"] is True
    assert part["IPN"] is None
    assert part["parameters"] == []
    assert part["revision_of"] is None


# ---------------------------------------------------------------------------
# PART-003  Create with IPN
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_create_part_with_ipn(part_factory):
    unique_ipn = "IPN-" + fake.unique.lexify("??????").upper()
    part = part_factory(IPN=unique_ipn)
    assert part["IPN"] == unique_ipn


# ---------------------------------------------------------------------------
# PART-004  Create with category
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_create_part_with_category(auth_client, part_factory, category_factory):
    """category_id (write) maps to category object (read)."""
    cat = category_factory()
    part = part_factory(category_id=cat["id"])
    assert part["category"] is not None
    assert part["category"]["id"] == cat["id"]
    assert "category_id" not in part  # write-only field not in response


# ---------------------------------------------------------------------------
# PART-005  All flags
# ---------------------------------------------------------------------------

@pytest.mark.positive
@pytest.mark.parametrize("flag,value", [
    ("active", True), ("active", False),
    ("virtual", True), ("virtual", False),
    ("template", True), ("template", False),
    ("assembly", True), ("assembly", False),
    ("component", True), ("component", False),
])
def test_create_part_boolean_flags(part_factory, flag, value):
    """Each boolean flag is stored and returned correctly."""
    part = part_factory(**{flag: value})
    assert part[flag] is value


# ---------------------------------------------------------------------------
# PART-006  Get by ID
# ---------------------------------------------------------------------------

@pytest.mark.positive
@pytest.mark.schema
def test_get_part_by_id(anon_client, part_factory):
    part = part_factory()
    r = anon_client.get(f"/api/part/{part['id']}/")
    assert_status(r, 200)
    body = r.json()
    assert_schema(body, PART_SCHEMA)
    assert body["id"] == part["id"]


# ---------------------------------------------------------------------------
# PART-007  PUT full update
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_put_part_full_update(auth_client, part_factory):
    part = part_factory()
    new_name = "Updated " + fake.catch_phrase()
    payload = {
        "name": new_name,
        "description": "Updated description",
        "active": True,
        "virtual": False,
        "template": False,
        "assembly": False,
        "component": True,
    }
    r = auth_client.put(f"/api/part/{part['id']}/", json=payload)
    assert_status(r, 200)
    assert r.json()["name"] == new_name


# ---------------------------------------------------------------------------
# PART-008  PATCH active flag
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_patch_active_flag(auth_client, part_factory):
    """Deactivate a part that has no active child revisions."""
    part = part_factory(active=True)
    r = auth_client.patch(f"/api/part/{part['id']}/", json={"active": False})
    assert_status(r, 200)
    assert r.json()["active"] is False


# ---------------------------------------------------------------------------
# PART-009  Delete
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_delete_part(auth_client, part_factory):
    part = part_factory()
    r = auth_client.delete(f"/api/part/{part['id']}/")
    assert_status(r, 204)
    r2 = auth_client.get(f"/api/part/{part['id']}/")
    assert_status(r2, 404)


# ---------------------------------------------------------------------------
# PART-010 / PART-011  Filter by active
# ---------------------------------------------------------------------------

@pytest.mark.positive
@pytest.mark.parametrize("active_value", [True, False])
def test_filter_by_active(auth_client, part_factory, active_value):
    part_factory(active=active_value)
    r = auth_client.get(f"/api/part/?active={str(active_value).lower()}&page_size=100")
    assert_status(r, 200)
    for item in r.json()["results"]:
        assert item["active"] is active_value


# ---------------------------------------------------------------------------
# PART-012  Filter by category
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_filter_by_category(auth_client, part_factory, category_factory):
    cat = category_factory()
    part = part_factory(category_id=cat["id"])
    other_part = part_factory()  # no category

    r = auth_client.get(f"/api/part/?category={cat['id']}&page_size=100")
    assert_status(r, 200)
    ids = [item["id"] for item in r.json()["results"]]
    assert part["id"] in ids
    assert other_part["id"] not in ids


# ---------------------------------------------------------------------------
# PART-013  include_child_categories
# ---------------------------------------------------------------------------

@pytest.mark.positive
@pytest.mark.business
def test_include_child_categories(auth_client, part_factory, category_factory):
    """Parts in descendant categories are included when include_child_categories=true."""
    root = category_factory()
    child = category_factory(parent=root["id"])
    grandchild = category_factory(parent=child["id"])

    part_root = part_factory(category_id=root["id"])
    part_deep = part_factory(category_id=grandchild["id"])
    part_other = part_factory()  # unrelated

    r = auth_client.get(
        f"/api/part/?category={root['id']}&include_child_categories=true&page_size=100"
    )
    assert_status(r, 200)
    ids = [item["id"] for item in r.json()["results"]]
    assert part_root["id"] in ids
    assert part_deep["id"] in ids
    assert part_other["id"] not in ids


# ---------------------------------------------------------------------------
# PART-014 / PART-015  Search
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_search_by_name(auth_client, part_factory):
    token = "SRCHNAME" + fake.lexify("????").upper()
    part = part_factory(name=f"{token} Part")
    r = auth_client.get(f"/api/part/?search={token}&page_size=100")
    assert_status(r, 200)
    ids = [item["id"] for item in r.json()["results"]]
    assert part["id"] in ids


@pytest.mark.positive
def test_search_by_ipn(auth_client, part_factory):
    unique_ipn = "SRCHIPN-" + fake.unique.lexify("??????").upper()
    part = part_factory(IPN=unique_ipn)
    r = auth_client.get(f"/api/part/?search={unique_ipn}&page_size=100")
    assert_status(r, 200)
    ids = [item["id"] for item in r.json()["results"]]
    assert part["id"] in ids


# ---------------------------------------------------------------------------
# PART-016  Ordering
# ---------------------------------------------------------------------------

@pytest.mark.positive
@pytest.mark.parametrize("ordering", ["name", "-name", "id", "-id", "creation_date", "-creation_date"])
def test_ordering(auth_client, part_factory, ordering):
    """Valid ordering fields are accepted without error."""
    part_factory()
    part_factory()
    r = auth_client.get(f"/api/part/?ordering={ordering}&page_size=5")
    assert_status(r, 200)


# ---------------------------------------------------------------------------
# PART-017  Missing name
# ---------------------------------------------------------------------------

@pytest.mark.negative
def test_create_part_without_name(auth_client):
    r = auth_client.post("/api/part/", json={"description": "No name"})
    assert_status(r, 400)
    assert_error_format(r, "BAD_REQUEST")


# ---------------------------------------------------------------------------
# PART-018  Missing description
# ---------------------------------------------------------------------------

@pytest.mark.negative
def test_create_part_without_description(auth_client):
    r = auth_client.post("/api/part/", json={"name": "Part without desc"})
    assert_status(r, 400)
    assert_error_format(r, "BAD_REQUEST")
    assert_field_error(r, "description")


# ---------------------------------------------------------------------------
# PART-019 / PART-020  Whitespace-only fields
# ---------------------------------------------------------------------------

@pytest.mark.negative
def test_create_part_whitespace_name(auth_client):
    r = auth_client.post("/api/part/", json={"name": "   ", "description": "ok"})
    assert_status(r, 400)
    assert_error_format(r, "BAD_REQUEST")
    assert_field_error(r, "name")


@pytest.mark.negative
def test_create_part_whitespace_description(auth_client):
    r = auth_client.post("/api/part/", json={"name": "Part", "description": "\t\n"})
    assert_status(r, 400)
    assert_error_format(r, "BAD_REQUEST")
    assert_field_error(r, "description")


# ---------------------------------------------------------------------------
# PART-021  Duplicate IPN
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.business
def test_create_part_duplicate_ipn(auth_client, part_factory):
    unique_ipn = "DUPE-" + fake.unique.lexify("??????").upper()
    part_factory(IPN=unique_ipn)
    r = auth_client.post(
        "/api/part/",
        json={"name": "Part2", "description": "desc", "IPN": unique_ipn},
    )
    assert_status(r, 400)
    err = assert_error_format(r, "BAD_REQUEST")
    # IPN uniqueness error surfaced in details or message
    body_str = str(err)
    assert "IPN" in body_str or "ipn" in body_str.lower() or "exist" in body_str.lower()


# ---------------------------------------------------------------------------
# PART-022  Deactivate with active revisions
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.business
def test_deactivate_part_with_active_revision(auth_client, part_factory):
    """Cannot deactivate a part that has active child revisions."""
    parent = part_factory(active=True)
    # Create revision via API
    r = auth_client.post(
        f"/api/part/{parent['id']}/create_revision/",
        json={"revision": "B"},
    )
    assert r.status_code == 201, f"Could not create revision: {r.text}"

    r2 = auth_client.patch(f"/api/part/{parent['id']}/", json={"active": False})
    assert_status(r2, 400)
    assert_error_format(r2, "BAD_REQUEST")


# ---------------------------------------------------------------------------
# PART-023  Remove assembly flag with BOM items
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.business
def test_remove_assembly_flag_with_bom_items(auth_client, part_factory, bom_item_factory):
    """Cannot unset assembly=True when BOM items exist."""
    asm = part_factory(assembly=True, component=False)
    comp = part_factory(component=True)
    bom_item_factory(asm["id"], comp["id"])

    r = auth_client.patch(f"/api/part/{asm['id']}/", json={"assembly": False})
    assert_status(r, 400)
    assert_field_error(r, "assembly")


# ---------------------------------------------------------------------------
# PART-024  Non-existent category_id
# ---------------------------------------------------------------------------

@pytest.mark.negative
def test_create_part_nonexistent_category(auth_client):
    r = auth_client.post(
        "/api/part/",
        json={"name": "Part", "description": "desc", "category_id": 999999999},
    )
    assert_status(r, 400)
    assert_error_format(r, "BAD_REQUEST")


# ---------------------------------------------------------------------------
# PART-025  Non-existent part
# ---------------------------------------------------------------------------

@pytest.mark.negative
def test_get_nonexistent_part(anon_client):
    r = anon_client.get("/api/part/999999999/")
    assert_status(r, 404)
    assert_error_format(r, "NOT_FOUND")


# ---------------------------------------------------------------------------
# PART-026  POST unauthenticated
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.auth
def test_create_part_unauthenticated(anon_client):
    r = anon_client.post("/api/part/", json={"name": "Part", "description": "desc"})
    assert r.status_code in (401, 403)
    assert_error_format(r)


# ---------------------------------------------------------------------------
# PART-027 / PART-028  IPN max_length
# ---------------------------------------------------------------------------

@pytest.mark.boundary
def test_create_part_ipn_max_length(part_factory):
    """IPN of exactly 50 chars is accepted."""
    part = part_factory(IPN="A" * 50)
    assert part["IPN"] == "A" * 50


@pytest.mark.boundary
def test_create_part_ipn_too_long(auth_client):
    """IPN of 51 chars is rejected."""
    r = auth_client.post(
        "/api/part/",
        json={"name": "Part", "description": "desc", "IPN": "A" * 51},
    )
    assert_status(r, 400)
    assert_error_format(r, "BAD_REQUEST")


# ---------------------------------------------------------------------------
# PART-029 / PART-030  Name max_length
# ---------------------------------------------------------------------------

@pytest.mark.boundary
def test_create_part_name_max_length(part_factory):
    """Name of exactly 200 chars is accepted."""
    part = part_factory(name="A" * 200)
    assert part["name"] == "A" * 200


@pytest.mark.boundary
def test_create_part_name_too_long(auth_client):
    """Name of 201 chars is rejected."""
    r = auth_client.post(
        "/api/part/",
        json={"name": "A" * 201, "description": "desc"},
    )
    assert_status(r, 400)
    assert_error_format(r, "BAD_REQUEST")


# ---------------------------------------------------------------------------
# PART-031  Two parts with IPN=null
# ---------------------------------------------------------------------------

@pytest.mark.boundary
@pytest.mark.business
def test_multiple_parts_with_null_ipn(part_factory):
    """NULL IPN does not violate unique constraint (SQL NULL != NULL)."""
    part1 = part_factory(IPN=None)
    part2 = part_factory(IPN=None)
    assert part1["IPN"] is None
    assert part2["IPN"] is None
    assert part1["id"] != part2["id"]


# ---------------------------------------------------------------------------
# PART-032 / PART-033  IPN update conflicts
# ---------------------------------------------------------------------------

@pytest.mark.boundary
@pytest.mark.business
def test_update_ipn_to_existing_ipn(auth_client, part_factory):
    """PATCH IPN to another part's IPN is rejected."""
    ipn_taken = "TAKEN-" + fake.unique.lexify("??????").upper()
    part_factory(IPN=ipn_taken)
    part2 = part_factory()
    r = auth_client.patch(f"/api/part/{part2['id']}/", json={"IPN": ipn_taken})
    assert_status(r, 400)
    assert_error_format(r, "BAD_REQUEST")


@pytest.mark.boundary
def test_update_ipn_to_same_value(auth_client, part_factory):
    """PATCH IPN to its own existing value is idempotent (200)."""
    ipn = "SAME-" + fake.unique.lexify("??????").upper()
    part = part_factory(IPN=ipn)
    r = auth_client.patch(f"/api/part/{part['id']}/", json={"IPN": ipn})
    assert_status(r, 200)
