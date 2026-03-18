# Major Domus v1

Major Domus v1 is a deterministic, filesystem-only governance orchestrator for multiple projects.

- Project mode: `majordomus validate`
- Workspace mode: `majordomus workspace validate|status|audit`
- Output formats: `human` and `json`
- Exit codes: `0`, `2`, `3`, `4`

## How It Works: The Philosophy

Majordomus is not just a validator; it's a **guardrail** for your development process. It enforces the **Trinity Pipeline**: a sequence of mandatory states that every task must pass through to be considered "done".

### The Trinity Pipeline
1. **DRAFT** (ARCH): The task is being defined.
2. **APPROVED** (ARCH): The goal, scope, and constraints are finalized.
3. **IN_PROGRESS** (DEV): The work is being actively done.
4. **DEV_DONE** (DEV): Coding is finished, unit tests passed.
5. **QA_DONE** (AUDITOR): Verification and evidence collected.
6. **ARCH_REVIEW** (ARCH): Final architectural check.
7. **DONE** (ARCH): Task officially closed.

### Technical Enforcement
- **State Machine:** You cannot skip steps (e.g., jumping from `APPROVED` to `DONE` is forbidden).
- **Role Discipline:** Only specific roles can trigger specific transitions (e.g., a `DEV` cannot close a task).
- **Completeness:** Certain states require specific fields (e.g., `DEV_DONE` requires `implementation.changed_files`).

## Success Path: Step-by-Step

1. **Bootstrap:** Run `majordomus init --profile trinity`. This creates your governance files and initial tasks.
2. **Acceptance:** Move `TASK-0001` from `DRAFT` to `APPROVED` by adding a transition in the JSON.
3. **Development:** Update the task to `IN_PROGRESS`, perform the work, then move to `DEV_DONE` while filling out the `implementation` section.
4. **Validation:** ALWAYS run `majordomus validate --path .` before and after any change. 
5. **Continuous Governance:** Keep the status `PASS`. If it's `FAIL`, the process is broken.

## Failure States & Troubleshooting

If `majordomus validate` returns **`status=FAIL`**, the system is "not working". Here is how to fix it:

### Common Error Codes
- **`TASK101` (Schema Error):** Your JSON is missing a required field (e.g., `schema_version: 1`).
- **`TASK201` (Transition Error):** You tried to skip a state or use an unauthorized role. Check `.majordomus/state_machine.yaml`.
- **`TASK300` (Missing Sections):** You moved to a state (like `DONE`) but didn't fill in the required sections (like `evidence` or `verification`).
- **`POL201` (Permission Denied):** You modified a file you're not allowed to touch (e.g., a DEV modified `.majordomus/` policy files).

### How to Fix
1. Read the error message carefully: it tells you the **File**, the **Task ID**, and the **Reason**.
2. Open the offending `TASK-*.json` file.
3. Fix the JSON to match the requirements of the current state.
4. Re-run `majordomus validate`.

## AI Agent Integration

Majordomus is specifically designed to control AI Agents (like Gemini CLI, Claude, etc.).
- **`GEMINI.md`**: Provides high-level instructions to the agent to respect the governance.
- **`MAJORDOMUS.md`**: Standardizes the "Compressed Transition" protocol for AI efficiency.

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
