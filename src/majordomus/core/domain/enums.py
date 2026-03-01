from __future__ import annotations

from enum import StrEnum


class Severity(StrEnum):
    ERROR = "ERROR"
    WARN = "WARN"


class ProjectStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"


class MissingGovernancePolicy(StrEnum):
    FAIL = "fail"
    SKIP = "skip"


class OrderingPolicy(StrEnum):
    BY_NAME = "by_name"
    AS_LISTED = "as_listed"


class RunMode(StrEnum):
    VALIDATE = "validate"
    STATUS = "status"
    AUDIT = "audit"
