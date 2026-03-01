from majordomus.core.governance.policy_engine import RolePolicy


def test_policy_engine_matches_rules_deterministically() -> None:
    payload = {
        "version": 1,
        "default_actions": ["VIEW"],
        "rules": [
            {"role": "DEV", "pattern": "src/**", "actions": ["EDIT"]},
            {"role": "DEV", "pattern": "src/**", "actions": ["TRANSITION"]},
        ],
    }
    policy = RolePolicy.from_payload(payload)

    allowed = policy.allowed_actions(role="DEV", relative_path="src/app.py")

    assert allowed == ("EDIT", "TRANSITION")


def test_policy_engine_uses_default_actions_when_no_rule_matches() -> None:
    payload = {
        "version": 1,
        "default_actions": ["VIEW"],
        "rules": [
            {"role": "ARCH", "pattern": "doc/**", "actions": ["EDIT"]},
        ],
    }
    policy = RolePolicy.from_payload(payload)

    assert policy.can(role="DEV", relative_path="src/app.py", action="VIEW") is True
    assert policy.can(role="DEV", relative_path="src/app.py", action="EDIT") is False
