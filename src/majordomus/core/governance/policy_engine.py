from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from typing import Any


@dataclass(frozen=True)
class RolePolicyRule:
    role: str
    pattern: str
    actions: tuple[str, ...]


@dataclass(frozen=True)
class RolePolicy:
    default_actions: tuple[str, ...]
    rules: tuple[RolePolicyRule, ...]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> RolePolicy:
        rules = tuple(
            RolePolicyRule(
                role=str(item["role"]),
                pattern=str(item["pattern"]),
                actions=tuple(str(action) for action in item.get("actions", [])),
            )
            for item in payload.get("rules", [])
        )
        default_actions = tuple(str(action) for action in payload.get("default_actions", []))
        return cls(default_actions=default_actions, rules=rules)

    def allowed_actions(self, role: str, relative_path: str) -> tuple[str, ...]:
        matched_actions: list[str] = []
        for rule in self.rules:
            if rule.role != role:
                continue
            if fnmatch(relative_path, rule.pattern):
                matched_actions.extend(rule.actions)

        if not matched_actions:
            return self.default_actions

        unique_actions = sorted(set(matched_actions))
        return tuple(unique_actions)

    def can(self, role: str, relative_path: str, action: str) -> bool:
        return action in self.allowed_actions(role=role, relative_path=relative_path)
