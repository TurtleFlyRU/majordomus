from __future__ import annotations

from typing import TYPE_CHECKING, Any

from majordomus.core.domain import ProjectContext, ProjectReport, WorkspaceConfig

if TYPE_CHECKING:
    from majordomus.core.domain import Issue
    from majordomus.core.governance.state_machine import StateMachine


class BasePlugin:
    def on_workspace_loaded(self, workspace_config: WorkspaceConfig) -> None:
        return None

    def on_project_context_created(self, project_ctx: ProjectContext) -> None:
        return None

    def on_governance_loaded(
        self, project_id: str, roles: set[str], state_machine: StateMachine
    ) -> None:
        return None

    def on_task_validated(self, task_id: str, issues: list[Issue]) -> None:
        return None

    def on_project_validated(self, project_report: ProjectReport) -> None:
        return None
