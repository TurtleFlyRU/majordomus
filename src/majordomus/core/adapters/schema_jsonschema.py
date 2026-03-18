from __future__ import annotations

import copy
from typing import Any

import jsonschema

from majordomus.core.domain import Issue, Location, Severity
from majordomus.core.ports.schema_validator import JsonSchemaValidatorPort
from majordomus.core.schema_loader import SchemaLoader


class JsonschemaValidatorAdapter(JsonSchemaValidatorPort):
    def __init__(self, schema_loader: SchemaLoader) -> None:
        self._schema_loader = schema_loader

    def validate(
        self,
        schema_name: str,
        payload: Any,
        *,
        code: str,
        project: str | None,
        location_path: str,
        task_id: str | None = None,
    ) -> list[Issue]:
        schema = self._schema_loader.load(schema_name)
        
        # Clean payload from internal __line__ markers before validation
        clean_payload = _strip_internal_keys(payload)
        
        validator = jsonschema.Draft202012Validator(
            schema,
            format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER,
        )
        issues: list[Issue] = []

        for error in sorted(validator.iter_errors(clean_payload), key=lambda item: str(item.path)):
            path_bits = [str(part) for part in error.path]
            path_str = ".".join(path_bits) if path_bits else "$"
            issues.append(
                Issue(
                    code=code,
                    severity=Severity.ERROR,
                    message=f"Schema validation failed at {path_str}: {error.message}",
                    location=Location(path=location_path),
                    project=project,
                    task_id=task_id,
                )
            )
        return issues


def _strip_internal_keys(data: Any) -> Any:
    if isinstance(data, dict):
        return {
            k: _strip_internal_keys(v) 
            for k, v in data.items() 
            if k != "__line__"
        }
    if isinstance(data, list):
        return [_strip_internal_keys(item) for item in data]
    return data
