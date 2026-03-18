from __future__ import annotations

import time

from majordomus.core.domain import (
    PRJ_GOVERNANCE_MISSING,
    PRJ_PATH_ESCAPE,
    Issue,
    Location,
    MissingGovernancePolicy,
    ProjectContext,
    ProjectReport,
    ProjectStats,
    ProjectStatus,
    Severity,
)
from majordomus.core.governance.validator import ProjectGovernanceValidator
from majordomus.core.plugins.host import PluginHost
from majordomus.core.ports.filesystem import FileSystemPort
from majordomus.core.util.paths import safe_join
from majordomus.core.util.sorting import sort_issues


class ProjectEngine:
    def __init__(
        self,
        fs: FileSystemPort,
        governance_validator: ProjectGovernanceValidator,
        plugin_host: PluginHost | None = None,
    ) -> None:
        self._fs = fs
        self._governance_validator = governance_validator
        self._plugin_host = plugin_host or PluginHost([])

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
                    code=PRJ_PATH_ESCAPE,
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
            should_skip = ctx.missing_governance == MissingGovernancePolicy.SKIP
            severity = Severity.WARN if should_skip else Severity.ERROR
            status = ProjectStatus.SKIP if should_skip else ProjectStatus.FAIL
            issues.append(
                Issue(
                    code=PRJ_GOVERNANCE_MISSING,
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
            project_root=ctx.project_root,
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
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        time_ms = max(1, elapsed_ms)

        return ProjectReport(
            project=project,
            status=status,
            issues=sorted_issues,
            stats=ProjectStats(tasks=tasks, errors=errors, warns=warns, time_ms=time_ms),
        )
