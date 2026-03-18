from __future__ import annotations

from typing import TYPE_CHECKING

from majordomus.core.domain import ProjectContext, ProjectReport, WorkspaceConfig

from .base import BasePlugin

if TYPE_CHECKING:
    from majordomus.core.domain import Issue
    from majordomus.core.governance.state_machine import StateMachine


class PluginHost:
    def __init__(self, plugins: list[BasePlugin] | None = None) -> None:
        self._plugins = list(plugins or [])

    def on_workspace_loaded(self, workspace_config: WorkspaceConfig) -> None:
        for plugin in self._plugins:
            plugin.on_workspace_loaded(workspace_config)

    def on_project_context_created(self, project_ctx: ProjectContext) -> None:
        for plugin in self._plugins:
            plugin.on_project_context_created(project_ctx)

    def on_governance_loaded(
        self, project_id: str, roles: set[str], state_machine: StateMachine
    ) -> None:
        for plugin in self._plugins:
            plugin.on_governance_loaded(project_id, roles, state_machine)

    def on_task_validated(self, task_id: str, issues: list[Issue]) -> None:
        for plugin in self._plugins:
            plugin.on_task_validated(task_id, issues)

    def on_project_validated(self, project_report: ProjectReport) -> None:
        for plugin in self._plugins:
            plugin.on_project_validated(project_report)
