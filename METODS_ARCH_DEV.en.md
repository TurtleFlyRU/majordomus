# Methodology: Guide for ARCH and DEV

This document defines a practical working method for two key roles:
- **ARCH (Architect)**
- **DEV (Developer)**

It is aligned with `majordomus` and the `trinity` profile.

## 1. Role responsibilities

### ARCH
Owns:
- task definition (goal, boundaries, constraints, acceptance criteria),
- architecture and contract decisions,
- approvals and final transitions (`draft -> approved`, `qa_done -> arch_review`, `arch_review -> done`),
- final acceptance based on evidence.

Does not do:
- implementation instead of DEV,
- verification instead of AUDITOR.

### DEV
Owns:
- implementation within `assignment.scope_in`,
- `implementation` section updates,
- transitions `approved -> in_progress -> dev_done`,
- code quality gates (lint/types/tests).

Does not do:
- architecture changes outside task scope,
- final acceptance instead of ARCH/AUDITOR.

## 2. Canonical workflow

1. ARCH creates/updates `TASK-XXXX.json` with:
- `assignment.goal`
- `assignment.scope_in`
- `assignment.scope_out`
- `assignment.constraints`
- `acceptance_checks`

2. ARCH transitions `draft -> approved`.

3. DEV transitions `approved -> in_progress`, implements, fills `implementation`, then moves to `dev_done`.

4. AUDITOR verifies, fills `verification`, `evidence`, updates `acceptance_checks`, then moves to `qa_done` (or returns to `in_progress`).

5. ARCH performs final review and either:
- closes `qa_done -> arch_review -> done`, or
- returns `arch_review -> in_progress` with a clear reason.

## 3. Required artifacts

Mandatory governance files:
- `.majordomus/roles.yaml`
- `.majordomus/state_machine.yaml`
- `.majordomus/project.yaml`
- `.majordomus/policies/role_policy.json`
- `.majordomus/tasks/TASK-XXXX.json`

Supporting artifacts:
- `.majordomus/templates/*.json`
- `.majordomus/docs/pipeline.json`
- `.majordomus/docs/prompts/*.system.md`

## 4. ARCH method

ARCH must ensure every task has:
1. **Goal**: one measurable outcome.
2. **Scope in/out**: explicit inclusion and exclusion boundaries.
3. **Constraints**: contract-first, deterministic behavior, no hidden side effects.
4. **Acceptance checks**: objectively testable criteria.
5. **Resources**: links to required docs/templates.

ARCH rule:
- If a criterion cannot be verified, it is not an acceptance criterion.

## 5. DEV method

DEV starts only after `approved`.

Execution order:
1. Confirm task status is `approved`.
2. Transition to `in_progress` with a clear note.
3. Implement only `scope_in`.
4. Fill `implementation`:
- `changed_files`
- `checks_run`
- `artifacts`
5. Transition to `dev_done`.

DEV rule:
- Any out-of-scope change must become a separate task.

## 6. Definition of Done

A task can be closed as `done` only if:
1. `assignment` is fully complete.
2. For post-`dev_done` states, `implementation` and `verification` are complete.
3. `evidence` is non-empty.
4. `acceptance_checks` have final statuses.
5. Role transitions comply with `state_machine.yaml`.
6. Role actions comply with `role_policy.json`.
7. Validations pass:
```bash
majordomus --format json validate --path .
majordomus --format json workspace validate --workspace-file majordomus.workspace.yaml
```

## 7. Transition note standard

Each transition note should state:
- what was done,
- what was verified,
- what blocks the next step (if any).

Note style:
- concise,
- verifiable,
- no vague wording.

## 8. Anti-patterns (forbidden)

- Unrelated “while we are here” changes.
- Status transitions without required section updates.
- Missing evidence for `qa_done`/`done`.
- Non-testable acceptance criteria.
- Bypassing role policy or state machine.

## 9. Quick ARCH checklist

Before `approved`:
- [ ] clear goal and boundaries
- [ ] constraints set
- [ ] acceptance checks testable
- [ ] resources attached

Before `done`:
- [ ] sufficient evidence
- [ ] acceptance checks closed
- [ ] validate/workspace validate green

## 10. Quick DEV checklist

Before `dev_done`:
- [ ] only required files changed
- [ ] implementation filled
- [ ] checks executed
- [ ] transitions properly recorded

## 11. Core principle

**Contract and status discipline first, code second.**

If contract, role, or transition is not explicitly defined, execution is not ready.
