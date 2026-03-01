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
