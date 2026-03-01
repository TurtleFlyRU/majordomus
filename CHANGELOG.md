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
  - `role_policy_schema_v1.json`
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
- `majordomus init --profile trinity` bootstrap profile.
- Role policy enforcement (`POL100`, `POL200`) and Trinity task payload checks (`TASK300`).
- `majordomus init` default profile switched to `trinity` with full prompt/task/policy bundle.
- Trinity bootstrap now also generates integrated ARCH/DEV methodology docs in RU/EN.
- Human/JSON renderers and exit code contract (`0/2/3/4`).
- Test suite with fixtures and deterministic golden output test.
- `Makefile` targets: `fmt`, `lint`, `typecheck`, `test`, `ci`.

### Changed
- `pyproject.toml` finalized for packaging and entrypoint.
- Runtime dependency constraint adjusted to `jsonschema>=4.10` for offline-compatible environment.
- Governance architecture stabilization (no public API changes):
  - centralized error-code taxonomy in `core/domain/error_codes.py`
  - split overloaded codes: `PRJ010` (path escape) vs `PRJ011` (missing governance)
  - split policy violations: `POL200` (state violation) vs `POL201` (permission denied)
  - split generic project validation code into `PRJ101` (parse), `PRJ102` (schema), `PRJ103` (semantic)
  - removed enum string comparison (`missing_governance == MissingGovernancePolicy.SKIP`)
  - removed hidden `governance_root.parent` dependency by passing `project_root` internally
  - removed hardcoded Trinity status sets via `StateMachine.requires_*` methods
  - enabled real timing in `ProjectReport.stats.time_ms`

### Verified
- `pip install -e .` works in clean virtual environment.
- `majordomus --help` works.
- `make ci` passes:
  - `ruff format .`
  - `ruff check .`
  - `mypy src`
  - `pytest` (`16 passed`)
