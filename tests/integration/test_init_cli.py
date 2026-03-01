from __future__ import annotations

import json
from pathlib import Path

from majordomus.cli.main import run


def test_init_bootstraps_project_and_validate_passes(capsys, tmp_path: Path) -> None:
    code = run(["--format", "json", "init", "--path", str(tmp_path)])
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert code == 0
    assert (tmp_path / ".majordomus" / "roles.yaml").is_file()
    assert (tmp_path / ".majordomus" / "state_machine.yaml").is_file()
    assert (tmp_path / ".majordomus" / "tasks" / "TASK-0001.json").is_file()
    assert (tmp_path / "majordomus.workspace.yaml").is_file()
    assert payload["project_root"] == str(tmp_path.resolve())

    project_code = run(["--format", "json", "validate", "--path", str(tmp_path)])
    project_out = json.loads(capsys.readouterr().out)

    assert project_code == 0
    assert project_out["status"] == "PASS"

    ws_code = run(
        [
            "--format",
            "json",
            "workspace",
            "validate",
            "--workspace-file",
            str(tmp_path / "majordomus.workspace.yaml"),
        ]
    )
    ws_out = json.loads(capsys.readouterr().out)

    assert ws_code == 0
    assert ws_out["summary"]["failed_projects"] == 0


def test_init_is_idempotent_without_force(capsys, tmp_path: Path) -> None:
    first_code = run(["--format", "json", "init", "--path", str(tmp_path)])
    _ = capsys.readouterr().out
    second_code = run(["--format", "json", "init", "--path", str(tmp_path)])
    second_output = capsys.readouterr().out
    payload = json.loads(second_output)

    assert first_code == 0
    assert second_code == 0
    statuses = [item["status"] for item in payload["actions"]]
    assert all(status == "skipped" for status in statuses)
