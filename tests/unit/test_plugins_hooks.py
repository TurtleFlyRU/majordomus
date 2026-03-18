from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from majordomus.core.adapters import JsonschemaValidatorAdapter, LocalFileSystemAdapter
from majordomus.core.domain import Issue, Location, Severity
from majordomus.core.governance.role_engine import RoleEngine
from majordomus.core.governance.state_machine import StateMachine
from majordomus.core.governance.task_registry import TaskRegistry
from majordomus.core.governance.validator import ProjectGovernanceValidator
from majordomus.core.plugins.base import BasePlugin
from majordomus.core.plugins.host import PluginHost
from majordomus.core.schema_loader import SchemaLoader


class MockPlugin(BasePlugin):
    def __init__(self):
        self.governance_loaded_calls = []
        self.task_validated_calls = []

    def on_governance_loaded(
        self, project_id: str, roles: set[str], state_machine: StateMachine
    ) -> None:
        self.governance_loaded_calls.append((project_id, roles, state_machine))

    def on_task_validated(self, task_id: str, issues: list[Issue]) -> None:
        self.task_validated_calls.append((task_id, issues))


def test_validator_calls_plugin_hooks(tmp_path: Path):
    # Setup project structure
    gov_dir = tmp_path / ".majordomus"
    gov_dir.mkdir()
    tasks_dir = gov_dir / "tasks"
    tasks_dir.mkdir()

    # Create roles.yaml
    (gov_dir / "roles.yaml").write_text(
        "version: 1\nroles: [{id: admin, name: Administrator}]"
    )
    # Create state_machine.yaml
    (gov_dir / "state_machine.yaml").write_text(
        "version: 1\nstates: [open]\ninitial_state: open\ntransitions: []"
    )
    # Create a task
    task_payload = {
        "schema_version": 1,
        "id": "TASK-0001",
        "title": "Test Task",
        "status": "open"
    }
    (tasks_dir / "TASK-0001.json").write_text(json.dumps(task_payload))

    fs = LocalFileSystemAdapter()
    schema_loader = SchemaLoader()
    schema_validator = JsonschemaValidatorAdapter(schema_loader)

    plugin = MockPlugin()
    plugin_host = PluginHost([plugin])

    validator = ProjectGovernanceValidator(
        schema_validator=schema_validator,
        role_engine=RoleEngine(),
        task_registry=TaskRegistry(fs),
        plugin_host=plugin_host,
    )

    validator.validate(project="test-proj", governance_root=gov_dir, project_root=tmp_path)

    assert len(plugin.governance_loaded_calls) == 1
    assert plugin.governance_loaded_calls[0][0] == "test-proj"
    assert "admin" in plugin.governance_loaded_calls[0][1]

    assert len(plugin.task_validated_calls) == 1
    assert plugin.task_validated_calls[0][0] == "TASK-0001"
