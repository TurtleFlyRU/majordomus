from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InitAction:
    path: str
    status: str


@dataclass(frozen=True)
class InitReport:
    project_root: str
    project_name: str
    workspace_file: str | None
    actions: list[InitAction]

    def to_dict(self) -> dict[str, object]:
        return {
            "project_root": self.project_root,
            "project_name": self.project_name,
            "workspace_file": self.workspace_file,
            "actions": [{"path": item.path, "status": item.status} for item in self.actions],
        }


def run_init_command(
    *,
    project_root: Path,
    project_name: str | None,
    workspace_file: Path,
    include_workspace: bool,
    force: bool,
) -> InitReport:
    root = project_root.resolve()
    root.mkdir(parents=True, exist_ok=True)

    resolved_name = project_name or root.name
    actions: list[InitAction] = []

    governance_root = root / ".majordomus"
    tasks_dir = governance_root / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    roles_path = governance_root / "roles.yaml"
    state_machine_path = governance_root / "state_machine.yaml"
    project_yaml_path = governance_root / "project.yaml"
    task_path = tasks_dir / "TASK-0001.json"

    roles_content = (
        "version: 1\nroles:\n  - id: dev\n    name: Developer\n  - id: qa\n    name: QA\n"
    )
    sm_content = (
        "version: 1\n"
        "states: [todo, doing, done]\n"
        "initial_state: todo\n"
        "transitions:\n"
        "  - from: todo\n"
        "    to: doing\n"
        "    allowed_roles: [dev]\n"
        "  - from: doing\n"
        "    to: done\n"
        "    allowed_roles: [dev, qa]\n"
    )
    project_content = f"version: 1\nname: {resolved_name}\n"
    task_content = (
        json.dumps(
            {
                "schema_version": 1,
                "id": "TASK-0001",
                "title": "Bootstrap governance",
                "status": "todo",
                "owner_role": "dev",
                "transitions": [],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )

    actions.append(_write_file(roles_path, roles_content, force=force))
    actions.append(_write_file(state_machine_path, sm_content, force=force))
    actions.append(_write_file(project_yaml_path, project_content, force=force))
    actions.append(_write_file(task_path, task_content, force=force))

    resolved_workspace_file: str | None = None
    if include_workspace:
        ws_path = workspace_file if workspace_file.is_absolute() else root / workspace_file
        ws_content = (
            f"workspace_name: {resolved_name}-workspace\n"
            "defaults:\n"
            "  ordering: as_listed\n"
            "  governance_dir: .majordomus\n"
            "  missing_governance: fail\n"
            "projects:\n"
            f"  - name: {resolved_name}\n"
            "    path: .\n"
        )
        actions.append(_write_file(ws_path, ws_content, force=force))
        resolved_workspace_file = str(ws_path)

    return InitReport(
        project_root=str(root),
        project_name=resolved_name,
        workspace_file=resolved_workspace_file,
        actions=actions,
    )


def render_init_report(report: InitReport, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True, indent=2)

    lines = [
        f"project_root={report.project_root}",
        f"project_name={report.project_name}",
    ]
    if report.workspace_file:
        lines.append(f"workspace_file={report.workspace_file}")

    for action in report.actions:
        lines.append(f"{action.status}: {action.path}")

    lines.append("ready: run 'majordomus validate --path .'")
    if report.workspace_file is not None:
        lines.append(
            "ready: run 'majordomus workspace validate --workspace-file majordomus.workspace.yaml'"
        )
    return "\n".join(lines)


def _write_file(path: Path, content: str, *, force: bool) -> InitAction:
    path.parent.mkdir(parents=True, exist_ok=True)
    existed_before = path.exists()
    if existed_before and not force:
        return InitAction(path=str(path), status="skipped")

    path.write_text(content, encoding="utf-8")
    status = "overwritten" if existed_before and force else "created"
    return InitAction(path=str(path), status=status)
