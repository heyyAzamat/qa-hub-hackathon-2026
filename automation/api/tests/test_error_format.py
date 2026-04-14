"""
Tests that all error responses conform to the custom exception handler format:
    {"error_code": "...", "message": "...", "details": {...}}

Covers: ERR-001 – ERR-008 from api-manual-tests.md
"""
import pytest

from .helpers.assertions import assert_status, assert_error_format, assert_field_error


# ---------------------------------------------------------------------------
# ERR-001  Validation error format (400)
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_validation_error_format(auth_client):
    """POST without required field returns structured 400 error."""
    r = auth_client.post("/api/part/", json={"description": "no name field"})
    assert_status(r, 400)
    err = assert_error_format(r, "BAD_REQUEST")
    assert "details" in err, "Validation error must include 'details'"
    assert isinstance(err["details"], dict), "'details' must be a dict"


# ---------------------------------------------------------------------------
# ERR-002  Not found error format (404)
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_not_found_error_format(anon_client):
    r = anon_client.get("/api/part/999999999/")
    assert_status(r, 404)
    assert_error_format(r, "NOT_FOUND")


@pytest.mark.positive
def test_not_found_category_error_format(anon_client):
    r = anon_client.get("/api/part/category/999999999/")
    assert_status(r, 404)
    assert_error_format(r, "NOT_FOUND")


@pytest.mark.positive
def test_not_found_stock_error_format(anon_client):
    r = anon_client.get("/api/part/stock/999999999/")
    assert_status(r, 404)
    assert_error_format(r, "NOT_FOUND")


# ---------------------------------------------------------------------------
# ERR-003  Unauthenticated write (403)
# ---------------------------------------------------------------------------

@pytest.mark.positive
@pytest.mark.auth
def test_unauthenticated_write_error_format(anon_client):
    r = anon_client.post("/api/part/", json={"name": "X", "description": "x"})
    assert r.status_code in (401, 403)
    err = assert_error_format(r)
    assert err["error_code"] in ("UNAUTHORIZED", "FORBIDDEN")


# ---------------------------------------------------------------------------
# ERR-004  Method not allowed (405)
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_method_not_allowed_format(auth_client):
    """DELETE on a list-only action endpoint returns 405."""
    r = auth_client.delete("/api/part/category/root/")
    assert r.status_code == 405
    assert_error_format(r, "METHOD_NOT_ALLOWED")


# ---------------------------------------------------------------------------
# ERR-005  IntegrityError (duplicate BOM pair)
# ---------------------------------------------------------------------------

@pytest.mark.positive
@pytest.mark.business
def test_integrity_error_format(auth_client, assembly_part, component_part, bom_item_factory):
    """Duplicate (assembly, sub_part) triggers INTEGRITY_ERROR from middleware."""
    bom_item_factory(assembly_part["id"], component_part["id"])

    r = auth_client.post("/api/part/bom/", json={
        "assembly": assembly_part["id"],
        "sub_part": component_part["id"],
        "quantity": 3,
    })
    assert_status(r, 400)
    body = r.json()
    # Could be INTEGRITY_ERROR (from middleware) or BAD_REQUEST (if caught earlier)
    assert body.get("error_code") in ("INTEGRITY_ERROR", "BAD_REQUEST")
    assert "message" in body
    assert isinstance(body["message"], str) and body["message"]


# ---------------------------------------------------------------------------
# ERR-006  All errors have Content-Type: application/json
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_error_responses_have_json_content_type(anon_client, auth_client):
    """Error responses must include application/json content type."""
    test_cases = [
        anon_client.get("/api/part/999999999/"),                          # 404
        anon_client.post("/api/part/", json={"name": "X", "description": "x"}),  # 403
        auth_client.post("/api/part/", json={"description": "no name"}),  # 400
    ]
    for r in test_cases:
        content_type = r.headers.get("Content-Type", "")
        assert "application/json" in content_type, (
            f"Error response for {r.url} has Content-Type: {content_type}"
        )


# ---------------------------------------------------------------------------
# ERR-007  details dict has field keys on validation errors
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_validation_details_contains_field_keys(auth_client):
    """Field-level validation errors appear as keys in 'details'."""
    r = auth_client.post("/api/part/", json={"name": "   ", "description": "ok"})
    assert_status(r, 400)
    assert_field_error(r, "name")


# ---------------------------------------------------------------------------
# ERR-008  message is a non-empty string
# ---------------------------------------------------------------------------

@pytest.mark.positive
@pytest.mark.parametrize("url,method", [
    ("/api/part/999999/", "get"),
    ("/api/part/category/999999/", "get"),
    ("/api/part/stock/999999/", "get"),
])
def test_error_message_is_non_empty_string(anon_client, url, method):
    r = getattr(anon_client, method)(url)
    assert r.status_code in (400, 401, 403, 404, 405)
    body = r.json()
    assert "message" in body
    assert isinstance(body["message"], str)
    assert len(body["message"].strip()) > 0


# ---------------------------------------------------------------------------
# Field error keys match actual field names
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_description_field_error_key(auth_client):
    r = auth_client.post("/api/part/", json={"name": "Part"})
    assert_status(r, 400)
    assert_field_error(r, "description")


@pytest.mark.positive
def test_bom_assembly_field_error_key(auth_client, part_factory):
    not_assembly = part_factory(assembly=False)
    comp = part_factory(component=True)
    r = auth_client.post("/api/part/bom/", json={
        "assembly": not_assembly["id"],
        "sub_part": comp["id"],
        "quantity": 1,
    })
    assert_status(r, 400)
    assert_field_error(r, "assembly")


@pytest.mark.positive
def test_stock_part_field_error_template(auth_client, template_part):
    r = auth_client.post("/api/part/stock/", json={"part": template_part["id"], "quantity": 1})
    assert_status(r, 400)
    assert_field_error(r, "part")
