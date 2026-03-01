from majordomus.core.governance.state_machine import StateMachine


def test_state_machine_initial_state_must_exist() -> None:
    payload = {
        "version": 1,
        "states": ["todo", "done"],
        "initial_state": "unknown",
        "transitions": [],
    }

    machine, issues = StateMachine.from_payload(
        payload,
        project="proj",
        location_path="state_machine.yaml",
        known_roles={"dev"},
    )

    assert machine is None
    assert any(issue.code == "PRJ202" for issue in issues)


def test_state_machine_duplicate_transition_pair_is_invalid() -> None:
    payload = {
        "version": 1,
        "states": ["todo", "done"],
        "initial_state": "todo",
        "transitions": [
            {"from": "todo", "to": "done", "allowed_roles": ["dev"]},
            {"from": "todo", "to": "done", "allowed_roles": ["dev"]},
        ],
    }

    machine, issues = StateMachine.from_payload(
        payload,
        project="proj",
        location_path="state_machine.yaml",
        known_roles={"dev"},
    )

    assert machine is None
    assert any(
        issue.code == "PRJ202" and "Duplicate transition" in issue.message for issue in issues
    )


def test_state_machine_requirement_checks_follow_state_order_and_roles() -> None:
    payload = {
        "version": 1,
        "states": ["draft", "approved", "in_progress", "dev_done", "qa_done", "done"],
        "initial_state": "draft",
        "transitions": [
            {"from": "draft", "to": "approved", "allowed_roles": ["ARCH"]},
            {"from": "approved", "to": "in_progress", "allowed_roles": ["DEV"]},
            {"from": "in_progress", "to": "dev_done", "allowed_roles": ["DEV"]},
            {"from": "dev_done", "to": "qa_done", "allowed_roles": ["AUDITOR"]},
            {"from": "qa_done", "to": "done", "allowed_roles": ["ARCH"]},
        ],
    }

    machine, issues = StateMachine.from_payload(
        payload,
        project="proj",
        location_path="state_machine.yaml",
        known_roles={"ARCH", "DEV", "AUDITOR"},
    )

    assert issues == []
    assert machine is not None
    assert machine.requires_implementation("in_progress") is False
    assert machine.requires_implementation("dev_done") is True
    assert machine.requires_verification("dev_done") is False
    assert machine.requires_verification("qa_done") is True
