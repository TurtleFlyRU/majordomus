# Major Domus v1

Major Domus v1 is a deterministic, filesystem-only governance orchestrator for multiple projects.

- Project mode: `majordomus validate`
- Workspace mode: `majordomus workspace validate|status|audit`
- Output formats: `human` and `json`
- Exit codes: `0`, `2`, `3`, `4`

v1 scope explicitly excludes cross-project dependency logic (planned for v2).

## Machine-Readable Plan

Plan file: [execution_plan.yaml](execution_plan.yaml)

## Installation

Runtime install:

```bash
pip install -e .
```

Development install:

```bash
pip install -e ".[dev]"
```

## Dev Tooling

`pyproject.toml` contains:

- `[project.optional-dependencies].dev` with `pytest`, `ruff`, `mypy`, `types-PyYAML`
- `[tool.ruff]` + lint/format sections
- `[tool.mypy]`
- `[tool.pytest.ini_options]`

Minimal CI commands:

```bash
ruff format .
ruff check .
mypy src
pytest
```

Makefile shortcuts:

```bash
make fmt
make lint
make typecheck
make test
make ci
```

## Workspace Config

Create `majordomus.workspace.yaml`:

```yaml
workspace_name: my-workspace
defaults:
  ordering: by_name
  governance_dir: .majordomus
  missing_governance: fail
projects:
  - name: project-a
    path: projects/project-a
  - name: project-b
    path: projects/project-b
    missing_governance: skip
```

## Project Governance Layout

Each project is validated in isolation from its own governance directory:

```text
<project-root>/
  .majordomus/
    roles.yaml
    state_machine.yaml
    project.yaml          # optional
    tasks/
      TASK-0001.json
      TASK-0002.json
```

## CLI Usage

One-shot bootstrap in any project:

```bash
cd /path/to/your-project
majordomus init --path .
majordomus validate --path .
majordomus workspace validate --workspace-file majordomus.workspace.yaml
```

`majordomus init` now defaults to `--profile trinity` and creates:
- `.majordomus/roles.yaml`
- `.majordomus/state_machine.yaml`
- `.majordomus/project.yaml` (`profile: trinity`)
- `.majordomus/tasks/TASK-0001..TASK-0005.json`
- `.majordomus/policies/role_policy.json`
- `.majordomus/templates/*.json`
- `.majordomus/docs/pipeline.json`
- `.majordomus/docs/prompts/{arch,dev,auditor}.system.md`
- `.majordomus/docs/methodology/{arch_dev.ru,arch_dev.en}.md`
- `majordomus.workspace.yaml`

Repository guidance sources:
- [METODS.md](METODS.md) (general engineering methodology)
- [METODS_ARCH_DEV.ru.md](METODS_ARCH_DEV.ru.md) (ARCH/DEV operational guide, RU)
- [METODS_ARCH_DEV.en.md](METODS_ARCH_DEV.en.md) (ARCH/DEV operational guide, EN)

Explicit profile commands:

```bash
majordomus init --path . --profile trinity
majordomus init --path . --profile basic
```

`majordomus init` creates:
- `.majordomus/roles.yaml`
- `.majordomus/state_machine.yaml`
- `.majordomus/project.yaml`
- `.majordomus/tasks/TASK-0001.json`
- `majordomus.workspace.yaml` (unless `--no-workspace` is set)

Useful init flags:
- `--project-name <name>`
- `--workspace-file <path>`
- `--no-workspace`
- `--force` (overwrite existing bootstrap files)
- `--profile basic|trinity`

Project mode:

```bash
majordomus validate --format human
majordomus validate --format json --path ./projects/project-a
```

Workspace mode:

```bash
majordomus workspace validate --format human
majordomus workspace validate --format json --workspace-file ./majordomus.workspace.yaml
majordomus workspace status --format json
majordomus workspace audit --format json
```

For v1, `workspace status` and `workspace audit` run the same validation pipeline as `workspace validate`.

## Exit Codes

- `0` success (no FAIL projects and no ERROR issues)
- `2` validation failure
- `3` CLI usage error
- `4` internal error

## Determinism Guarantees

- Project ordering by policy: `by_name` or `as_listed`
- Task file ordering: lexicographic `tasks/*.json` (non-recursive)
- Issue ordering: `severity -> code -> project -> location.path -> task_id -> message`
- Stable JSON output ordering for arrays and issue sorting
