from __future__ import annotations

from pathlib import Path
from typing import Any

from majordomus.core.domain import (
    Issue,
    Location,
    MissingGovernancePolicy,
    OrderingPolicy,
    ProjectContext,
    ProjectRef,
    ProjectReport,
    ProjectStats,
    ProjectStatus,
    RunMode,
    Severity,
    WorkspaceConfig,
    WorkspaceReport,
    WorkspaceSummary,
)
from majordomus.core.plugins.host import PluginHost
from majordomus.core.ports.schema_validator import JsonSchemaValidatorPort
from majordomus.core.project_engine import ProjectEngine
from majordomus.core.util.parsing import parse_yaml_file
from majordomus.core.util.paths import resolve_project_root
from majordomus.core.util.sorting import sort_issues


class WorkspaceEngine:
    def __init__(
        self,
        project_engine: ProjectEngine,
        schema_validator: JsonSchemaValidatorPort,
        plugin_host: PluginHost | None = None,
    ) -> None:
        self._project_engine = project_engine
        self._schema_validator = schema_validator
        self._plugin_host = plugin_host or PluginHost([])

    def run(self, workspace_file: Path, *, mode: RunMode) -> WorkspaceReport:
        config, issues = self.load_workspace(workspace_file)
        if config is None:
            summary = WorkspaceSummary(
                total_projects=0,
                passed_projects=0,
                failed_projects=0,
                skipped_projects=0,
                errors=sum(1 for item in issues if item.severity == Severity.ERROR),
                warns=sum(1 for item in issues if item.severity == Severity.WARN),
            )
            return WorkspaceReport(
                workspace=str(workspace_file),
                mode=mode,
                ordering=OrderingPolicy.AS_LISTED,
                project_reports=[],
                issues=sort_issues(issues),
                summary=summary,
                exit_code=2,
            )

        self._plugin_host.on_workspace_loaded(config)

        project_refs = list(config.projects)
        if config.ordering == OrderingPolicy.BY_NAME:
            project_refs.sort(key=lambda item: item.name)

        project_reports: list[ProjectReport] = []
        for project_ref in project_refs:
            try:
                project_root = resolve_project_root(workspace_file, project_ref.path)
            except ValueError:
                issue = Issue(
                    code="PRJ001",
                    severity=Severity.ERROR,
                    message=f"Project path escapes workspace root: {project_ref.path}",
                    location=Location(path=str(workspace_file)),
                    project=project_ref.name,
                )
                project_reports.append(
                    ProjectReport(
                        project=project_ref.name,
                        status=ProjectStatus.FAIL,
                        issues=[issue],
                        stats=ProjectStats(tasks=0, errors=1, warns=0, time_ms=0),
                    )
                )
                continue
            missing_policy = project_ref.missing_governance or config.default_missing_governance
            governance_dir = project_ref.governance_dir or config.default_governance_dir

            ctx = ProjectContext(
                project=project_ref.name,
                project_root=project_root,
                governance_dir=governance_dir,
                missing_governance=missing_policy,
                mode=mode,
            )
            self._plugin_host.on_project_context_created(ctx)

            try:
                report = self._project_engine.run(ctx)
            except Exception as exc:
                report = ProjectReport(
                    project=project_ref.name,
                    status=ProjectStatus.FAIL,
                    issues=[
                        Issue(
                            code="PRJ500",
                            severity=Severity.ERROR,
                            message=f"Internal project validation error: {exc}",
                            location=Location(path=str(project_root)),
                            project=project_ref.name,
                        )
                    ],
                    stats=ProjectStats(tasks=0, errors=1, warns=0, time_ms=0),
                )
            project_reports.append(report)
            self._plugin_host.on_project_validated(report)

        summary = _build_summary(project_reports)
        exit_code = 0 if summary.failed_projects == 0 and summary.errors == 0 else 2

        return WorkspaceReport(
            workspace=config.workspace_name,
            mode=mode,
            ordering=config.ordering,
            project_reports=project_reports,
            issues=[],
            summary=summary,
            exit_code=exit_code,
        )

    def load_workspace(self, workspace_file: Path) -> tuple[WorkspaceConfig | None, list[Issue]]:
        payload, parse_issues = parse_yaml_file(
            workspace_file,
            code="WS001",
            message="Cannot parse workspace yaml",
            project=None,
        )
        issues: list[Issue] = list(parse_issues)
        if payload is None:
            return None, sort_issues(issues)

        schema_issues = self._schema_validator.validate(
            "workspace_schema_v1.json",
            payload,
            code="WS002",
            project=None,
            location_path=str(workspace_file),
        )
        issues.extend(schema_issues)
        if schema_issues:
            return None, sort_issues(issues)

        semantic_issues = self._validate_workspace_semantics(payload, workspace_file)
        issues.extend(semantic_issues)
        if semantic_issues:
            return None, sort_issues(issues)

        config = _to_workspace_config(payload)
        return config, []

    def _validate_workspace_semantics(
        self, payload: dict[str, Any], workspace_file: Path
    ) -> list[Issue]:
        issues: list[Issue] = []
        names = [str(item["name"]) for item in payload.get("projects", [])]

        seen: set[str] = set()
        duplicates: set[str] = set()
        for name in names:
            if name in seen:
                duplicates.add(name)
            seen.add(name)

        for duplicate in sorted(duplicates):
            issues.append(
                Issue(
                    code="WS010",
                    severity=Severity.ERROR,
                    message=f"Duplicate project name: {duplicate}",
                    location=Location(path=str(workspace_file)),
                )
            )

        return sort_issues(issues)


def _to_workspace_config(payload: dict[str, Any]) -> WorkspaceConfig:
    defaults = payload.get("defaults", {})
    ordering = OrderingPolicy(defaults.get("ordering", OrderingPolicy.AS_LISTED.value))
    default_gov_dir = str(defaults.get("governance_dir", ".majordomus"))
    default_missing = MissingGovernancePolicy(defaults.get("missing_governance", "fail"))

    projects: list[ProjectRef] = []
    for item in payload["projects"]:
        missing_raw = item.get("missing_governance")
        missing_value = MissingGovernancePolicy(missing_raw) if missing_raw is not None else None
        projects.append(
            ProjectRef(
                name=str(item["name"]),
                path=str(item["path"]),
                governance_dir=str(item["governance_dir"]) if "governance_dir" in item else None,
                missing_governance=missing_value,
            )
        )

    return WorkspaceConfig(
        workspace_name=str(payload["workspace_name"]),
        ordering=ordering,
        default_governance_dir=default_gov_dir,
        default_missing_governance=default_missing,
        projects=projects,
    )


def _build_summary(project_reports: list[ProjectReport]) -> WorkspaceSummary:
    passed = sum(1 for item in project_reports if item.status == ProjectStatus.PASS)
    failed = sum(1 for item in project_reports if item.status == ProjectStatus.FAIL)
    skipped = sum(1 for item in project_reports if item.status == ProjectStatus.SKIP)
    errors = sum(item.stats.errors for item in project_reports)
    warns = sum(item.stats.warns for item in project_reports)

    return WorkspaceSummary(
        total_projects=len(project_reports),
        passed_projects=passed,
        failed_projects=failed,
        skipped_projects=skipped,
        errors=errors,
        warns=warns,
    )
