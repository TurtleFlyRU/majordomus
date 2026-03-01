# Changelog

## 0.1.0 - 2026-03-01

### Added
- Full Major Domus v1 package in `src-layout`.
- Domain contracts: DTOs/enums for issues and reports.
- Deterministic utilities: issue sorting and safe path join.
- Built-in JSON schemas:
  - `workspace_schema_v1.json`
  - `roles_schema_v1.json`
  - `state_machine_schema_v1.json`
  - `task_schema_v1.json`
- Schema loading via `importlib.resources`.
- Governance layer:
  - role validation
  - state-machine invariants
  - task registry (`tasks/*.json`, non-recursive)
  - project semantic validator
- Engines:
  - `ProjectEngine`
  - `WorkspaceEngine`
- Plugin system v1 hooks (`PluginHost`, `BasePlugin`).
- CLI commands:
  - `majordomus init`
  - `majordomus validate`
  - `majordomus workspace validate|status|audit`
- Human/JSON renderers and exit code contract (`0/2/3/4`).
- Test suite with fixtures and deterministic golden output test.
- `Makefile` targets: `fmt`, `lint`, `typecheck`, `test`, `ci`.

### Changed
- `pyproject.toml` finalized for packaging and entrypoint.
- Runtime dependency constraint adjusted to `jsonschema>=4.10` for offline-compatible environment.

### Verified
- `pip install -e .` works in clean virtual environment.
- `majordomus --help` works.
- `make ci` passes:
  - `ruff format .`
  - `ruff check .`
  - `mypy src`
  - `pytest` (`16 passed`)
