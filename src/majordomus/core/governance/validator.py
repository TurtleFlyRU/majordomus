from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from majordomus.core.domain import Issue, Location, Severity
from majordomus.core.governance.role_engine import RoleEngine
from majordomus.core.governance.state_machine import StateMachine
from majordomus.core.governance.task_registry import TaskRegistry
from majordomus.core.ports.schema_validator import JsonSchemaValidatorPort
from majordomus.core.util.parsing import parse_json_file, parse_yaml_file
from majordomus.core.util.sorting import sort_issues


class ProjectGovernanceValidator:
    def __init__(
        self,
        schema_validator: JsonSchemaValidatorPort,
        role_engine: RoleEngine,
        task_registry: TaskRegistry,
    ) -> None:
        self._schema_validator = schema_validator
        self._role_engine = role_engine
        self._task_registry = task_registry

    def validate(self, *, project: str, governance_root: Path) -> tuple[list[Issue], int]:
        issues: list[Issue] = []

        roles_path = governance_root / "roles.yaml"
        state_machine_path = governance_root / "state_machine.yaml"

        roles_payload, roles_parse_issues = parse_yaml_file(
            roles_path,
            code="PRJ101",
            message="Cannot parse roles.yaml",
            project=project,
        )
        issues.extend(roles_parse_issues)

        role_ids: set[str] = set()
        if roles_payload is not None:
            schema_issues = self._schema_validator.validate(
                "roles_schema_v1.json",
                roles_payload,
                code="PRJ101",
                project=project,
                location_path=str(roles_path),
            )
            issues.extend(schema_issues)
            if not schema_issues:
                role_ids, role_issues = self._role_engine.validate(
                    roles_payload,
                    project=project,
                    location_path=str(roles_path),
                )
                issues.extend(role_issues)

        sm_payload, sm_parse_issues = parse_yaml_file(
            state_machine_path,
            code="PRJ101",
            message="Cannot parse state_machine.yaml",
            project=project,
        )
        issues.extend(sm_parse_issues)

        state_machine: StateMachine | None = None
        if sm_payload is not None:
            schema_issues = self._schema_validator.validate(
                "state_machine_schema_v1.json",
                sm_payload,
                code="PRJ101",
                project=project,
                location_path=str(state_machine_path),
            )
            issues.extend(schema_issues)
            if not schema_issues:
                state_machine, sm_issues = StateMachine.from_payload(
                    sm_payload,
                    project=project,
                    location_path=str(state_machine_path),
                    known_roles=role_ids,
                )
                issues.extend(sm_issues)

        task_files = self._task_registry.list_task_files(governance_root)
        for task_file in task_files:
            task_payload, task_parse_issues = parse_json_file(
                task_file,
                code="TASK100",
                message="Cannot parse task JSON",
                project=project,
            )
            issues.extend(task_parse_issues)
            if task_payload is None:
                continue

            task_id = str(task_payload.get("id", ""))
            schema_issues = self._schema_validator.validate(
                "task_schema_v1.json",
                task_payload,
                code="TASK101",
                project=project,
                location_path=str(task_file),
                task_id=task_id or None,
            )
            issues.extend(schema_issues)
            if schema_issues:
                continue

            self._validate_task_semantics(
                task_payload,
                task_file,
                project,
                role_ids,
                set(state_machine.states) if state_machine else set(),
                issues,
            )

        return sort_issues(issues), len(task_files)

    def _validate_task_semantics(
        self,
        payload: dict[str, Any],
        task_file: Path,
        project: str,
        role_ids: set[str],
        states: set[str],
        issues: list[Issue],
    ) -> None:
        task_id = str(payload["id"])

        if task_file.stem != task_id:
            issues.append(
                Issue(
                    code="TASK001",
                    severity=Severity.ERROR,
                    message=f"Task filename '{task_file.stem}' must match task id '{task_id}'",
                    location=Location(path=str(task_file)),
                    project=project,
                    task_id=task_id,
                )
            )

        status = str(payload["status"])
        if status not in states:
            issues.append(
                Issue(
                    code="TASK200",
                    severity=Severity.ERROR,
                    message=f"Unknown task status '{status}'",
                    location=Location(path=str(task_file)),
                    project=project,
                    task_id=task_id,
                )
            )

        owner_role = payload.get("owner_role")
        if owner_role is not None and str(owner_role) not in role_ids:
            issues.append(
                Issue(
                    code="PRJ203",
                    severity=Severity.ERROR,
                    message=f"Unknown owner role '{owner_role}'",
                    location=Location(path=str(task_file)),
                    project=project,
                    task_id=task_id,
                )
            )

        for transition in payload.get("transitions", []):
            source = str(transition["from"])
            target = str(transition["to"])
            role = str(transition["role"])

            if source not in states or target not in states:
                issues.append(
                    Issue(
                        code="TASK200",
                        severity=Severity.ERROR,
                        message=f"Transition has unknown state ({source} -> {target})",
                        location=Location(path=str(task_file)),
                        project=project,
                        task_id=task_id,
                    )
                )

            if role not in role_ids:
                issues.append(
                    Issue(
                        code="PRJ203",
                        severity=Severity.ERROR,
                        message=f"Unknown transition role '{role}'",
                        location=Location(path=str(task_file)),
                        project=project,
                        task_id=task_id,
                    )
                )

        created_at = payload.get("created_at")
        updated_at = payload.get("updated_at")
        if created_at and updated_at:
            created_ts = _parse_datetime(str(created_at))
            updated_ts = _parse_datetime(str(updated_at))
            if created_ts is None or updated_ts is None:
                issues.append(
                    Issue(
                        code="TASK101",
                        severity=Severity.ERROR,
                        message="Invalid datetime format in created_at/updated_at",
                        location=Location(path=str(task_file)),
                        project=project,
                        task_id=task_id,
                    )
                )
            elif updated_ts < created_ts:
                issues.append(
                    Issue(
                        code="TASK101",
                        severity=Severity.ERROR,
                        message="updated_at must be greater or equal to created_at",
                        location=Location(path=str(task_file)),
                        project=project,
                        task_id=task_id,
                    )
                )


def _parse_datetime(value: str) -> datetime | None:
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None
