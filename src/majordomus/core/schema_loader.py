from __future__ import annotations

import json
from importlib import resources
from typing import Any, cast


class SchemaLoader:
    def load(self, schema_name: str) -> dict[str, Any]:
        package = "majordomus.schemas"
        with resources.files(package).joinpath(schema_name).open("r", encoding="utf-8") as stream:
            payload = json.load(stream)
        return cast(dict[str, Any], payload)
