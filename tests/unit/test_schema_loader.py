from majordomus.core.schema_loader import SchemaLoader


def test_schema_loader_loads_builtin_schema() -> None:
    schema = SchemaLoader().load("workspace_schema_v1.json")

    assert schema["type"] == "object"
    assert "workspace_name" in schema["properties"]
