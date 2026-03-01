# План полной реализации (v1)

## Фаза 0 — Baseline и правила

- Создать репозиторий со src-layout:
  - `pyproject.toml`, `README.md`, `src/majordomus/...`, `tests/...`
- Зафиксировать инженерные правила:
  - No shared state между проектами
  - No network, no DB, только FS
  - Deterministic ordering: projects/files/issues
  - Ошибки не кидают наружу, возвращаются как Issue/Report
  - Любая ошибка в проекте не ломает workspace обход
- Deliverable: проект ставится `pip install -e .`, CLI entrypoint работает (`majordomus --help`).

## Фаза 1 — Контракты и доменные типы

- Реализовать `domain/enums.py`, `domain/types.py` (Issue/Report/Config DTO)
- Реализовать сортировку issues и общие утилиты (`util/sorting.py`, `util/paths.py`, `util/parsing.py`)
- Определить каталог error codes (WS/PRJ/TASK) как константы или строками (v1 допускает строки, но тесты должны ожидать их)
- Deliverable: unit-тесты на `sort_issues`, `safe_join`, базовые DTO.

## Фаза 2 — Schemas и schema loader

- Положить built-in JSON schemas в `src/majordomus/schemas/`:
  - `workspace_schema_v1.json`
  - `task_schema_v1.json`
  - `roles_schema_v1.json`
  - `state_machine_schema_v1.json`
- Реализовать loader через `importlib.resources` (без зависимости от cwd)
- Реализовать адаптер `JsonschemaValidatorAdapter` и порт `JsonSchemaValidatorPort`
- Deliverable: unit-тест: schemas грузятся, валидатор выдаёт issues на намеренно неверных данных.

## Фаза 3 — FS порт и adapters

- Реализовать `FileSystemPort` + `LocalFileSystemAdapter`
- Обеспечить, что `glob()` не рекурсивный и используется только внутри `governance_root/tasks_dir`
- Везде использовать `Path` и нормализацию
- Deliverable: unit-тест на `TaskRegistry.list_task_files()` deterministic order.

## Фаза 4 — Project Governance Engine (локально)

- Реализовать:
  - `RoleEngine`
  - `StateMachine`
  - `TaskRegistry`
  - `Validator` (schema + semantic checks v1)
- Реализовать `ProjectEngine.run(ctx, missing_policy, mode, extra_issues)`
  - missing governance -> SKIP/FAIL
  - `roles.yaml` / `state_machine.yaml` required
  - `project.yaml` optional
  - `mode=STATUS`: быстрый путь (без полной валидации задач)
  - `mode=VALIDATE`: полная проверка задач
- Детерминизм:
  - сортировка файлов
  - сортировка issues
- Deliverable: unit-тесты на state machine invariants, roles invariants; integration тест project-level на broken task json.

## Фаза 5 — Workspace Orchestrator

- Реализовать `WorkspaceEngine.load_workspace()`:
  - parse yaml
  - schema validate (`workspace_schema`)
  - uniqueness project names
  - defaults + overrides
- Реализовать `WorkspaceEngine.validate(ws_yaml_path, mode)`:
  - deterministic ordering проектов
  - iterating по проектам без остановки
  - aggregation summary + exit_code
- Implement plugin host hooks v1 (пустые плагины — но готовность)
- Deliverable: integration тесты:
  - all pass -> exit 0
  - one project fails -> exit 2 + остальные не ломаются
  - missing governance skip -> SKIP + warn
  - invalid workspace yaml/schema -> exit 2 без project обхода

## Фаза 6 — CLI

- Разнести команды:
  - `cli/main.py` — argparsing + routing
  - `cli/workspace_cmd.py` — workspace validate/status/audit
  - `cli/project_cmd.py` — validate (project mode), task show/transition (минимально)
  - `cli/render.py` — human output (deterministic), JSON output
- Контракты вывода:
  - `--format human|json`
  - exit codes: 0 ok; 2 validation fail; 3 cli usage; 4 internal error
- Deliverable: e2e тест через subprocess (опционально), либо integration test напрямую вызывая engines.

## Фаза 7 — Fixtures + Golden tests

- Добавить `tests/fixtures/*` workspace деревья
- “Golden” test: сравнение JSON output (или нормализованного human output) для детерминизма
- Deliverable: стабильные тесты, одинаковый вывод на каждом запуске.

## Фаза 8 — Документация и hardening

- README: install/run/examples/exit codes
- Уточнить edge cases:
  - project path отсутствует
  - governance missing
  - broken task json
  - file name != id
- Убедиться в отсутствии сканирования всего repo: только `.majordomus/` + `tasks_dir`
- Deliverable: v1 релиз 0.1.0.
