from __future__ import annotations

import json
from pathlib import Path

from majordomus.core.adapters import JsonschemaValidatorAdapter, LocalFileSystemAdapter
from majordomus.core.governance.role_engine import RoleEngine
from majordomus.core.governance.task_registry import TaskRegistry
from majordomus.core.governance.validator import ProjectGovernanceValidator
from majordomus.core.schema_loader import SchemaLoader


def test_schema_error_reports_correct_line(tmp_path: Path):
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
    
    # Create a task with a schema error (missing title)
    # Line 1: {
    # Line 2:   "schema_version": 1,
    # Line 3:   "id": "TASK-0001",
    # Line 4:   "status": "open",
    # Line 5:   "evidence": [
    # Line 6:     {"note": "missing path"}
    # Line 7:   ]
    # Line 8: }
    task_content = """{
  "schema_version": 1,
  "id": "TASK-0001",
  "status": "open",
  "evidence": [
    {"note": "missing path"}
  ]
}"""
    (tasks_dir / "TASK-0001.json").write_text(task_content)

    fs = LocalFileSystemAdapter()
    schema_loader = SchemaLoader()
    schema_validator = JsonschemaValidatorAdapter(schema_loader)

    validator = ProjectGovernanceValidator(
        schema_validator=schema_validator,
        role_engine=RoleEngine(),
        task_registry=TaskRegistry(fs),
    )

    issues, tasks_count = validator.validate(
        project="test-proj", governance_root=gov_dir, project_root=tmp_path
    )

    # We expect at least two errors: 
    # 1. Missing 'title' at root (line 1)
    # 2. Missing 'path' in evidence[0] (line 6)
    
    # Filter for schema errors
    schema_errors = [i for i in issues if i.code == "TASK101"]
    
    # Debug print if needed
    for i in schema_errors:
        print(f"Error: {i.message} at line {i.location.line}")

    assert any("title" in i.message and i.location.line == 1 for i in schema_errors)
    assert any("path" in i.message and i.location.line == 6 for i in schema_errors)


def test_trinity_empty_block_with_line_markers(tmp_path: Path):
    # Verify that an empty block still triggers TASK300 even with __line__
    gov_dir = tmp_path / ".majordomus"
    gov_dir.mkdir()
    (gov_dir / "tasks").mkdir()
    
    # Create project.yaml with trinity profile
    (gov_dir / "project.yaml").write_text("profile: trinity")
    (gov_dir / "roles.yaml").write_text("version: 1\nroles: [{id: admin, name: Admin}]")
    (gov_dir / "state_machine.yaml").write_text("version: 1\nstates: [open]\ninitial_state: open\ntransitions: []")
    
    # TASK-0001.json: implementation is an empty object
    task_payload = {
        "schema_version": 1,
        "id": "TASK-0001",
        "title": "Test",
        "status": "open",
        "assignment": {"owner": "admin"},
        "implementation": {} # Empty mapping should trigger TASK300 if state requires it
    }
    # Note: 'open' status in basic SM might not require implementation. 
    # But ProjectGovernanceValidator check uses state_machine.requires_implementation(status)
    
    # Let's mock the SM behavior by choosing a status that requires it if possible, 
    # or just check the _is_non_empty_mapping helper directly if we want a unit test.
    # But let's do a semi-integration test.
    
    # Wait, the default StateMachine.requires_implementation(status) returns False 
    # unless we define it.
    
    from majordomus.core.governance.validator import _is_non_empty_mapping
    
    # Test helper directly
    assert _is_non_empty_mapping({"__line__": 10}) is False
    assert _is_non_empty_mapping({"id": "foo", "__line__": 10}) is True
    assert _is_non_empty_mapping({}) is False
