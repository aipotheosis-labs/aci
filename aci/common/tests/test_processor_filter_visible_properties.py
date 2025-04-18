from copy import deepcopy

from aci.common.processor import filter_visible_properties


def test_basic_filtering() -> None:
    schema = {
        "type": "object",
        "properties": {
            "a": {"type": "string"},
            "b": {"type": "integer"},
        },
        "visible": ["a"],
    }
    expected = {
        "type": "object",
        "properties": {
            "a": {"type": "string"},
        },
    }
    result = filter_visible_properties(schema)
    assert result == expected


def test_no_visible_field() -> None:
    schema = {
        "type": "object",
        "properties": {
            "a": {"type": "string"},
            "b": {"type": "integer"},
        },
    }
    expected = {"type": "object", "properties": {}}
    result = filter_visible_properties(schema)
    assert result == expected


def test_empty_visible_field() -> None:
    schema = {
        "type": "object",
        "properties": {
            "a": {"type": "string"},
            "b": {"type": "integer"},
        },
        "visible": [],
    }
    expected = {"type": "object", "properties": {}}
    result = filter_visible_properties(schema)
    assert result == expected


def test_nested_properties() -> None:
    schema = {
        "type": "object",
        "properties": {
            "a": {
                "type": "object",
                "properties": {
                    "b": {"type": "string"},
                    "c": {"type": "integer"},
                },
                "visible": ["b"],
            },
            "d": {"type": "boolean"},
        },
        "visible": ["a"],
    }
    expected = {
        "type": "object",
        "properties": {
            "a": {
                "type": "object",
                "properties": {
                    "b": {"type": "string"},
                },
            }
        },
    }
    result = filter_visible_properties(schema)
    assert result == expected


def test_no_modification_of_original() -> None:
    schema = {
        "type": "object",
        "properties": {
            "a": {"type": "string"},
            "b": {"type": "integer"},
        },
        "visible": ["a"],
    }
    original_schema = deepcopy(schema)
    filter_visible_properties(schema)
    assert schema == original_schema
