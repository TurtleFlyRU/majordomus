from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class InitAction:
    path: str
    status: str


@dataclass(frozen=True)
class InitReport:
    project_root: str
    project_name: str
    profile: str
    workspace_file: str | None
    actions: list[InitAction]

    def to_dict(self) -> dict[str, object]:
        return {
            "project_root": self.project_root,
            "project_name": self.project_name,
            "profile": self.profile,
            "workspace_file": self.workspace_file,
            "actions": [{"path": item.path, "status": item.status} for item in self.actions],
        }


def run_init_command(
    *,
    project_root: Path,
    project_name: str | None,
    workspace_file: Path,
    include_workspace: bool,
    force: bool,
    profile: str,
) -> InitReport:
    root = project_root.resolve()
    root.mkdir(parents=True, exist_ok=True)

    resolved_profile = profile.strip().lower()
    if resolved_profile not in {"basic", "trinity"}:
        raise ValueError(f"Unsupported profile: {profile}")

    resolved_name = project_name or root.name
    actions: list[InitAction] = []

    governance_root = root / ".majordomus"
    actions.extend(
        _build_profile_files(
            governance_root=governance_root,
            project_name=resolved_name,
            profile=resolved_profile,
            force=force,
        )
    )

    resolved_workspace_file: str | None = None
    if include_workspace:
        ws_path = workspace_file if workspace_file.is_absolute() else root / workspace_file
        ws_content = (
            f"workspace_name: {resolved_name}-workspace\n"
            "defaults:\n"
            "  ordering: as_listed\n"
            "  governance_dir: .majordomus\n"
            "  missing_governance: fail\n"
            "projects:\n"
            f"  - name: {resolved_name}\n"
            "    path: .\n"
        )
        actions.append(_write_file(ws_path, ws_content, force=force))
        resolved_workspace_file = str(ws_path)

    return InitReport(
        project_root=str(root),
        project_name=resolved_name,
        profile=resolved_profile,
        workspace_file=resolved_workspace_file,
        actions=actions,
    )


def render_init_report(report: InitReport, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True, indent=2)

    lines = [
        f"project_root={report.project_root}",
        f"project_name={report.project_name}",
        f"profile={report.profile}",
    ]
    if report.workspace_file:
        lines.append(f"workspace_file={report.workspace_file}")

    for action in report.actions:
        lines.append(f"{action.status}: {action.path}")

    lines.append("ready: run 'majordomus validate --path .'")
    if report.workspace_file is not None:
        lines.append(
            "ready: run 'majordomus workspace validate --workspace-file majordomus.workspace.yaml'"
        )
    return "\n".join(lines)


def _build_profile_files(
    *,
    governance_root: Path,
    project_name: str,
    profile: str,
    force: bool,
) -> list[InitAction]:
    if profile == "trinity":
        return _build_trinity_files(
            governance_root=governance_root,
            project_name=project_name,
            force=force,
        )

    return _build_basic_files(
        governance_root=governance_root,
        project_name=project_name,
        force=force,
    )


def _build_basic_files(
    *, governance_root: Path, project_name: str, force: bool
) -> list[InitAction]:
    tasks_dir = governance_root / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    roles_path = governance_root / "roles.yaml"
    state_machine_path = governance_root / "state_machine.yaml"
    project_yaml_path = governance_root / "project.yaml"
    task_path = tasks_dir / "TASK-0001.json"

    roles_content = (
        "version: 1\nroles:\n  - id: dev\n    name: Developer\n  - id: qa\n    name: QA\n"
    )
    sm_content = (
        "version: 1\n"
        "states: [todo, doing, done]\n"
        "initial_state: todo\n"
        "transitions:\n"
        "  - from: todo\n"
        "    to: doing\n"
        "    allowed_roles: [dev]\n"
        "  - from: doing\n"
        "    to: done\n"
        "    allowed_roles: [dev, qa]\n"
    )
    project_content = f"version: 1\nname: {project_name}\nprofile: basic\n"
    task_content = (
        json.dumps(
            {
                "schema_version": 1,
                "id": "TASK-0001",
                "title": "Bootstrap governance",
                "status": "todo",
                "owner_role": "dev",
                "transitions": [],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )

    return [
        _write_file(roles_path, roles_content, force=force),
        _write_file(state_machine_path, sm_content, force=force),
        _write_file(project_yaml_path, project_content, force=force),
        _write_file(task_path, task_content, force=force),
    ]


def _build_trinity_files(
    *, governance_root: Path, project_name: str, force: bool
) -> list[InitAction]:
    project_root = governance_root.parent

    tasks_dir = governance_root / "tasks"
    policies_dir = governance_root / "policies"
    templates_dir = governance_root / "templates"
    docs_dir = governance_root / "docs"
    prompts_dir = docs_dir / "prompts"
    methodology_dir = docs_dir / "methodology"

    tasks_dir.mkdir(parents=True, exist_ok=True)
    policies_dir.mkdir(parents=True, exist_ok=True)
    templates_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir.mkdir(parents=True, exist_ok=True)
    methodology_dir.mkdir(parents=True, exist_ok=True)

    roles_path = governance_root / "roles.yaml"
    state_machine_path = governance_root / "state_machine.yaml"
    project_yaml_path = governance_root / "project.yaml"
    policy_path = policies_dir / "role_policy.json"
    task_template_path = templates_dir / "task.template.json"
    assignment_template_path = templates_dir / "assignment.template.json"
    verification_template_path = templates_dir / "verification.template.json"
    pipeline_doc_path = docs_dir / "pipeline.json"
    arch_prompt_path = prompts_dir / "arch.system.md"
    dev_prompt_path = prompts_dir / "dev.system.md"
    auditor_prompt_path = prompts_dir / "auditor.system.md"
    methodology_ru_path = methodology_dir / "arch_dev.ru.md"
    methodology_en_path = methodology_dir / "arch_dev.en.md"

    roles_content = (
        "version: 1\n"
        "roles:\n"
        "  - id: ARCH\n"
        "    name: Architect\n"
        "  - id: DEV\n"
        "    name: Developer\n"
        "  - id: AUDITOR\n"
        "    name: Auditor\n"
    )

    sm_content = (
        "version: 1\n"
        "states: [draft, approved, in_progress, dev_done, qa_done, arch_review, done]\n"
        "initial_state: draft\n"
        "transitions:\n"
        "  - from: draft\n"
        "    to: approved\n"
        "    allowed_roles: [ARCH]\n"
        "  - from: approved\n"
        "    to: in_progress\n"
        "    allowed_roles: [DEV]\n"
        "  - from: in_progress\n"
        "    to: dev_done\n"
        "    allowed_roles: [DEV]\n"
        "  - from: dev_done\n"
        "    to: qa_done\n"
        "    allowed_roles: [AUDITOR]\n"
        "  - from: qa_done\n"
        "    to: arch_review\n"
        "    allowed_roles: [ARCH]\n"
        "  - from: arch_review\n"
        "    to: done\n"
        "    allowed_roles: [ARCH]\n"
        "  - from: qa_done\n"
        "    to: in_progress\n"
        "    allowed_roles: [AUDITOR]\n"
        "  - from: arch_review\n"
        "    to: in_progress\n"
        "    allowed_roles: [ARCH]\n"
    )

    project_content = f"version: 1\nname: {project_name}\nprofile: trinity\n"

    task_payloads = _default_trinity_tasks()
    policy_payload = _default_trinity_policy()
    task_template_payload = {
        "schema_version": 1,
        "id": "TASK-0000",
        "title": "",
        "status": "draft",
        "owner_role": "ARCH",
        "assignment": {
            "goal": "",
            "scope_in": [],
            "scope_out": [],
            "constraints": [],
            "resources": [],
        },
        "implementation": {"changed_files": [], "checks_run": [], "artifacts": []},
        "verification": {"scenarios": [], "results": [], "regressions": []},
        "evidence": [],
        "acceptance_checks": [],
        "transitions": [],
    }

    assignment_template_payload = {
        "goal": "",
        "scope_in": [""],
        "scope_out": [""],
        "constraints": [""],
        "resources": [""],
    }

    verification_template_payload = {
        "scenarios": [""],
        "results": [""],
        "regressions": [""],
    }

    pipeline_payload = {
        "pipeline": "Trinity",
        "states": [
            "draft",
            "approved",
            "in_progress",
            "dev_done",
            "qa_done",
            "arch_review",
            "done",
        ],
        "roles": ["ARCH", "DEV", "AUDITOR"],
        "gates": [
            {"from": "draft", "to": "approved", "role": "ARCH"},
            {"from": "approved", "to": "in_progress", "role": "DEV"},
            {"from": "in_progress", "to": "dev_done", "role": "DEV"},
            {"from": "dev_done", "to": "qa_done", "role": "AUDITOR"},
            {"from": "qa_done", "to": "arch_review", "role": "ARCH"},
            {"from": "arch_review", "to": "done", "role": "ARCH"},
        ],
    }

    arch_prompt, dev_prompt, auditor_prompt = _default_prompts(str(project_root))
    methodology_ru, methodology_en = _default_methodology_docs()

    actions = [
        _write_file(roles_path, roles_content, force=force),
        _write_file(state_machine_path, sm_content, force=force),
        _write_file(project_yaml_path, project_content, force=force),
        _write_file(policy_path, _to_json_text(policy_payload), force=force),
        _write_file(task_template_path, _to_json_text(task_template_payload), force=force),
        _write_file(
            assignment_template_path, _to_json_text(assignment_template_payload), force=force
        ),
        _write_file(
            verification_template_path, _to_json_text(verification_template_payload), force=force
        ),
        _write_file(pipeline_doc_path, _to_json_text(pipeline_payload), force=force),
        _write_file(arch_prompt_path, arch_prompt, force=force),
        _write_file(dev_prompt_path, dev_prompt, force=force),
        _write_file(auditor_prompt_path, auditor_prompt, force=force),
        _write_file(methodology_ru_path, methodology_ru, force=force),
        _write_file(methodology_en_path, methodology_en, force=force),
    ]

    for payload in task_payloads:
        task_path = tasks_dir / f"{payload['id']}.json"
        actions.append(_write_file(task_path, _to_json_text(payload), force=force))

    return actions


def _default_trinity_policy() -> dict[str, Any]:
    return {
        "version": 1,
        "default_actions": ["VIEW"],
        "rules": [
            {
                "role": "ARCH",
                "pattern": ".majordomus/tasks/*.json",
                "actions": ["VIEW", "TRANSITION"],
            },
            {
                "role": "DEV",
                "pattern": ".majordomus/tasks/*.json",
                "actions": ["VIEW", "TRANSITION"],
            },
            {
                "role": "AUDITOR",
                "pattern": ".majordomus/tasks/*.json",
                "actions": ["VIEW", "TRANSITION"],
            },
            {"role": "ARCH", "pattern": ".majordomus/**", "actions": ["VIEW", "EDIT"]},
            {"role": "DEV", "pattern": "src/**", "actions": ["VIEW", "EDIT"]},
            {"role": "DEV", "pattern": "tests/**", "actions": ["VIEW", "EDIT"]},
            {"role": "AUDITOR", "pattern": "tests/**", "actions": ["VIEW", "EDIT"]},
        ],
    }


def _default_trinity_tasks() -> list[dict[str, Any]]:
    return [
        {
            "schema_version": 1,
            "id": "TASK-0001",
            "title": "Bootstrap Trinity governance",
            "status": "draft",
            "owner_role": "ARCH",
            "assignment": {
                "goal": "Establish governance process and task lifecycle",
                "scope_in": ["setup governance files", "validate pipeline"],
                "scope_out": ["business feature implementation"],
                "constraints": ["contract-first", "deterministic output"],
                "resources": [
                    ".majordomus/docs/pipeline.json",
                    ".majordomus/docs/prompts/arch.system.md",
                    ".majordomus/docs/methodology/arch_dev.ru.md",
                    ".majordomus/docs/methodology/arch_dev.en.md",
                ],
            },
            "transitions": [],
        },
        {
            "schema_version": 1,
            "id": "TASK-0002",
            "title": "Define Trinity coding conventions and CI gates",
            "status": "approved",
            "owner_role": "ARCH",
            "created_at": "2026-03-01T13:20:00Z",
            "updated_at": "2026-03-01T13:28:00Z",
            "assignment": {
                "goal": "Formalize coding standards and acceptance checks for project contributors",
                "scope_in": [
                    "define lint/type/test gates",
                    "document role responsibilities",
                    "create deterministic command set",
                ],
                "scope_out": [
                    "implement business features",
                    "cross-project dependency logic",
                ],
                "constraints": [
                    "contract-first",
                    "deterministic execution",
                    "no hidden side effects",
                ],
                "resources": [
                    ".majordomus/docs/pipeline.json",
                    ".majordomus/templates/task.template.json",
                ],
            },
            "transitions": [
                {
                    "at": "2026-03-01T13:25:00Z",
                    "from": "draft",
                    "to": "approved",
                    "role": "ARCH",
                    "note": "Assignment reviewed and accepted",
                }
            ],
        },
        {
            "schema_version": 1,
            "id": "TASK-0003",
            "title": "Implement core project skeleton",
            "status": "dev_done",
            "owner_role": "DEV",
            "created_at": "2026-03-01T13:30:00Z",
            "updated_at": "2026-03-01T13:45:00Z",
            "assignment": {
                "goal": "Create initial source and test folder layout",
                "scope_in": [
                    "create package skeleton",
                    "add placeholders for core modules",
                    "add basic unit test scaffolding",
                ],
                "scope_out": ["advanced integrations", "deployment automation"],
                "constraints": [
                    "maintain deterministic file naming",
                    "preserve role boundaries",
                ],
                "resources": [".majordomus/templates/task.template.json"],
            },
            "implementation": {
                "changed_files": [
                    "src/barseek/__init__.py",
                    "src/barseek/core/__init__.py",
                    "tests/unit/test_smoke.py",
                ],
                "checks_run": ["ruff check .", "mypy src", "pytest"],
                "artifacts": ["logs/build-skeleton.log"],
            },
            "transitions": [
                {
                    "at": "2026-03-01T13:33:00Z",
                    "from": "approved",
                    "to": "in_progress",
                    "role": "DEV",
                    "note": "Development started",
                },
                {
                    "at": "2026-03-01T13:44:00Z",
                    "from": "in_progress",
                    "to": "dev_done",
                    "role": "DEV",
                    "note": "Implementation complete, awaiting QA",
                },
            ],
        },
        {
            "schema_version": 1,
            "id": "TASK-0004",
            "title": "QA verify skeleton quality and determinism",
            "status": "qa_done",
            "owner_role": "AUDITOR",
            "created_at": "2026-03-01T13:40:00Z",
            "updated_at": "2026-03-01T13:58:00Z",
            "assignment": {
                "goal": "Validate CI checks and deterministic behavior for skeleton baseline",
                "scope_in": [
                    "execute verification scenarios",
                    "record evidence artifacts",
                    "check regressions",
                ],
                "scope_out": ["new feature development"],
                "constraints": ["evidence-based reporting", "repeatable results"],
                "resources": [".majordomus/docs/pipeline.json"],
            },
            "implementation": {
                "changed_files": ["tests/integration/test_workspace_flow.py"],
                "checks_run": ["pytest -q", "ruff check ."],
                "artifacts": ["logs/qa-verify-task-0004.log"],
            },
            "verification": {
                "scenarios": [
                    "run full validation pipeline",
                    "repeat pipeline and compare output",
                    "negative check for malformed task payload",
                ],
                "results": [
                    "pipeline returned exit code 0",
                    "repeated output matched",
                    "negative check produced expected issue codes",
                ],
                "regressions": ["none observed"],
            },
            "evidence": [
                {
                    "name": "pytest_report",
                    "path": "logs/qa-verify-task-0004.log",
                    "kind": "test-log",
                    "result": "pass",
                },
                {
                    "name": "validation_output",
                    "path": "logs/validation-task-0004.json",
                    "kind": "json-report",
                    "result": "pass",
                },
            ],
            "acceptance_checks": [
                {
                    "id": "AC-1",
                    "status": "pass",
                    "note": "All mandatory checks green",
                },
                {
                    "id": "AC-2",
                    "status": "pass",
                    "note": "Determinism confirmed",
                },
            ],
            "transitions": [
                {
                    "at": "2026-03-01T13:46:00Z",
                    "from": "dev_done",
                    "to": "qa_done",
                    "role": "AUDITOR",
                    "note": "QA verification complete",
                }
            ],
        },
        {
            "schema_version": 1,
            "id": "TASK-0005",
            "title": "Architect final review and close baseline phase",
            "status": "done",
            "owner_role": "ARCH",
            "created_at": "2026-03-01T13:50:00Z",
            "updated_at": "2026-03-01T14:05:00Z",
            "assignment": {
                "goal": "Perform final architecture review and close the initial governance phase",
                "scope_in": [
                    "review QA evidence",
                    "confirm readiness",
                    "close task with acceptance",
                ],
                "scope_out": ["follow-up feature tasks"],
                "constraints": [
                    "architect sign-off required",
                    "all acceptance checks must pass",
                ],
                "resources": [
                    ".majordomus/tasks/TASK-0004.json",
                    ".majordomus/docs/pipeline.json",
                ],
            },
            "implementation": {
                "changed_files": [".majordomus/tasks/TASK-0005.json"],
                "checks_run": [
                    "majordomus --format json validate --path .",
                    (
                        "majordomus --format json workspace validate "
                        "--workspace-file majordomus.workspace.yaml"
                    ),
                ],
                "artifacts": ["logs/arch-review-task-0005.log"],
            },
            "verification": {
                "scenarios": [
                    "review all prior gate transitions",
                    "verify policy compliance",
                ],
                "results": [
                    "all transitions role-compliant",
                    "policy checks passed",
                ],
                "regressions": ["none"],
            },
            "evidence": [
                {
                    "name": "arch_review_log",
                    "path": "logs/arch-review-task-0005.log",
                    "kind": "review-log",
                    "result": "pass",
                },
                {
                    "name": "workspace_report",
                    "path": "logs/workspace-task-0005.json",
                    "kind": "json-report",
                    "result": "pass",
                },
            ],
            "acceptance_checks": [
                {
                    "id": "AC-1",
                    "status": "pass",
                    "note": "Architecture review approved",
                },
                {
                    "id": "AC-2",
                    "status": "pass",
                    "note": "Governance baseline closed",
                },
            ],
            "transitions": [
                {
                    "at": "2026-03-01T14:00:00Z",
                    "from": "qa_done",
                    "to": "arch_review",
                    "role": "ARCH",
                    "note": "Entered architecture review",
                },
                {
                    "at": "2026-03-01T14:04:00Z",
                    "from": "arch_review",
                    "to": "done",
                    "role": "ARCH",
                    "note": "Task closed",
                },
            ],
        },
    ]


def _default_prompts(project_root: str) -> tuple[str, str, str]:
    arch = f"""[ROLE: ARCH]

Работаем в проекте {project_root}.
Ты действуешь как ARCH в Trinity governance.

Обязательные входы перед любым действием:
1) {project_root}/.majordomus/roles.yaml
2) {project_root}/.majordomus/state_machine.yaml
3) {project_root}/.majordomus/policies/role_policy.json
4) целевой TASK-*.json

Твоя цель:
- формировать assignment,
- принимать/отклонять результаты DEV и AUDITOR,
- закрывать задачи в done только при полном evidence.

Правила:
- не меняй несвязанные файлы,
- соблюдай allowed_roles в state_machine,
- соблюдай policy actions в role_policy,
- все изменения task только через валидный status + transitions,
- если данных для приемки не хватает, возвращай задачу в in_progress с явной причиной.

Формат выполнения:
1) Короткий план (3-6 пунктов).
2) Изменения файлов.
3) Обновление TASK-*.json (status/transitions/sections).
4) Прогон:
   - majordomus --format json validate --path .
   - majordomus --format json workspace validate --workspace-file majordomus.workspace.yaml
5) Итог:
   - финальный status,
   - какие acceptance_checks pass/fail,
   - список evidence (path + result).

Работай до полностью завершенного результата в рамках этой задачи.
"""

    dev = f"""[ROLE: DEV]

Работаем в проекте {project_root}.
Ты действуешь как DEV в Trinity governance.

Перед началом:
1) прочитай TASK-*.json
2) проверь role constraints в roles/state_machine/role_policy
3) убедись, что переход approved -> in_progress зафиксирован (или зафиксируй его ролью DEV)

Твоя цель:
- реализовать задачу в рамках assignment.scope_in,
- заполнить implementation и при необходимости verification/evidence,
- довести задачу минимум до dev_done.

Обязательные правила:
- не выходить за scope_in,
- не менять scope_out,
- не делать рефакторинг вне задачи,
- фиксировать transitions с UTC временем и понятной note,
- все checks_run писать в implementation.checks_run.

Формат ответа:
1) Что сделал.
2) Какие файлы изменил.
3) Как обновил TASK-*.json (status, transitions, implementation).
4) Результаты validate/workspace validate.
5) Что нужно от AUDITOR дальше.

Если есть блокер — явно укажи его и предложи минимальный безопасный обход.
"""

    auditor = f"""[ROLE: AUDITOR]

Работаем в проекте {project_root}.
Ты действуешь как AUDITOR в Trinity governance.

Перед началом:
1) прочитай TASK-*.json
2) проверь state_machine и role_policy
3) убедись, что задача в dev_done (или объясни почему нельзя принимать)

Твоя цель:
- провести проверку результатов DEV,
- заполнить verification/results/regressions,
- добавить evidence и acceptance_checks,
- перевести задачу в qa_done или вернуть в in_progress с причиной.

Обязательные правила:
- никаких изменений архитектуры/контрактов без основания,
- evidence должен быть конкретный: name/path/kind/result,
- при fail обязательно укажи точный критерий, который не выполнен.

Формат ответа:
1) Сценарии проверки (что проверялось).
2) Результаты по каждому сценарию.
3) Список evidence.
4) Обновления TASK-*.json (verification/evidence/acceptance_checks/transitions/status).
5) Результат validate/workspace validate.

Если всё корректно — готовишь задачу к ARCH review.
"""

    return arch, dev, auditor


def _default_methodology_docs() -> tuple[str, str]:
    ru = """# Методология: Руководство для ARCH и DEV

Этот документ описывает рабочий метод для двух ключевых ролей:
- ARCH (архитектор)
- DEV (разработчик)

Ключевые правила:
1) Сначала контракт и критерии приемки, потом реализация.
2) Переходы статусов только по state_machine и role_policy.
3) Любое изменение фиксируется в TASK-*.json (sections + transitions).
4) Закрытие задачи в done только при полном evidence.

Цикл:
- ARCH: draft -> approved
- DEV: approved -> in_progress -> dev_done
- AUDITOR: dev_done -> qa_done (или возврат в in_progress)
- ARCH: qa_done -> arch_review -> done (или возврат в in_progress)

DoD минимум:
- assignment заполнен
- implementation/verification заполнены для соответствующего статуса
- evidence и acceptance_checks заполнены
- validate/workspace validate проходят без ошибок
"""

    en = """# Methodology: Guide for ARCH and DEV

This document defines the working method for two key roles:
- ARCH (architect)
- DEV (developer)

Core rules:
1) Contract and acceptance criteria first, implementation second.
2) Status transitions must follow state_machine and role_policy.
3) Every change is tracked in TASK-*.json (sections + transitions).
4) A task can be closed as done only with complete evidence.

Flow:
- ARCH: draft -> approved
- DEV: approved -> in_progress -> dev_done
- AUDITOR: dev_done -> qa_done (or return to in_progress)
- ARCH: qa_done -> arch_review -> done (or return to in_progress)

Minimum DoD:
- assignment completed
- implementation/verification completed for the current status
- evidence and acceptance_checks completed
- validate/workspace validate pass with no errors
"""

    return ru + "\n", en + "\n"


def _to_json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _write_file(path: Path, content: str, *, force: bool) -> InitAction:
    path.parent.mkdir(parents=True, exist_ok=True)
    existed_before = path.exists()
    if existed_before and not force:
        return InitAction(path=str(path), status="skipped")

    path.write_text(content, encoding="utf-8")
    status = "overwritten" if existed_before and force else "created"
    return InitAction(path=str(path), status=status)
