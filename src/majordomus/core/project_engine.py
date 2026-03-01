from __future__ import annotations

import time

from majordomus.core.domain import (
    Issue,
    Location,
    ProjectContext,
    ProjectReport,
    ProjectStats,
    ProjectStatus,
    Severity,
)
from majordomus.core.governance.validator import ProjectGovernanceValidator
from majordomus.core.ports.filesystem import FileSystemPort
from majordomus.core.util.paths import safe_join
from majordomus.core.util.sorting import sort_issues


class ProjectEngine:
    def __init__(
        self, fs: FileSystemPort, governance_validator: ProjectGovernanceValidator
    ) -> None:
        self._fs = fs
        self._governance_validator = governance_validator

    def run(self, ctx: ProjectContext) -> ProjectReport:
        started = time.perf_counter()
        issues: list[Issue] = []

        if not self._fs.is_dir(ctx.project_root):
            issues.append(
                Issue(
                    code="PRJ001",
                    severity=Severity.ERROR,
                    message=f"Project path does not exist: {ctx.project_root}",
                    location=Location(path=str(ctx.project_root)),
                    project=ctx.project,
                )
            )
            return self._build_report(
                ctx.project, ProjectStatus.FAIL, issues, tasks=0, started=started
            )

        try:
            governance_root = safe_join(ctx.project_root, ctx.governance_dir)
        except ValueError:
            issues.append(
                Issue(
                    code="PRJ010",
                    severity=Severity.ERROR,
                    message=f"Invalid governance_dir escape attempt: {ctx.governance_dir}",
                    location=Location(path=str(ctx.project_root)),
                    project=ctx.project,
                )
            )
            return self._build_report(
                ctx.project, ProjectStatus.FAIL, issues, tasks=0, started=started
            )

        if not self._fs.is_dir(governance_root):
            severity = Severity.WARN if ctx.missing_governance.value == "skip" else Severity.ERROR
            status = (
                ProjectStatus.SKIP if ctx.missing_governance.value == "skip" else ProjectStatus.FAIL
            )
            issues.append(
                Issue(
                    code="PRJ010",
                    severity=severity,
                    message=f"Governance directory is missing: {governance_root}",
                    location=Location(path=str(governance_root)),
                    project=ctx.project,
                )
            )
            return self._build_report(ctx.project, status, issues, tasks=0, started=started)

        validation_issues, tasks_count = self._governance_validator.validate(
            project=ctx.project,
            governance_root=governance_root,
        )
        issues.extend(validation_issues)

        has_errors = any(item.severity == Severity.ERROR for item in issues)
        status = ProjectStatus.FAIL if has_errors else ProjectStatus.PASS
        return self._build_report(ctx.project, status, issues, tasks=tasks_count, started=started)

    def _build_report(
        self,
        project: str,
        status: ProjectStatus,
        issues: list[Issue],
        *,
        tasks: int,
        started: float,
    ) -> ProjectReport:
        sorted_issues = sort_issues(issues)
        errors = sum(1 for issue in sorted_issues if issue.severity == Severity.ERROR)
        warns = sum(1 for issue in sorted_issues if issue.severity == Severity.WARN)
        _ = started
        time_ms = 0

        return ProjectReport(
            project=project,
            status=status,
            issues=sorted_issues,
            stats=ProjectStats(tasks=tasks, errors=errors, warns=warns, time_ms=time_ms),
        )
