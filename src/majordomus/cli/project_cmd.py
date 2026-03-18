from __future__ import annotations

from pathlib import Path

from majordomus.core.adapters import JsonschemaValidatorAdapter, LocalFileSystemAdapter
from majordomus.core.domain import MissingGovernancePolicy, ProjectContext, ProjectReport, RunMode
from majordomus.core.governance.role_engine import RoleEngine
from majordomus.core.governance.task_registry import TaskRegistry
from majordomus.core.governance.validator import ProjectGovernanceValidator
from majordomus.core.plugins.host import PluginHost
from majordomus.core.project_engine import ProjectEngine
from majordomus.core.schema_loader import SchemaLoader


def run_project_validate(*, project_root: Path) -> ProjectReport:
    resolved_root = project_root.resolve()
    project_name = resolved_root.name or str(resolved_root)

    fs = LocalFileSystemAdapter()
    schema_loader = SchemaLoader()
    schema_validator = JsonschemaValidatorAdapter(schema_loader)
    plugin_host = PluginHost([])

    validator = ProjectGovernanceValidator(
        schema_validator=schema_validator,
        role_engine=RoleEngine(),
        task_registry=TaskRegistry(fs),
        plugin_host=plugin_host,
    )
    engine = ProjectEngine(
        fs=fs, governance_validator=validator, plugin_host=plugin_host
    )

    ctx = ProjectContext(
        project=project_name,
        project_root=resolved_root,
        governance_dir=".majordomus",
        missing_governance=MissingGovernancePolicy.FAIL,
        mode=RunMode.VALIDATE,
    )
    return engine.run(ctx)
