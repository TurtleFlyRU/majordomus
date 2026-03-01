from __future__ import annotations

from pathlib import Path


def safe_join(base: Path, *parts: str) -> Path:
    resolved_base = base.resolve()
    candidate = resolved_base.joinpath(*parts).resolve()
    if candidate != resolved_base and resolved_base not in candidate.parents:
        raise ValueError(f"Path escapes base directory: {candidate}")
    return candidate


def resolve_project_root(workspace_file: Path, project_path: str) -> Path:
    base = workspace_file.parent.resolve()
    return safe_join(base, project_path)
