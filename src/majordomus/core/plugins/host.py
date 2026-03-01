from __future__ import annotations

from majordomus.core.domain import ProjectContext, ProjectReport, WorkspaceConfig

from .base import BasePlugin


class PluginHost:
    def __init__(self, plugins: list[BasePlugin] | None = None) -> None:
        self._plugins = list(plugins or [])

    def on_workspace_loaded(self, workspace_config: WorkspaceConfig) -> None:
        for plugin in self._plugins:
            plugin.on_workspace_loaded(workspace_config)

    def on_project_context_created(self, project_ctx: ProjectContext) -> None:
        for plugin in self._plugins:
            plugin.on_project_context_created(project_ctx)

    def on_project_validated(self, project_report: ProjectReport) -> None:
        for plugin in self._plugins:
            plugin.on_project_validated(project_report)
