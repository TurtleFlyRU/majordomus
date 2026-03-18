from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .enums import MissingGovernancePolicy, OrderingPolicy, ProjectStatus, RunMode, Severity


@dataclass(frozen=True)
class Location:
    path: str
    line: int = 1
    col: int | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"path": self.path, "line": self.line}
        if self.col is not None:
            data["col"] = self.col
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Location:
        return cls(
            path=data["path"],
            line=data.get("line", 1),
            col=data.get("col"),
        )


@dataclass(frozen=True)
class Issue:
    code: str
    severity: Severity
    message: str
    location: Location
    project: str | None = None
    task_id: str | None = None
    data: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "location": self.location.to_dict(),
        }
        if self.project is not None:
            payload["project"] = self.project
        if self.task_id is not None:
            payload["task_id"] = self.task_id
        if self.data is not None:
            payload["data"] = self.data
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Issue:
        return cls(
            code=data["code"],
            severity=Severity(data["severity"]),
            message=data["message"],
            location=Location.from_dict(data["location"]),
            project=data.get("project"),
            task_id=data.get("task_id"),
            data=data.get("data"),
        )


@dataclass(frozen=True)
class ProjectStats:
    tasks: int = 0
    errors: int = 0
    warns: int = 0
    time_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "tasks": self.tasks,
            "errors": self.errors,
            "warns": self.warns,
            "time_ms": self.time_ms,
        }


@dataclass(frozen=True)
class ProjectReport:
    project: str
    status: ProjectStatus
    issues: list[Issue] = field(default_factory=list)
    stats: ProjectStats = field(default_factory=ProjectStats)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "status": self.status.value,
            "issues": [item.to_dict() for item in self.issues],
            "stats": self.stats.to_dict(),
        }


@dataclass(frozen=True)
class WorkspaceSummary:
    total_projects: int = 0
    passed_projects: int = 0
    failed_projects: int = 0
    skipped_projects: int = 0
    errors: int = 0
    warns: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_projects": self.total_projects,
            "passed_projects": self.passed_projects,
            "failed_projects": self.failed_projects,
            "skipped_projects": self.skipped_projects,
            "errors": self.errors,
            "warns": self.warns,
        }


@dataclass(frozen=True)
class ProjectRef:
    name: str
    path: str
    governance_dir: str | None = None
    missing_governance: MissingGovernancePolicy | None = None


@dataclass(frozen=True)
class WorkspaceConfig:
    workspace_name: str
    ordering: OrderingPolicy
    default_governance_dir: str
    default_missing_governance: MissingGovernancePolicy
    projects: list[ProjectRef]


@dataclass(frozen=True)
class ProjectContext:
    project: str
    project_root: Path
    governance_dir: str
    missing_governance: MissingGovernancePolicy
    mode: RunMode


@dataclass(frozen=True)
class WorkspaceReport:
    workspace: str
    mode: RunMode
    ordering: OrderingPolicy
    project_reports: list[ProjectReport]
    issues: list[Issue]
    summary: WorkspaceSummary
    exit_code: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace": self.workspace,
            "mode": self.mode.value,
            "ordering": self.ordering.value,
            "project_reports": [item.to_dict() for item in self.project_reports],
            "issues": [item.to_dict() for item in self.issues],
            "summary": self.summary.to_dict(),
            "exit_code": self.exit_code,
        }
