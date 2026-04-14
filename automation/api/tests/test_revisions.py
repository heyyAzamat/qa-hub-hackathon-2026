"""
Tests for Part Revisions (create_revision, list_revisions, clear_revisions).

Covers: REV-001 – REV-016 from api-manual-tests.md
"""
import pytest
from faker import Faker

from .helpers.assertions import (
    assert_status,
    assert_paginated,
    assert_error_format,
)

fake = Faker()


# ---------------------------------------------------------------------------
# REV-001  No revisions
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_list_revisions_empty(anon_client, part_factory):
    part = part_factory()
    r = anon_client.get(f"/api/part/{part['id']}/revisions/")
    assert_status(r, 200)
    data = r.json()
    assert_paginated(data)
    assert data["count"] == 0
    assert data["results"] == []


# ---------------------------------------------------------------------------
# REV-002  Create first revision
# ---------------------------------------------------------------------------

@pytest.mark.smoke
@pytest.mark.positive
def test_create_revision(auth_client, part_factory):
    parent = part_factory()
    r = auth_client.post(f"/api/part/{parent['id']}/create_revision/", json={"revision": "B"})
    assert_status(r, 201)
    body = r.json()
    assert body["revision"] == "B"
    assert body["revision_of"] == parent["id"]
    assert body["name"] == parent["name"]
    assert body["description"] == parent["description"]

    # cleanup: delete the revision
    auth_client.delete(f"/api/part/{body['id']}/")


# ---------------------------------------------------------------------------
# REV-003  Name override
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_create_revision_with_name_override(auth_client, part_factory):
    parent = part_factory()
    r = auth_client.post(
        f"/api/part/{parent['id']}/create_revision/",
        json={"revision": "C", "name": "Custom Revision Name"},
    )
    assert_status(r, 201)
    body = r.json()
    assert body["revision"] == "C"
    assert body["name"] == "Custom Revision Name"
    auth_client.delete(f"/api/part/{body['id']}/")


# ---------------------------------------------------------------------------
# REV-004  List after creation
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_list_revisions_after_creation(auth_client, part_factory):
    parent = part_factory()
    r1 = auth_client.post(f"/api/part/{parent['id']}/create_revision/", json={"revision": "B"})
    assert_status(r1, 201)
    rev_id = r1.json()["id"]

    r2 = auth_client.get(f"/api/part/{parent['id']}/revisions/")
    assert_status(r2, 200)
    data = r2.json()
    assert data["count"] == 1
    assert data["results"][0]["revision"] == "B"

    auth_client.delete(f"/api/part/{rev_id}/")


# ---------------------------------------------------------------------------
# REV-005  Multiple revisions
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_create_multiple_revisions(auth_client, part_factory):
    parent = part_factory()
    rev_ids = []
    for code in ["B", "C", "D"]:
        r = auth_client.post(f"/api/part/{parent['id']}/create_revision/", json={"revision": code})
        assert_status(r, 201)
        rev_ids.append(r.json()["id"])

    r_list = auth_client.get(f"/api/part/{parent['id']}/revisions/")
    assert_status(r_list, 200)
    assert r_list.json()["count"] == 3

    for rev_id in rev_ids:
        auth_client.delete(f"/api/part/{rev_id}/")


# ---------------------------------------------------------------------------
# REV-006  Clear all revisions
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_clear_revisions(auth_client, part_factory):
    parent = part_factory()
    for code in ["B", "C", "D"]:
        r = auth_client.post(f"/api/part/{parent['id']}/create_revision/", json={"revision": code})
        assert_status(r, 201)

    r_clear = auth_client.delete(f"/api/part/{parent['id']}/revisions/clear/")
    assert_status(r_clear, 200)
    body = r_clear.json()
    assert "detail" in body
    assert "3" in body["detail"]

    r_check = auth_client.get(f"/api/part/{parent['id']}/revisions/")
    assert_status(r_check, 200)
    assert r_check.json()["count"] == 0


# ---------------------------------------------------------------------------
# REV-007  Ordering newest first
# ---------------------------------------------------------------------------

@pytest.mark.positive
def test_revisions_ordered_newest_first(auth_client, part_factory):
    parent = part_factory()
    rev_ids = []
    for code in ["B", "C"]:
        r = auth_client.post(f"/api/part/{parent['id']}/create_revision/", json={"revision": code})
        assert_status(r, 201)
        rev_ids.append(r.json()["id"])

    r_list = auth_client.get(f"/api/part/{parent['id']}/revisions/")
    results = r_list.json()["results"]
    # results[0] should be the most recently created (newest id)
    assert results[0]["id"] >= results[-1]["id"]

    for rev_id in rev_ids:
        auth_client.delete(f"/api/part/{rev_id}/")


# ---------------------------------------------------------------------------
# REV-008  Missing revision code
# ---------------------------------------------------------------------------

@pytest.mark.negative
def test_create_revision_without_code(auth_client, part_factory):
    parent = part_factory()
    r = auth_client.post(f"/api/part/{parent['id']}/create_revision/", json={})
    assert_status(r, 400)
    body = r.json()
    assert "revision" in body


# ---------------------------------------------------------------------------
# REV-009  Duplicate revision code
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.business
def test_create_duplicate_revision_code(auth_client, part_factory):
    parent = part_factory()
    r1 = auth_client.post(f"/api/part/{parent['id']}/create_revision/", json={"revision": "B"})
    assert_status(r1, 201)
    rev_id = r1.json()["id"]

    r2 = auth_client.post(f"/api/part/{parent['id']}/create_revision/", json={"revision": "B"})
    assert_status(r2, 400)

    auth_client.delete(f"/api/part/{rev_id}/")


# ---------------------------------------------------------------------------
# REV-010  Revision of a revision (edge case — documents behavior)
# ---------------------------------------------------------------------------

@pytest.mark.negative
def test_create_revision_of_revision(auth_client, part_factory):
    """
    Creating a revision of a revision is a potential bug / edge case.
    The view does not explicitly block this. We document the actual behavior.
    """
    parent = part_factory()
    r1 = auth_client.post(f"/api/part/{parent['id']}/create_revision/", json={"revision": "B"})
    assert_status(r1, 201)
    rev_id = r1.json()["id"]

    r2 = auth_client.post(
        f"/api/part/{rev_id}/create_revision/",
        json={"revision": "B2"},
    )
    # Document the actual behavior — could be 201 or 400
    assert r2.status_code in (200, 201, 400), (
        f"Unexpected status for revision-of-revision: {r2.status_code} — {r2.text}"
    )

    if r2.status_code == 201:
        auth_client.delete(f"/api/part/{r2.json()['id']}/")
    auth_client.delete(f"/api/part/{rev_id}/")


# ---------------------------------------------------------------------------
# REV-011  Revision of inactive part
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.business
def test_create_revision_of_inactive_part(auth_client, inactive_part):
    """Cannot create a revision based on an inactive part (validate_revision_of)."""
    r = auth_client.post(
        f"/api/part/{inactive_part['id']}/create_revision/",
        json={"revision": "B"},
    )
    assert_status(r, 400)
    assert_error_format(r, "BAD_REQUEST")


# ---------------------------------------------------------------------------
# REV-012  Unauthenticated create revision
# ---------------------------------------------------------------------------

@pytest.mark.negative
@pytest.mark.auth
def test_create_revision_unauthenticated(anon_client, part_factory):
    parent = part_factory()
    r = anon_client.post(f"/api/part/{parent['id']}/create_revision/", json={"revision": "B"})
    assert r.status_code in (401, 403)
    assert_error_format(r)


# ---------------------------------------------------------------------------
# REV-013  Clear revisions on non-existent part
# ---------------------------------------------------------------------------

@pytest.mark.negative
def test_clear_revisions_nonexistent_part(auth_client):
    r = auth_client.delete("/api/part/999999999/revisions/clear/")
    assert_status(r, 404)
    assert_error_format(r, "NOT_FOUND")


# ---------------------------------------------------------------------------
# REV-014 / REV-015  Revision code max_length
# ---------------------------------------------------------------------------

@pytest.mark.boundary
def test_revision_code_max_length(auth_client, part_factory):
    """Revision code of exactly 20 chars is accepted."""
    parent = part_factory()
    r = auth_client.post(
        f"/api/part/{parent['id']}/create_revision/",
        json={"revision": "A" * 20},
    )
    assert_status(r, 201)
    auth_client.delete(f"/api/part/{r.json()['id']}/")


@pytest.mark.boundary
def test_revision_code_too_long(auth_client, part_factory):
    """Revision code of 21 chars is rejected."""
    parent = part_factory()
    r = auth_client.post(
        f"/api/part/{parent['id']}/create_revision/",
        json={"revision": "A" * 21},
    )
    assert_status(r, 400)
    assert_error_format(r, "BAD_REQUEST")


# ---------------------------------------------------------------------------
# REV-016  Same revision code on different parents
# ---------------------------------------------------------------------------

@pytest.mark.boundary
@pytest.mark.business
def test_same_revision_code_different_parents(auth_client, part_factory):
    """Two different parents can each have a revision with code 'B'."""
    parent1 = part_factory()
    parent2 = part_factory()

    r1 = auth_client.post(f"/api/part/{parent1['id']}/create_revision/", json={"revision": "B"})
    assert_status(r1, 201)
    r2 = auth_client.post(f"/api/part/{parent2['id']}/create_revision/", json={"revision": "B"})
    assert_status(r2, 201)

    auth_client.delete(f"/api/part/{r1.json()['id']}/")
    auth_client.delete(f"/api/part/{r2.json()['id']}/")
