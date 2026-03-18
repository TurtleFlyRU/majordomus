from __future__ import annotations

from pathlib import Path

from majordomus.core.adapters import JsonschemaValidatorAdapter, LocalFileSystemAdapter
from majordomus.core.domain import RunMode, WorkspaceReport
from majordomus.core.governance.role_engine import RoleEngine
from majordomus.core.governance.task_registry import TaskRegistry
from majordomus.core.governance.validator import ProjectGovernanceValidator
from majordomus.core.plugins.host import PluginHost
from majordomus.core.project_engine import ProjectEngine
from majordomus.core.schema_loader import SchemaLoader
from majordomus.core.workspace_engine import WorkspaceEngine


def run_workspace_command(
    action: str,
    *,
    workspace_file: Path,
) -> WorkspaceReport:
    fs = LocalFileSystemAdapter()
    schema_loader = SchemaLoader()
    schema_validator = JsonschemaValidatorAdapter(schema_loader)
    plugin_host = PluginHost([])

    governance_validator = ProjectGovernanceValidator(
        schema_validator=schema_validator,
        role_engine=RoleEngine(),
        task_registry=TaskRegistry(fs),
        plugin_host=plugin_host,
    )
    project_engine = ProjectEngine(
        fs=fs, governance_validator=governance_validator, plugin_host=plugin_host
    )
    workspace_engine = WorkspaceEngine(
        project_engine=project_engine,
        schema_validator=schema_validator,
        plugin_host=plugin_host,
    )

    mode = RunMode(action)
    return workspace_engine.run(workspace_file=workspace_file, mode=mode)
