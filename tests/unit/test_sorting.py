from majordomus.core.domain import Issue, Location, Severity
from majordomus.core.util.sorting import sort_issues


def test_sort_issues_is_deterministic_by_contract_order() -> None:
    issues = [
        Issue(
            code="B002",
            severity=Severity.WARN,
            message="z-msg",
            location=Location(path="b/path"),
            project="b-project",
            task_id="TASK-0002",
        ),
        Issue(
            code="A001",
            severity=Severity.ERROR,
            message="a-msg",
            location=Location(path="a/path"),
            project="a-project",
            task_id="TASK-0001",
        ),
        Issue(
            code="A001",
            severity=Severity.ERROR,
            message="b-msg",
            location=Location(path="a/path"),
            project="a-project",
            task_id="TASK-0001",
        ),
    ]

    sorted_issues = sort_issues(issues)

    assert [issue.severity for issue in sorted_issues] == [
        Severity.ERROR,
        Severity.ERROR,
        Severity.WARN,
    ]
    assert [issue.message for issue in sorted_issues] == ["a-msg", "b-msg", "z-msg"]
