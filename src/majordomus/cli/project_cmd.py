from __future__ import annotations

from pathlib import Path

from majordomus.core.adapters import JsonschemaValidatorAdapter, LocalFileSystemAdapter
from majordomus.core.domain import MissingGovernancePolicy, ProjectContext, ProjectReport, RunMode
from majordomus.core.governance.role_engine import RoleEngine
from majordomus.core.governance.task_registry import TaskRegistry
from majordomus.core.governance.validator import ProjectGovernanceValidator
from majordomus.core.project_engine import ProjectEngine
from majordomus.core.schema_loader import SchemaLoader


def run_project_validate(*, project_root: Path) -> ProjectReport:
    fs = LocalFileSystemAdapter()
    schema_loader = SchemaLoader()
    schema_validator = JsonschemaValidatorAdapter(schema_loader)

    validator = ProjectGovernanceValidator(
        schema_validator=schema_validator,
        role_engine=RoleEngine(),
        task_registry=TaskRegistry(fs),
    )
    engine = ProjectEngine(fs=fs, governance_validator=validator)

    ctx = ProjectContext(
        project=project_root.name,
        project_root=project_root.resolve(),
        governance_dir=".majordomus",
        missing_governance=MissingGovernancePolicy.FAIL,
        mode=RunMode.VALIDATE,
    )
    return engine.run(ctx)
