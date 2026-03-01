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

    def requires_implementation(self, state: str) -> bool:
        anchor = self._furthest_target_for_role("DEV")
        return self._is_at_or_after_anchor(state, anchor)

    def requires_verification(self, state: str) -> bool:
        anchor = self._furthest_target_for_role("AUDITOR")
        return self._is_at_or_after_anchor(state, anchor)

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

    def _furthest_target_for_role(self, role: str) -> str | None:
        state_order = {name: index for index, name in enumerate(self.states)}
        candidates = [
            transition.target
            for transition in self.transitions
            if role in transition.allowed_roles and transition.target in state_order
        ]
        if not candidates:
            return None
        return max(candidates, key=state_order.__getitem__)

    def _is_at_or_after_anchor(self, state: str, anchor: str | None) -> bool:
        if anchor is None:
            return False
        state_order = {name: index for index, name in enumerate(self.states)}
        state_index = state_order.get(state)
        anchor_index = state_order.get(anchor)
        if state_index is None or anchor_index is None:
            return False
        return state_index >= anchor_index
