"""
JSON Schema definitions for API response validation.
Used with jsonschema.validate() in tests.
"""

PART_CATEGORY_SCHEMA = {
    "type": "object",
    "required": ["id", "name", "children", "part_count"],
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "description": {"type": ["string", "null"]},
        "parent": {"type": ["integer", "null"]},
        "children": {"type": "array"},
        "part_count": {"type": "integer"},
    },
}

PART_CATEGORY_TREE_SCHEMA = {
    "type": "object",
    "required": ["id", "name", "children"],
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "parent": {"type": ["integer", "null"]},
        "children": {"type": "array"},
    },
}

PART_SCHEMA = {
    "type": "object",
    "required": ["id", "name", "active", "virtual", "template", "assembly", "component", "creation_date", "parameters"],
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "description": {"type": ["string", "null"]},
        "IPN": {"type": ["string", "null"]},
        "active": {"type": "boolean"},
        "virtual": {"type": "boolean"},
        "template": {"type": "boolean"},
        "assembly": {"type": "boolean"},
        "component": {"type": "boolean"},
        "category": {"type": ["object", "null"]},
        "revision_of": {"type": ["integer", "null"]},
        "revision": {"type": ["string", "null"]},
        "creation_date": {"type": "string"},
        "parameters": {"type": "array"},
        "stock_count": {"type": ["string", "number", "null"]},
        "bom_count": {"type": ["integer", "null"]},
    },
}

BOM_ITEM_SCHEMA = {
    "type": "object",
    "required": ["id", "assembly", "sub_part", "quantity", "optional", "assembly_name", "sub_part_name"],
    "properties": {
        "id": {"type": "integer"},
        "assembly": {"type": "integer"},
        "sub_part": {"type": "integer"},
        "quantity": {"type": ["string", "number"]},
        "optional": {"type": "boolean"},
        "note": {"type": ["string", "null"]},
        "assembly_name": {"type": "string"},
        "sub_part_name": {"type": "string"},
    },
}

STOCK_ITEM_SCHEMA = {
    "type": "object",
    "required": ["id", "part", "part_name", "quantity", "created"],
    "properties": {
        "id": {"type": "integer"},
        "part": {"type": "integer"},
        "part_name": {"type": "string"},
        "quantity": {"type": ["string", "number"]},
        "location": {"type": ["string", "null"]},
        "batch": {"type": ["string", "null"]},
        "created": {"type": "string"},
    },
}

PAGINATED_SCHEMA = {
    "type": "object",
    "required": ["count", "results"],
    "properties": {
        "count": {"type": "integer"},
        "next": {"type": ["string", "null"]},
        "previous": {"type": ["string", "null"]},
        "results": {"type": "array"},
    },
}

ERROR_SCHEMA = {
    "type": "object",
    "required": ["error_code", "message"],
    "properties": {
        "error_code": {"type": "string"},
        "message": {"type": "string"},
        "details": {},
    },
}
