from __future__ import annotations

from typing import Any

from majordomus.core.domain import Issue, Location, Severity


class RoleEngine:
    def validate(
        self, payload: dict[str, Any], *, project: str, location_path: str
    ) -> tuple[set[str], list[Issue]]:
        issues: list[Issue] = []
        role_ids: list[str] = [str(item["id"]) for item in payload.get("roles", [])]

        seen: set[str] = set()
        duplicates: set[str] = set()
        for role_id in role_ids:
            if role_id in seen:
                duplicates.add(role_id)
            seen.add(role_id)

        for duplicate in sorted(duplicates):
            issues.append(
                Issue(
                    code="PRJ203",
                    severity=Severity.ERROR,
                    message=f"Duplicate role id: {duplicate}",
                    location=Location(path=location_path),
                    project=project,
                )
            )

        return set(role_ids), issues
