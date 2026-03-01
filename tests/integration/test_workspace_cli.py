from __future__ import annotations

import json
from pathlib import Path

from majordomus.cli.main import run

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
GOLDEN = FIXTURES / "golden"


def _run_workspace_json(capsys, workspace_file: Path) -> tuple[int, dict]:
    code = run(
        [
            "--format",
            "json",
            "workspace",
            "validate",
            "--workspace-file",
            str(workspace_file),
        ]
    )
    output = capsys.readouterr().out
    return code, json.loads(output)


def test_workspace_all_pass_exit_0(capsys) -> None:
    workspace_file = FIXTURES / "workspace_all_pass" / "majordomus.workspace.yaml"

    code, payload = _run_workspace_json(capsys, workspace_file)

    assert code == 0
    assert payload["exit_code"] == 0
    assert payload["summary"]["failed_projects"] == 0
    # by_name ordering: proj_a, proj_b regardless of input list order
    assert [item["project"] for item in payload["project_reports"]] == ["proj_a", "proj_b"]
    assert all(item["stats"]["time_ms"] > 0 for item in payload["project_reports"])


def test_workspace_one_fail_exit_2_and_continue(capsys) -> None:
    workspace_file = FIXTURES / "workspace_one_fail" / "majordomus.workspace.yaml"

    code, payload = _run_workspace_json(capsys, workspace_file)

    assert code == 2
    assert payload["summary"]["failed_projects"] == 1
    assert len(payload["project_reports"]) == 2
    missing_project = next(
        item for item in payload["project_reports"] if item["project"] == "proj_missing"
    )
    assert any(issue["code"] == "PRJ001" for issue in missing_project["issues"])


def test_missing_governance_skip_results_in_skip_and_warn(capsys) -> None:
    workspace_file = FIXTURES / "workspace_missing_governance_skip" / "majordomus.workspace.yaml"

    code, payload = _run_workspace_json(capsys, workspace_file)

    assert code == 0
    assert payload["summary"]["skipped_projects"] == 1
    report = payload["project_reports"][0]
    assert report["status"] == "SKIP"
    assert any(
        issue["code"] == "PRJ011" and issue["severity"] == "WARN" for issue in report["issues"]
    )


def test_invalid_workspace_schema_exit_2(capsys) -> None:
    workspace_file = FIXTURES / "workspace_invalid_schema" / "majordomus.workspace.yaml"

    code, payload = _run_workspace_json(capsys, workspace_file)

    assert code == 2
    assert any(issue["code"] == "WS002" for issue in payload["issues"])


def test_invalid_workspace_yaml_exit_2(capsys) -> None:
    workspace_file = FIXTURES / "workspace_invalid_yaml" / "majordomus.workspace.yaml"

    code, payload = _run_workspace_json(capsys, workspace_file)

    assert code == 2
    assert any(issue["code"] == "WS001" for issue in payload["issues"])


def test_project_broken_task_json_yields_task100(capsys) -> None:
    workspace_file = FIXTURES / "workspace_broken_task_json" / "majordomus.workspace.yaml"

    code, payload = _run_workspace_json(capsys, workspace_file)

    assert code == 2
    report = payload["project_reports"][0]
    assert any(issue["code"] == "TASK100" for issue in report["issues"])


def test_workspace_json_output_is_deterministic(capsys) -> None:
    workspace_file = FIXTURES / "workspace_all_pass" / "majordomus.workspace.yaml"

    first_code = run(
        ["--format", "json", "workspace", "validate", "--workspace-file", str(workspace_file)]
    )
    first_output = capsys.readouterr().out

    second_code = run(
        ["--format", "json", "workspace", "validate", "--workspace-file", str(workspace_file)]
    )
    second_output = capsys.readouterr().out

    assert first_code == 0
    assert second_code == 0
    assert first_output == second_output


def test_workspace_json_matches_golden(capsys) -> None:
    workspace_file = FIXTURES / "workspace_all_pass" / "majordomus.workspace.yaml"
    golden_file = GOLDEN / "workspace_all_pass.validate.json"

    code, payload = _run_workspace_json(capsys, workspace_file)
    expected = json.loads(golden_file.read_text(encoding="utf-8"))

    assert code == 0
    assert len(payload["project_reports"]) == len(expected["project_reports"])
    for index, report in enumerate(payload["project_reports"]):
        assert report["stats"]["time_ms"] > 0
        expected["project_reports"][index]["stats"]["time_ms"] = report["stats"]["time_ms"]
    assert payload == expected


def test_trinity_invalid_policy_schema_yields_pol100(capsys) -> None:
    workspace_file = FIXTURES / "workspace_policy_invalid" / "majordomus.workspace.yaml"

    code, payload = _run_workspace_json(capsys, workspace_file)

    assert code == 2
    report = payload["project_reports"][0]
    assert any(issue["code"] == "POL100" for issue in report["issues"])


def test_trinity_forbidden_transition_by_policy_yields_pol201(capsys) -> None:
    workspace_file = FIXTURES / "workspace_policy_forbidden" / "majordomus.workspace.yaml"

    code, payload = _run_workspace_json(capsys, workspace_file)

    assert code == 2
    report = payload["project_reports"][0]
    assert any(issue["code"] == "POL201" for issue in report["issues"])


def test_trinity_missing_sections_yield_task300(capsys) -> None:
    workspace_file = FIXTURES / "workspace_trinity_missing_sections" / "majordomus.workspace.yaml"

    code, payload = _run_workspace_json(capsys, workspace_file)

    assert code == 2
    report = payload["project_reports"][0]
    assert any(issue["code"] == "TASK300" for issue in report["issues"])
