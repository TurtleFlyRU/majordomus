from __future__ import annotations

from typing import Any, Protocol

from majordomus.core.domain import Issue


class JsonSchemaValidatorPort(Protocol):
    def validate(
        self,
        schema_name: str,
        payload: Any,
        *,
        code: str,
        project: str | None,
        location_path: str,
        task_id: str | None = None,
    ) -> list[Issue]: ...
