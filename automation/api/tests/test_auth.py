"""
Tests for authentication and authorization (IsAuthenticatedOrReadOnly).

All write endpoints must reject unauthenticated requests.
All read endpoints must allow anonymous access.
"""
import pytest

from .helpers.assertions import assert_status, assert_error_format


# ---------------------------------------------------------------------------
# Helpers: create minimal objects for use in parametrized write tests
# ---------------------------------------------------------------------------

def _get_or_create_resources(auth_client) -> dict:
    """Create one of each resource and return their IDs for use in URL templates."""
    cat_r = auth_client.post("/api/part/category/", json={"name": "AuthTestCat", "description": "x"})
    cat_id = cat_r.json()["id"] if cat_r.status_code == 201 else 1

    part_r = auth_client.post("/api/part/", json={"name": "AuthTestPart", "description": "x"})
    part_id = part_r.json()["id"] if part_r.status_code == 201 else 1

    asm_r = auth_client.post("/api/part/", json={"name": "AuthTestAsm", "description": "x", "assembly": True, "component": False})
    asm_id = asm_r.json()["id"] if asm_r.status_code == 201 else 1

    comp_r = auth_client.post("/api/part/", json={"name": "AuthTestComp", "description": "x", "component": True})
    comp_id = comp_r.json()["id"] if comp_r.status_code == 201 else 1

    bom_r = auth_client.post("/api/part/bom/", json={"assembly": asm_id, "sub_part": comp_id, "quantity": 1})
    bom_id = bom_r.json()["id"] if bom_r.status_code == 201 else 1

    stock_r = auth_client.post("/api/part/stock/", json={"part": part_id, "quantity": 1})
    stock_id = stock_r.json()["id"] if stock_r.status_code == 201 else 1

    return {
        "cat_id": cat_id,
        "part_id": part_id,
        "asm_id": asm_id,
        "comp_id": comp_id,
        "bom_id": bom_id,
        "stock_id": stock_id,
    }


# ---------------------------------------------------------------------------
# Write endpoints — unauthenticated → 401/403
# ---------------------------------------------------------------------------

@pytest.mark.auth
@pytest.mark.negative
def test_write_endpoints_require_auth(anon_client, auth_client):
    """All write operations on all resources must fail without authentication."""
    ids = _get_or_create_resources(auth_client)

    write_requests = [
        # PartCategory
        ("post",   "/api/part/category/",                          {"name": "X", "description": "x"}),
        ("put",    f"/api/part/category/{ids['cat_id']}/",         {"name": "X", "description": "x"}),
        ("patch",  f"/api/part/category/{ids['cat_id']}/",         {"name": "X"}),
        ("delete", f"/api/part/category/{ids['cat_id']}/",         None),
        # Part
        ("post",   "/api/part/",                                   {"name": "X", "description": "x"}),
        ("put",    f"/api/part/{ids['part_id']}/",                 {"name": "X", "description": "x", "active": True, "virtual": False, "template": False, "assembly": False, "component": True}),
        ("patch",  f"/api/part/{ids['part_id']}/",                 {"name": "X"}),
        ("delete", f"/api/part/{ids['part_id']}/",                 None),
        # Revisions
        ("post",   f"/api/part/{ids['part_id']}/create_revision/", {"revision": "B"}),
        ("delete", f"/api/part/{ids['part_id']}/revisions/clear/", None),
        # BOM
        ("post",   "/api/part/bom/",                               {"assembly": ids["asm_id"], "sub_part": ids["comp_id"], "quantity": 2}),
        ("put",    f"/api/part/bom/{ids['bom_id']}/",              {"assembly": ids["asm_id"], "sub_part": ids["comp_id"], "quantity": 2}),
        ("patch",  f"/api/part/bom/{ids['bom_id']}/",              {"quantity": 2}),
        ("delete", f"/api/part/bom/{ids['bom_id']}/",              None),
        # Stock
        ("post",   "/api/part/stock/",                             {"part": ids["part_id"], "quantity": 1}),
        ("put",    f"/api/part/stock/{ids['stock_id']}/",          {"part": ids["part_id"], "quantity": 2}),
        ("patch",  f"/api/part/stock/{ids['stock_id']}/",          {"quantity": 2}),
        ("delete", f"/api/part/stock/{ids['stock_id']}/",          None),
    ]

    failures = []
    for method, path, body in write_requests:
        fn = getattr(anon_client, method)
        r = fn(path, json=body) if body is not None else fn(path)
        if r.status_code not in (401, 403):
            failures.append(f"{method.upper()} {path} → {r.status_code} (expected 401/403)")

    assert not failures, "Some write endpoints allowed unauthenticated access:\n" + "\n".join(failures)

    # Cleanup
    for url in [
        f"/api/part/stock/{ids['stock_id']}/",
        f"/api/part/bom/{ids['bom_id']}/",
        f"/api/part/{ids['asm_id']}/",
        f"/api/part/{ids['comp_id']}/",
        f"/api/part/{ids['part_id']}/",
        f"/api/part/category/{ids['cat_id']}/",
    ]:
        auth_client.delete(url)


# ---------------------------------------------------------------------------
# Read endpoints — anonymous access → 200
# ---------------------------------------------------------------------------

@pytest.mark.auth
@pytest.mark.positive
def test_read_endpoints_allow_anonymous(anon_client, auth_client):
    """All GET (list/detail) endpoints are accessible without authentication."""
    ids = _get_or_create_resources(auth_client)

    read_requests = [
        "/api/part/category/",
        f"/api/part/category/{ids['cat_id']}/",
        "/api/part/category/root/",
        "/api/part/category/tree/",
        "/api/part/",
        f"/api/part/{ids['part_id']}/",
        f"/api/part/{ids['part_id']}/revisions/",
        "/api/part/bom/",
        f"/api/part/bom/{ids['bom_id']}/",
        "/api/part/stock/",
        f"/api/part/stock/{ids['stock_id']}/",
    ]

    failures = []
    for path in read_requests:
        r = anon_client.get(path)
        if r.status_code != 200:
            failures.append(f"GET {path} → {r.status_code} (expected 200)")

    # Cleanup
    for url in [
        f"/api/part/stock/{ids['stock_id']}/",
        f"/api/part/bom/{ids['bom_id']}/",
        f"/api/part/{ids['asm_id']}/",
        f"/api/part/{ids['comp_id']}/",
        f"/api/part/{ids['part_id']}/",
        f"/api/part/category/{ids['cat_id']}/",
    ]:
        auth_client.delete(url)

    assert not failures, "Some read endpoints rejected anonymous access:\n" + "\n".join(failures)


# ---------------------------------------------------------------------------
# Authenticated reads also work
# ---------------------------------------------------------------------------

@pytest.mark.auth
@pytest.mark.positive
def test_authenticated_reads_work(auth_client):
    r = auth_client.get("/api/part/")
    assert_status(r, 200)

    r2 = auth_client.get("/api/part/category/")
    assert_status(r2, 200)
