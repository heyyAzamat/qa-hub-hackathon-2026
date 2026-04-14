"""
Reusable assertion helpers.
All functions accept a requests.Response and raise AssertionError with descriptive messages.
"""
from __future__ import annotations
import json
import requests
from jsonschema import validate, ValidationError


def assert_status(response: requests.Response, expected: int) -> None:
    assert response.status_code == expected, (
        f"Expected HTTP {expected}, got {response.status_code}.\n"
        f"URL: {response.url}\n"
        f"Body: {_safe_body(response)}"
    )


def assert_schema(data: dict, schema: dict) -> None:
    try:
        validate(instance=data, schema=schema)
    except ValidationError as exc:
        raise AssertionError(f"Schema validation failed: {exc.message}\nData: {data}") from exc


def assert_paginated(data: dict) -> None:
    for key in ("count", "results"):
        assert key in data, f"Missing pagination key '{key}' in response: {data}"
    assert isinstance(data["count"], int), "count must be an integer"
    assert isinstance(data["results"], list), "results must be a list"


def assert_error_format(response: requests.Response, expected_code: str | None = None) -> dict:
    data = response.json()
    assert "error_code" in data, f"Missing 'error_code' in error response: {data}"
    assert "message" in data, f"Missing 'message' in error response: {data}"
    assert isinstance(data["message"], str) and data["message"], "'message' must be a non-empty string"
    if expected_code:
        assert data["error_code"] == expected_code, (
            f"Expected error_code='{expected_code}', got '{data['error_code']}'"
        )
    return data


def assert_field_error(response: requests.Response, field_name: str) -> None:
    data = response.json()
    details = data.get("details", {})
    assert field_name in details, (
        f"Expected field error for '{field_name}' in details, got: {details}"
    )


def _safe_body(response: requests.Response) -> str:
    try:
        return json.dumps(response.json(), ensure_ascii=False, indent=2)
    except Exception:
        return response.text[:500]
