from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from majordomus.core.domain import Issue, Location, Severity
from majordomus.core.governance.policy_engine import RolePolicy
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
        profile = self._resolve_profile(
            project=project, governance_root=governance_root, issues=issues
        )

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

        policy = self._load_policy(
            project=project,
            governance_root=governance_root,
            profile=profile,
            issues=issues,
        )

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
                payload=task_payload,
                task_file=task_file,
                project=project,
                role_ids=role_ids,
                state_machine=state_machine,
                governance_root=governance_root,
                policy=policy,
                profile=profile,
                issues=issues,
            )

        return sort_issues(issues), len(task_files)

    def _resolve_profile(
        self,
        *,
        project: str,
        governance_root: Path,
        issues: list[Issue],
    ) -> str:
        project_yaml_path = governance_root / "project.yaml"
        if not project_yaml_path.exists():
            return "basic"

        payload, parse_issues = parse_yaml_file(
            project_yaml_path,
            code="PRJ101",
            message="Cannot parse project.yaml",
            project=project,
        )
        issues.extend(parse_issues)
        if payload is None:
            return "basic"

        raw_profile = payload.get("profile", "basic")
        profile = str(raw_profile).strip().lower()
        if profile not in {"basic", "trinity"}:
            issues.append(
                Issue(
                    code="PRJ101",
                    severity=Severity.ERROR,
                    message=f"Unknown project profile '{raw_profile}'",
                    location=Location(path=str(project_yaml_path)),
                    project=project,
                )
            )
            return "basic"

        return profile

    def _load_policy(
        self,
        *,
        project: str,
        governance_root: Path,
        profile: str,
        issues: list[Issue],
    ) -> RolePolicy | None:
        policy_path = governance_root / "policies" / "role_policy.json"
        if not policy_path.exists():
            if profile == "trinity":
                issues.append(
                    Issue(
                        code="POL100",
                        severity=Severity.ERROR,
                        message="Trinity profile requires .majordomus/policies/role_policy.json",
                        location=Location(path=str(policy_path)),
                        project=project,
                    )
                )
            return None

        payload, parse_issues = parse_json_file(
            policy_path,
            code="POL100",
            message="Cannot parse role policy JSON",
            project=project,
        )
        issues.extend(parse_issues)
        if payload is None:
            return None

        schema_issues = self._schema_validator.validate(
            "role_policy_schema_v1.json",
            payload,
            code="POL100",
            project=project,
            location_path=str(policy_path),
        )
        issues.extend(schema_issues)
        if schema_issues:
            return None

        return RolePolicy.from_payload(payload)

    def _validate_task_semantics(
        self,
        *,
        payload: dict[str, Any],
        task_file: Path,
        project: str,
        role_ids: set[str],
        state_machine: StateMachine | None,
        governance_root: Path,
        policy: RolePolicy | None,
        profile: str,
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

        states = set(state_machine.states) if state_machine else set()
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

        transition_allowed_roles: dict[tuple[str, str], set[str]] = {}
        if state_machine is not None:
            for sm_transition in state_machine.transitions:
                transition_allowed_roles[(sm_transition.source, sm_transition.target)] = set(
                    sm_transition.allowed_roles
                )

        relative_task_path = _to_project_relative_path(task_file, governance_root.parent)

        for task_transition in payload.get("transitions", []):
            if not isinstance(task_transition, dict):
                continue
            source = str(task_transition["from"])
            target = str(task_transition["to"])
            role = str(task_transition["role"])
            pair = (source, target)

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
                continue

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
                continue

            allowed_roles = transition_allowed_roles.get(pair)
            if allowed_roles is None:
                issues.append(
                    Issue(
                        code="TASK200",
                        severity=Severity.ERROR,
                        message=(
                            f"Transition ({source} -> {target}) is not declared in state machine"
                        ),
                        location=Location(path=str(task_file)),
                        project=project,
                        task_id=task_id,
                    )
                )
                continue

            if role not in allowed_roles:
                issues.append(
                    Issue(
                        code="POL200",
                        severity=Severity.ERROR,
                        message=(
                            f"Role '{role}' is not allowed by state machine for transition "
                            f"({source} -> {target})"
                        ),
                        location=Location(path=str(task_file)),
                        project=project,
                        task_id=task_id,
                    )
                )

            if policy is not None and not policy.can(
                role=role,
                relative_path=relative_task_path,
                action="TRANSITION",
            ):
                issues.append(
                    Issue(
                        code="POL200",
                        severity=Severity.ERROR,
                        message=(
                            f"Role '{role}' is not permitted to perform TRANSITION on "
                            f"'{relative_task_path}'"
                        ),
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

        if profile == "trinity":
            self._validate_trinity_task_payload(
                payload, task_file, project, task_id, status, issues
            )

    def _validate_trinity_task_payload(
        self,
        payload: dict[str, Any],
        task_file: Path,
        project: str,
        task_id: str,
        status: str,
        issues: list[Issue],
    ) -> None:
        assignment = payload.get("assignment")
        if not _is_non_empty_mapping(assignment):
            issues.append(
                Issue(
                    code="TASK300",
                    severity=Severity.ERROR,
                    message="Trinity task requires non-empty 'assignment' object",
                    location=Location(path=str(task_file)),
                    project=project,
                    task_id=task_id,
                )
            )

        needs_implementation = status in {"dev_done", "qa_done", "arch_review", "done"}
        if needs_implementation and not _is_non_empty_mapping(payload.get("implementation")):
            issues.append(
                Issue(
                    code="TASK300",
                    severity=Severity.ERROR,
                    message=(
                        "Trinity task status requires non-empty 'implementation' object "
                        f"(status={status})"
                    ),
                    location=Location(path=str(task_file)),
                    project=project,
                    task_id=task_id,
                )
            )

        needs_verification = status in {"qa_done", "arch_review", "done"}
        if needs_verification and not _is_non_empty_mapping(payload.get("verification")):
            issues.append(
                Issue(
                    code="TASK300",
                    severity=Severity.ERROR,
                    message=(
                        "Trinity task status requires non-empty 'verification' object "
                        f"(status={status})"
                    ),
                    location=Location(path=str(task_file)),
                    project=project,
                    task_id=task_id,
                )
            )

        if needs_verification and not _is_non_empty_list(payload.get("evidence")):
            issues.append(
                Issue(
                    code="TASK300",
                    severity=Severity.ERROR,
                    message=(
                        f"Trinity task status requires non-empty 'evidence' list (status={status})"
                    ),
                    location=Location(path=str(task_file)),
                    project=project,
                    task_id=task_id,
                )
            )

        if needs_verification and not _is_non_empty_list(payload.get("acceptance_checks")):
            issues.append(
                Issue(
                    code="TASK300",
                    severity=Severity.ERROR,
                    message=(
                        "Trinity task status requires non-empty 'acceptance_checks' list "
                        f"(status={status})"
                    ),
                    location=Location(path=str(task_file)),
                    project=project,
                    task_id=task_id,
                )
            )


def _to_project_relative_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _parse_datetime(value: str) -> datetime | None:
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _is_non_empty_mapping(value: Any) -> bool:
    return isinstance(value, dict) and len(value) > 0


def _is_non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0
