def validate_function_parameters_schema_common(parameters_schema: dict, path: str) -> None:
    """
    Validate a function parameters schema based on a set of common rules.
    These rules should be true for all types of protocols. (rest, connector, etc.)
    Some of rules we make it more strict than JSON Schema standard to avoid human errors, e.g., 'required' must be specified.
    """
    # if not an object type schema, skip most of the validation but make sure required and visible does NOT exist
    if parameters_schema.get("type") != "object":
        if "required" in parameters_schema or "visible" in parameters_schema:
            raise ValueError(
                f"Invalid schema at {path}: 'required' and 'visible' fields are not allowed for non-object type schemas"
            )
        return

    # Ensure properties field exists
    if "properties" not in parameters_schema:
        raise ValueError(f"Missing 'properties' field at {path}")

    # Ensure required field exists
    if "required" not in parameters_schema:
        raise ValueError(f"Missing 'required' field at {path}")

    # Ensure visible field exists
    if "visible" not in parameters_schema:
        raise ValueError(f"Missing 'visible' field at {path}")

    # Ensure additionalProperties field exists
    if "additionalProperties" not in parameters_schema:
        raise ValueError(f"Missing 'additionalProperties' field at {path}")

    properties = parameters_schema.get("properties", {})
    required = parameters_schema.get("required", [])
    visible = parameters_schema.get("visible", [])

    # Check that all required properties actually exist
    for prop in required:
        if prop not in properties:
            raise ValueError(f"Required property '{prop}' at {path} not found in properties")

    # Check that all visible properties actually exist
    for prop in visible:
        if prop not in properties:
            raise ValueError(f"Visible property '{prop}' at {path} not found in properties")

    # Check properties in 'required' but not in 'visible' have defaults (except for objects)
    for prop_name, prop_schema in properties.items():
        if prop_name in required and prop_name not in visible:
            if prop_schema.get("type") != "object" and "default" not in prop_schema:
                raise ValueError(
                    f"Non-visible but required property '{prop_name}' at {path} must have a default value"
                )

    # Recursively validate nested properties
    for prop_name, prop_schema in properties.items():
        validate_function_parameters_schema_common(prop_schema, f"{path}.{prop_name}")

        # Check if each property should be visible based on children's visibility
        if prop_schema.get("type") == "object":
            child_visible = prop_schema.get("visible", [])
            # if all properties of this object are not visible, then this object itself should not be visible.
            # Unless additionalProperties of this object is true
            if (
                not child_visible
                and prop_name in visible
                and not prop_schema.get("additionalProperties", False)
            ):
                raise ValueError(
                    f"Property '{prop_name}' at {path} cannot be visible when all its children are non-visible"
                )


def validate_function_parameters_schema_rest_protocol(
    parameters_schema: dict, path: str, allowed_top_level_keys: list[str]
) -> None:
    """
    Validate a function parameters schema for the REST protocol, for rules that are not covered by the common rules.
    """
    # Skip if empty schema (happens in some cases, e.g. when function needs no input arguments)
    if not parameters_schema:
        return

    # type must be "object"
    if parameters_schema.get("type") != "object":
        raise ValueError("top level type must be 'object' for REST protocol's parameters schema")
    # properties must be a dict and can only have "path", "query", "header", "cookie", "body" keys
    properties = parameters_schema["properties"]
    if not isinstance(properties, dict):
        raise ValueError(
            "top level properties must be a dict for REST protocol's parameters schema"
        )
    for key in properties.keys():
        if key not in allowed_top_level_keys:
            raise ValueError(
                f"invalid key '{key}' for top level properties in REST protocol's parameters schema"
            )
    # required must be present and must be a list and can only have keys in "properties"
    required = parameters_schema["required"]
    if not isinstance(required, list):
        raise ValueError("'required' must be a list for REST protocol's properties")
    for key in required:
        if key not in properties:
            raise ValueError(
                f"key '{key}' in 'required' must be in 'properties' for REST protocol's properties"
            )
    # additionalProperties must be false
    if parameters_schema["additionalProperties"]:
        raise ValueError(
            "'additionalProperties' must be false for REST protocol's top level properties"
        )
