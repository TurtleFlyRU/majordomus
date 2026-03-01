class MajorDomusError(Exception):
    """Base exception for domain-level failures."""


class InternalExecutionError(MajorDomusError):
    """Raised for unexpected internal execution failures."""
