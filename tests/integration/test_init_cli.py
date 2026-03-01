from __future__ import annotations

import json
from pathlib import Path

from majordomus.cli.main import run


def test_init_bootstraps_project_and_validate_passes(capsys, tmp_path: Path) -> None:
    code = run(["--format", "json", "init", "--path", str(tmp_path)])
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert code == 0
    assert payload["profile"] == "trinity"
    assert (tmp_path / ".majordomus" / "roles.yaml").is_file()
    assert (tmp_path / ".majordomus" / "state_machine.yaml").is_file()
    assert (tmp_path / ".majordomus" / "tasks" / "TASK-0001.json").is_file()
    assert (tmp_path / ".majordomus" / "tasks" / "TASK-0005.json").is_file()
    assert (tmp_path / ".majordomus" / "docs" / "prompts" / "arch.system.md").is_file()
    assert (tmp_path / ".majordomus" / "docs" / "methodology" / "arch_dev.ru.md").is_file()
    assert (tmp_path / ".majordomus" / "docs" / "methodology" / "arch_dev.en.md").is_file()
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


def test_init_trinity_profile_creates_policy_and_templates(capsys, tmp_path: Path) -> None:
    code = run(
        [
            "--format",
            "json",
            "init",
            "--path",
            str(tmp_path),
            "--profile",
            "trinity",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert payload["profile"] == "trinity"
    assert (tmp_path / ".majordomus" / "policies" / "role_policy.json").is_file()
    assert (tmp_path / ".majordomus" / "templates" / "task.template.json").is_file()
    assert (tmp_path / ".majordomus" / "docs" / "pipeline.json").is_file()

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
    ws_payload = json.loads(capsys.readouterr().out)
    assert ws_code == 0
    assert ws_payload["summary"]["failed_projects"] == 0


def test_init_marks_seed_tasks_as_not_executed(capsys, tmp_path: Path) -> None:
    code = run(["--format", "json", "init", "--path", str(tmp_path), "--profile", "trinity"])
    _ = json.loads(capsys.readouterr().out)

    assert code == 0
    for idx in range(1, 6):
        task_path = tmp_path / ".majordomus" / "tasks" / f"TASK-{idx:04d}.json"
        payload = json.loads(task_path.read_text(encoding="utf-8"))
        metadata = payload.get("metadata", {})
        assert metadata.get("seed_template") is True
        assert metadata.get("execution_status") == "not_executed"
