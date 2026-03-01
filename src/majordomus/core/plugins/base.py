from __future__ import annotations

from majordomus.core.domain import ProjectContext, ProjectReport, WorkspaceConfig


class BasePlugin:
    def on_workspace_loaded(self, workspace_config: WorkspaceConfig) -> None:
        return None

    def on_project_context_created(self, project_ctx: ProjectContext) -> None:
        return None

    def on_project_validated(self, project_report: ProjectReport) -> None:
        return None
