"""
Tests for pagination, filtering, search and ordering across all endpoints.

Covers: PAG-001 – PAG-012 from api-manual-tests.md
"""
import pytest
from faker import Faker

from .helpers.assertions import assert_status, assert_paginated

fake = Faker()


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_default_page_size_is_25(auth_client, part_factory):
    """Creating 26 parts and requesting the default list gives 25 results with next != null."""
    # Create 26 parts
    for _ in range(26):
        part_factory()

    r = auth_client.get("/api/part/")
    assert_status(r, 200)
    data = r.json()
    assert_paginated(data)
    assert data["count"] >= 26
    assert len(data["results"]) == 25
    assert data["next"] is not None


@pytest.mark.positive
def test_custom_page_size(auth_client, part_factory):
    """?page_size=5 returns exactly 5 items."""
    for _ in range(6):
        part_factory()

    r = auth_client.get("/api/part/?page_size=5")
    assert_status(r, 200)
    assert len(r.json()["results"]) == 5


@pytest.mark.positive
def test_second_page_offset(auth_client, part_factory):
    """?page=2&page_size=5 returns a different set of 5 items."""
    ids_created = [part_factory()["id"] for _ in range(10)]

    r1 = auth_client.get("/api/part/?page_size=5&page=1&ordering=id")
    r2 = auth_client.get("/api/part/?page_size=5&page=2&ordering=id")
    assert_status(r1, 200)
    assert_status(r2, 200)

    ids_page1 = {item["id"] for item in r1.json()["results"]}
    ids_page2 = {item["id"] for item in r2.json()["results"]}
    assert ids_page1.isdisjoint(ids_page2), "Pages 1 and 2 have overlapping items"


@pytest.mark.boundary
def test_max_page_size_100(auth_client, part_factory):
    """?page_size=100 never returns more than 100 items."""
    r = auth_client.get("/api/part/?page_size=100")
    assert_status(r, 200)
    assert len(r.json()["results"]) <= 100


# ---------------------------------------------------------------------------
# Filtering — parts
# ---------------------------------------------------------------------------

@pytest.mark.positive
@pytest.mark.parametrize("flag", ["assembly", "template", "virtual", "component"])
def test_filter_parts_by_boolean_flag(auth_client, part_factory, flag):
    """?{flag}=true returns only parts with that flag set."""
    part_factory(**{flag: True})
    r = auth_client.get(f"/api/part/?{flag}=true&page_size=100")
    assert_status(r, 200)
    for item in r.json()["results"]:
        assert item[flag] is True, f"Part {item['id']} has {flag}=False in ?{flag}=true filter"


@pytest.mark.positive
@pytest.mark.business
def test_include_child_categories_nonexistent(auth_client):
    """Non-existent category with include_child_categories returns empty list."""
    r = auth_client.get("/api/part/?category=999999999&include_child_categories=true")
    assert_status(r, 200)
    data = r.json()
    assert data["count"] == 0
    assert data["results"] == []


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_search_no_matches(auth_client):
    r = auth_client.get("/api/part/?search=NONEXISTENT_XYZ_99999_UNIQUE")
    assert_status(r, 200)
    assert r.json()["count"] == 0


@pytest.mark.positive
def test_category_search_no_matches(auth_client):
    r = auth_client.get("/api/part/category/?search=NONEXISTENT_XYZ_99999_UNIQUE")
    assert_status(r, 200)
    assert r.json()["count"] == 0


# ---------------------------------------------------------------------------
# Ordering — parts
# ---------------------------------------------------------------------------

@pytest.mark.positive
@pytest.mark.parametrize("ordering,field", [
    ("name", "name"),
    ("-name", "name"),
    ("id", "id"),
    ("-id", "id"),
])
def test_parts_ordering_is_correct(auth_client, part_factory, ordering, field):
    """Results are sorted in the expected direction."""
    for _ in range(3):
        part_factory()

    r = auth_client.get(f"/api/part/?ordering={ordering}&page_size=50")
    assert_status(r, 200)
    results = r.json()["results"]
    if len(results) < 2:
        pytest.skip("Not enough results to check ordering")

    values = [item[field] for item in results if item[field] is not None]
    if len(values) < 2:
        pytest.skip("Not enough non-null values")

    if ordering.startswith("-"):
        assert values == sorted(values, reverse=True), f"Not sorted desc by {field}"
    else:
        assert values == sorted(values), f"Not sorted asc by {field}"


# ---------------------------------------------------------------------------
# Category filtering
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_category_filter_by_parent_direct_children_only(auth_client, category_factory):
    """?parent=<id> does NOT include grandchildren."""
    parent = category_factory()
    child = category_factory(parent=parent["id"])
    grandchild = category_factory(parent=child["id"])

    r = auth_client.get(f"/api/part/category/?parent={parent['id']}&page_size=100")
    assert_status(r, 200)
    ids = [item["id"] for item in r.json()["results"]]
    assert child["id"] in ids
    assert grandchild["id"] not in ids


@pytest.mark.positive
@pytest.mark.business
def test_include_child_categories_deep_hierarchy(auth_client, part_factory, category_factory):
    """Parts in deep nested categories are found with include_child_categories=true."""
    root = category_factory()
    child = category_factory(parent=root["id"])
    grandchild = category_factory(parent=child["id"])
    deep_part = part_factory(category_id=grandchild["id"])

    r = auth_client.get(
        f"/api/part/?category={root['id']}&include_child_categories=true&page_size=100"
    )
    assert_status(r, 200)
    ids = [item["id"] for item in r.json()["results"]]
    assert deep_part["id"] in ids, "Deep nested part not found with include_child_categories=true"


# ---------------------------------------------------------------------------
# BOM and Stock filtering smoke
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_bom_list_accepts_filter(auth_client):
    r = auth_client.get("/api/part/bom/?optional=false&page_size=5")
    assert_status(r, 200)
    assert_paginated(r.json())


@pytest.mark.positive
def test_stock_list_accepts_ordering(auth_client):
    r = auth_client.get("/api/part/stock/?ordering=-created&page_size=5")
    assert_status(r, 200)
    assert_paginated(r.json())
