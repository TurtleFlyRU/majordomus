from __future__ import annotations

import json
from pathlib import Path

from majordomus.cli.main import run

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_project_validate_broken_json_returns_exit_2_and_task100(capsys) -> None:
    project_root = FIXTURES / "workspace_broken_task_json" / "projects" / "proj_bad"

    code = run(["--format", "json", "validate", "--path", str(project_root)])
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert code == 2
    assert payload["status"] == "FAIL"
    assert any(issue["code"] == "TASK100" for issue in payload["issues"])
