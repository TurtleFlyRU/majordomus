from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from majordomus.core.domain import Issue, Location, Severity


@dataclass(frozen=True)
class Transition:
    source: str
    target: str
    allowed_roles: tuple[str, ...]


@dataclass(frozen=True)
class StateMachine:
    states: tuple[str, ...]
    initial_state: str
    transitions: tuple[Transition, ...]

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, Any],
        *,
        project: str,
        location_path: str,
        known_roles: set[str],
    ) -> tuple[StateMachine | None, list[Issue]]:
        issues: list[Issue] = []
        states = tuple(str(item) for item in payload.get("states", []))
        initial_state = str(payload.get("initial_state", ""))

        if initial_state not in states:
            issues.append(
                Issue(
                    code="PRJ202",
                    severity=Severity.ERROR,
                    message=f"initial_state '{initial_state}' is not in states",
                    location=Location(path=location_path),
                    project=project,
                )
            )

        transitions_payload = payload.get("transitions", [])
        transitions: list[Transition] = []
        seen_pairs: set[tuple[str, str]] = set()

        for item in transitions_payload:
            source = str(item["from"])
            target = str(item["to"])
            pair = (source, target)
            if pair in seen_pairs:
                issues.append(
                    Issue(
                        code="PRJ202",
                        severity=Severity.ERROR,
                        message=f"Duplicate transition pair ({source} -> {target})",
                        location=Location(path=location_path),
                        project=project,
                    )
                )
            seen_pairs.add(pair)

            if source not in states or target not in states:
                issues.append(
                    Issue(
                        code="PRJ202",
                        severity=Severity.ERROR,
                        message=f"Transition ({source} -> {target}) references unknown state",
                        location=Location(path=location_path),
                        project=project,
                    )
                )

            allowed_roles = tuple(str(role) for role in item.get("allowed_roles", []))
            for role in allowed_roles:
                if role not in known_roles:
                    issues.append(
                        Issue(
                            code="PRJ203",
                            severity=Severity.ERROR,
                            message=f"Unknown role in transition: {role}",
                            location=Location(path=location_path),
                            project=project,
                        )
                    )

            transitions.append(
                Transition(source=source, target=target, allowed_roles=allowed_roles)
            )

        if issues:
            return None, issues

        return cls(states=states, initial_state=initial_state, transitions=tuple(transitions)), []
