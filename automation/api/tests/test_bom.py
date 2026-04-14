"""
Tests for BOM (Bill of Materials) CRUD and business rules.

Covers: BOM-001 – BOM-023 from api-manual-tests.md
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
from .helpers.schemas import BOM_ITEM_SCHEMA

fake = Faker()


# ---------------------------------------------------------------------------
# BOM-001  Empty list
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_list_bom_items_empty(anon_client):
    r = anon_client.get("/api/part/bom/")
    assert_status(r, 200)
    assert_paginated(r.json())


# ---------------------------------------------------------------------------
# BOM-002  Create BOM item
# ---------------------------------------------------------------------------

@pytest.mark.smoke
@pytest.mark.positive
@pytest.mark.schema
def test_create_bom_item(bom_item_factory, assembly_part, component_part):
    bom = bom_item_factory(assembly_part["id"], component_part["id"], quantity=2)
    assert_schema(bom, BOM_ITEM_SCHEMA)
    assert bom["assembly"] == assembly_part["id"]
    assert bom["sub_part"] == component_part["id"]
    assert bom["assembly_name"] == assembly_part["name"]
    assert bom["sub_part_name"] == component_part["name"]
    assert bom["optional"] is False
    # quantity stored as string with 5 decimal places
    assert float(bom["quantity"]) == 2.0


# ---------------------------------------------------------------------------
# BOM-003  Optional flag
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_create_optional_bom_item(bom_item_factory, assembly_part, component_part):
    bom = bom_item_factory(assembly_part["id"], component_part["id"], optional=True)
    assert bom["optional"] is True


# ---------------------------------------------------------------------------
# BOM-004  Note field
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_create_bom_item_with_note(bom_item_factory, assembly_part, component_part):
    bom = bom_item_factory(assembly_part["id"], component_part["id"], note="Use premium grade")
    assert bom["note"] == "Use premium grade"


# ---------------------------------------------------------------------------
# BOM-005  Get by ID
# ---------------------------------------------------------------------------

@pytest.mark.positive
@pytest.mark.schema
def test_get_bom_item_by_id(anon_client, bom_item_factory, assembly_part, component_part):
    bom = bom_item_factory(assembly_part["id"], component_part["id"])
    r = anon_client.get(f"/api/part/bom/{bom['id']}/")
    assert_status(r, 200)
    assert_schema(r.json(), BOM_ITEM_SCHEMA)


# ---------------------------------------------------------------------------
# BOM-006  PATCH quantity
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_patch_bom_quantity(auth_client, bom_item_factory, assembly_part, component_part):
    bom = bom_item_factory(assembly_part["id"], component_part["id"])
    r = auth_client.patch(f"/api/part/bom/{bom['id']}/", json={"quantity": 5.5})
    assert_status(r, 200)
    assert float(r.json()["quantity"]) == 5.5


# ---------------------------------------------------------------------------
# BOM-007  Delete
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_delete_bom_item(auth_client, assembly_part, component_part, part_factory):
    # Create BOM item manually (without factory for cleanup control)
    comp = part_factory(component=True)
    r = auth_client.post("/api/part/bom/", json={
        "assembly": assembly_part["id"],
        "sub_part": comp["id"],
        "quantity": 1,
    })
    assert_status(r, 201)
    bom_id = r.json()["id"]

    r_del = auth_client.delete(f"/api/part/bom/{bom_id}/")
    assert_status(r_del, 204)

    r_get = auth_client.get(f"/api/part/bom/{bom_id}/")
    assert_status(r_get, 404)


# ---------------------------------------------------------------------------
# BOM-008  Filter by assembly
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_filter_bom_by_assembly(auth_client, bom_item_factory, assembly_part, component_part):
    bom = bom_item_factory(assembly_part["id"], component_part["id"])
    r = auth_client.get(f"/api/part/bom/?assembly={assembly_part['id']}&page_size=100")
    assert_status(r, 200)
    ids = [item["id"] for item in r.json()["results"]]
    assert bom["id"] in ids


# ---------------------------------------------------------------------------
# BOM-009  Filter by optional
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_filter_bom_by_optional(auth_client, bom_item_factory, assembly_part, component_part):
    bom = bom_item_factory(assembly_part["id"], component_part["id"], optional=True)
    r = auth_client.get("/api/part/bom/?optional=true&page_size=100")
    assert_status(r, 200)
    for item in r.json()["results"]:
        assert item["optional"] is True


# ---------------------------------------------------------------------------
# BOM-010  Non-assembly parent
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.business
def test_create_bom_non_assembly_parent(auth_client, part_factory):
    """Assembly must have assembly=True."""
    not_assembly = part_factory(assembly=False)
    comp = part_factory(component=True)
    r = auth_client.post("/api/part/bom/", json={
        "assembly": not_assembly["id"],
        "sub_part": comp["id"],
        "quantity": 1,
    })
    assert_status(r, 400)
    assert_field_error(r, "assembly")


# ---------------------------------------------------------------------------
# BOM-011  Non-component sub_part
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.business
def test_create_bom_non_component_subpart(auth_client, assembly_part, part_factory):
    not_component = part_factory(component=False)
    r = auth_client.post("/api/part/bom/", json={
        "assembly": assembly_part["id"],
        "sub_part": not_component["id"],
        "quantity": 1,
    })
    assert_status(r, 400)
    assert_field_error(r, "sub_part")


# ---------------------------------------------------------------------------
# BOM-012  Inactive sub_part
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.business
def test_create_bom_inactive_subpart(auth_client, assembly_part, inactive_part):
    r = auth_client.post("/api/part/bom/", json={
        "assembly": assembly_part["id"],
        "sub_part": inactive_part["id"],
        "quantity": 1,
    })
    assert_status(r, 400)
    assert_field_error(r, "sub_part")


# ---------------------------------------------------------------------------
# BOM-013  Self-referential BOM
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.business
def test_create_bom_self_referential(auth_client, part_factory):
    """A part cannot be its own BOM component."""
    part = part_factory(assembly=True, component=True)
    r = auth_client.post("/api/part/bom/", json={
        "assembly": part["id"],
        "sub_part": part["id"],
        "quantity": 1,
    })
    assert_status(r, 400)
    assert_field_error(r, "sub_part")


# ---------------------------------------------------------------------------
# BOM-014  Direct cycle A→B then B→A
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.business
def test_create_bom_direct_cycle(auth_client, part_factory, bom_item_factory):
    """BFS cycle detection blocks A→B after B→A already exists."""
    a = part_factory(assembly=True, component=True)
    b = part_factory(assembly=True, component=True)

    bom_item_factory(a["id"], b["id"])  # A → B (valid)

    r = auth_client.post("/api/part/bom/", json={  # B → A (cycle!)
        "assembly": b["id"],
        "sub_part": a["id"],
        "quantity": 1,
    })
    assert_status(r, 400)
    assert_field_error(r, "sub_part")


# ---------------------------------------------------------------------------
# BOM-015  Transitive cycle A→B→C then C→A
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.business
def test_create_bom_transitive_cycle(auth_client, part_factory, bom_item_factory):
    a = part_factory(assembly=True, component=True)
    b = part_factory(assembly=True, component=True)
    c = part_factory(assembly=True, component=True)

    bom_item_factory(a["id"], b["id"])  # A → B
    bom_item_factory(b["id"], c["id"])  # B → C

    r = auth_client.post("/api/part/bom/", json={  # C → A (transitive cycle!)
        "assembly": c["id"],
        "sub_part": a["id"],
        "quantity": 1,
    })
    assert_status(r, 400)
    assert_field_error(r, "sub_part")


# ---------------------------------------------------------------------------
# BOM-016  Duplicate (assembly, sub_part) pair
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.business
def test_create_bom_duplicate_pair(auth_client, assembly_part, component_part, bom_item_factory):
    bom_item_factory(assembly_part["id"], component_part["id"])
    r = auth_client.post("/api/part/bom/", json={
        "assembly": assembly_part["id"],
        "sub_part": component_part["id"],
        "quantity": 3,
    })
    assert_status(r, 400)
    # Should be INTEGRITY_ERROR from middleware or BAD_REQUEST from serializer
    body = r.json()
    assert body.get("error_code") in ("INTEGRITY_ERROR", "BAD_REQUEST")


# ---------------------------------------------------------------------------
# BOM-017 / BOM-018  Invalid quantities
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.parametrize("qty", [0, -1, -0.5])
def test_create_bom_invalid_quantity(auth_client, assembly_part, component_part, qty):
    r = auth_client.post("/api/part/bom/", json={
        "assembly": assembly_part["id"],
        "sub_part": component_part["id"],
        "quantity": qty,
    })
    assert_status(r, 400)
    assert_error_format(r, "BAD_REQUEST")


# ---------------------------------------------------------------------------
# BOM-019  Unauthenticated
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.auth
def test_create_bom_unauthenticated(anon_client, assembly_part, component_part):
    r = anon_client.post("/api/part/bom/", json={
        "assembly": assembly_part["id"],
        "sub_part": component_part["id"],
        "quantity": 1,
    })
    assert r.status_code in (401, 403)
    assert_error_format(r)


# ---------------------------------------------------------------------------
# BOM-020 / BOM-021  Valid decimal quantities
# ---------------------------------------------------------------------------

@pytest.mark.boundary
@pytest.mark.parametrize("qty", [0.00001, 1.12345, 1, 99999.99999])
def test_create_bom_valid_decimal_quantities(
    auth_client, part_factory, assembly_part, qty
):
    comp = part_factory(component=True)
    r = auth_client.post("/api/part/bom/", json={
        "assembly": assembly_part["id"],
        "sub_part": comp["id"],
        "quantity": qty,
    })
    assert_status(r, 201)
    assert abs(float(r.json()["quantity"]) - qty) < 0.000001
    # cleanup
    auth_client.delete(f"/api/part/bom/{r.json()['id']}/")


# ---------------------------------------------------------------------------
# BOM-022  Too many decimal places
# ---------------------------------------------------------------------------

@pytest.mark.boundary
def test_create_bom_quantity_too_many_decimals(auth_client, assembly_part, component_part):
    """6 decimal places exceeds decimal_places=5."""
    r = auth_client.post("/api/part/bom/", json={
        "assembly": assembly_part["id"],
        "sub_part": component_part["id"],
        "quantity": 1.123456,
    })
    assert_status(r, 400)


# ---------------------------------------------------------------------------
# BOM-023  Deep valid chain (no cycle)
# ---------------------------------------------------------------------------

@pytest.mark.boundary
@pytest.mark.business
def test_deep_bom_chain_no_cycle(auth_client, part_factory, bom_item_factory):
    """A→B→C→D with no cycle — all BOM items created successfully."""
    a = part_factory(assembly=True, component=True)
    b = part_factory(assembly=True, component=True)
    c = part_factory(assembly=True, component=True)
    d = part_factory(assembly=False, component=True)

    bom_item_factory(a["id"], b["id"])
    bom_item_factory(b["id"], c["id"])
    bom_item_factory(c["id"], d["id"])

    # Verify all exist
    for asm_id, sub_id in [(a["id"], b["id"]), (b["id"], c["id"]), (c["id"], d["id"])]:
        r = auth_client.get(f"/api/part/bom/?assembly={asm_id}&page_size=100")
        assert_status(r, 200)
        ids = [item["sub_part"] for item in r.json()["results"]]
        assert sub_id in ids
