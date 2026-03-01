### 1) Read docs first
- `AGENTS.md`
- `METODS.md`
- `METODS_ARCH_DEV.ru.md`
- `METODS_ARCH_DEV.en.md`

### 2) Who r u
Ты — инженер-исполнитель. Твоя задача: полностью реализовать Major Domus v1 (Multi-Project Governance Orchestrator) как Python пакет в src-layout, строго по требованиям.

ОБЩИЕ ПРАВИЛА (обязательные):
1) Никакого shared state между проектами. Каждый проект валидируется изолированно.
2) Workspace mode — только оркестрация: он не меняет project-level логику.
3) Только файловая система. Никаких сетей, БД, глобальных кешей.
4) Детерминизм обязателен: одинаковый результат при каждом запуске (порядок проектов, файлов, ошибок).
5) Ошибки не должны “ронять” процесс: они собираются как Issue и входят в Report.
6) Любое нарушение правил в validate → exit code != 0.
7) v1 НЕ содержит cross-project dependency logic. Никаких графов зависимостей. Только задел через plugin hooks.

### 3) Project
ЦЕЛЬ:
Реализовать CLI и ядро:
- Project mode: majordomus validate
- Workspace mode: majordomus workspace validate/status/audit
- Вывод: human и json (--format), exit codes: 0/2/3/4.
- Workspace config: majordomus.workspace.yaml (schema v1).
- Проектная governance директория: .majordomus/ с roles.yaml, state_machine.yaml, tasks/*.json, project.yaml (optional).
- Централизованная валидация: единый Validator pipeline и встроенные JSON schemas.

СТРУКТУРА РЕПОЗИТОРИЯ (src-layout, не отклоняться):
major-domus/
  pyproject.toml
  README.md
  src/
    majordomus/
      core/
        workspace_engine.py
        project_engine.py
        (доп: schema_loader.py допустимо)
        domain/
        governance/
        ports/
        adapters/
        plugins/
        util/
        exceptions.py
      cli/
        main.py
        workspace_cmd.py
        project_cmd.py
        render.py
      schemas/
        task_schema_v1.json
        workspace_schema_v1.json
        roles_schema_v1.json
        state_machine_schema_v1.json
  tests/
    unit/
    integration/
    fixtures/

КОНТРАКТЫ (обязательные DTO/Enums):
- Issue(code, severity(ERROR|WARN), message, location{path,line,col?}, project?, task_id?, data?)
- ProjectReport(project, status(PASS|FAIL|SKIP), issues[], stats{tasks,errors,warns,time_ms})
- WorkspaceReport(workspace, mode(validate|status|audit), ordering(by_name|as_listed), project_reports[], issues[], summary, exit_code)
- MissingGovernancePolicy: fail|skip

SCHEMAS (обязательны):
- workspace_schema_v1.json: workspace_name, defaults, projects[name,path,governance_dir?,missing_governance?]
- roles_schema_v1.json: version=1, roles[{id,name}]
- state_machine_schema_v1.json: version=1, states[], initial_state, transitions[{from,to,allowed_roles[]}]
- task_schema_v1.json: schema_version=1, id TASK-0001..., title, status, owner_role?, transitions[{at,from,to,role,note?}] etc.

СЕМАНТИЧЕСКАЯ ВАЛИДАЦИЯ (поверх JSON schema):
- project path not found → FAIL проекта, но workspace продолжает.
- governance missing → SKIP/FAIL по policy.
- roles ids unique.
- transitions unique by (from,to).
- initial_state в states.
- task filename stem == task.id.
- task.status в states.
- owner_role и transition.role должны существовать в roles.
- transition.from/to должны быть валидными states.
- updated_at >= created_at (если оба есть).
- Issues сортируются детерминированно: severity, code, project, location.path, task_id, message.

ПРОИЗВОДИТЕЛЬНОСТЬ:
- Никакого сканирования всего repo. Только governance_root и tasks_dir (glob *.json, не рекурсивно).

PLUGIN SYSTEM v1:
- PluginHost + BasePlugin hooks:
  - on_workspace_loaded(workspace_config)
  - on_project_context_created(project_ctx)
  - on_project_validated(project_report)
- По умолчанию plugins=[]; hooks должны работать, но логика плагинов в v1 минимальна.

CLI:
- majordomus workspace validate|status|audit [--format human|json]
- majordomus validate (project mode) [--format human|json]
- exit codes: 0 ok, 2 validation fail, 3 CLI usage error, 4 internal error.

ДЕТЕРМИНИЗМ:
- проекты: ordering policy by_name/as_listed
- task files: lexicographic by path
- issues: deterministic sorting key (см. выше)
- отчёт и вывод должны быть стабильны.

ТЕСТЫ (обязательны):
Unit:
- sort_issues ordering
- safe_join prevents escaping
- StateMachine invariants (initial_state, duplicate transition)
Integration (fixtures):
- workspace all pass → exit 0
- workspace one fail → exit 2, другие валидируются
- missing governance skip → SKIP + WARN
- invalid workspace yaml/schema → exit 2
- project broken task json → TASK100

ФИКСТУРЫ:
Создай tests/fixtures с минимум 3 workspace сценариями.

ПОРЯДОК РЕАЛИЗАЦИИ (не нарушать):
1) DTO/enums/util
2) schemas + schema loader + validator adapter
3) task registry + state machine + roles
4) project engine
5) workspace engine
6) CLI + render
7) fixtures + tests
8) README

КРИТЕРИИ ГОТОВНОСТИ:
- `pip install -e .` работает
- `majordomus workspace validate` работает на фикстурах
- pytest проходит
- deterministic output подтверждён golden test (JSON предпочтительнее)

СДЕЛАЙ:
- Реализуй весь код.
- Добавь schemas как реальные файлы.
- Добавь фикстуры и тесты.
- Добавь README с примерами.
- Убедись, что всё соответствует ограничениям v1.

### 4) PR Definition of Done (DoD):
PR Definition of Done (DoD) — Major Domus v1
A) Архитектурные границы и зависимости

 Src-layout соблюдён: весь код в src/majordomus, тесты в tests/.

 CLI = composition root: создание адаптеров/инжект зависимостей происходит только в majordomus/cli/* (или одном wiring-модуле).

 CLI не импортирует напрямую majordomus.core.governance.* (кроме случаев, специально оговорённых контрактом команд).
Разрешено: core.workspace_engine, core.project_engine, cli.render.

 Workspace layer не содержит project-level логики: WorkspaceEngine не знает деталей state machine / ролей / задач.

 Нет циклических импортов между слоями (domain, core, governance, ports, adapters, cli).

 Нет “скрытых” side effects при импорте модулей (никакого чтения FS/схем/конфигов на import-time).

 Нет глобального состояния (singletons, module-level cache, mutable globals) влияющего на разные проекты.

B) Изоляция проектов (Isolation Guarantees)

 Проверка каждого проекта использует только project_root/.majordomus (или override governance_dir).
Никаких чтений соседних проектов или workspace-root, кроме majordomus.workspace.yaml.

 Ошибки одного проекта не ломают обработку остальных: WorkspaceEngine продолжает итерацию.

 Любой shared ресурс (schema loader, validator adapter) — stateless и не хранит данных проекта между вызовами.

C) Детерминизм (Deterministic Ordering)

 Порядок проектов детерминирован:

by_name — сортировка по name

as_listed — как в yaml

 Порядок task-файлов детерминирован: лексикографическая сортировка путей.

 Порядок issues детерминирован:
severity(ERROR before WARN) → code → project → location.path → task_id → message.

 JSON output стабилен (одинаковый порядок массивов projects[] и issues[]).

 Есть golden test на JSON output (или нормализованный human), подтверждающий стабильность.

D) Валидация и ошибки

 Все ошибки преобразуются в Issue и входят в ProjectReport/WorkspaceReport, а не “падают” исключениями.

 Исключения разрешены только как internal errors, и тогда:

превращаются в exit_code=4 на уровне CLI

содержат понятное сообщение (без trace в stdout по умолчанию)

 Workspace schema валидируется (минимум):

parse YAML errors → WS001

schema/semantic errors (например, duplicate names) → WS002/WS010

 Project-level ошибки покрыты:

project path missing → PRJ001

governance missing → PRJ010 (SKIP/FAIL по policy)

broken task json → TASK100

schema failed → TASK101

filename != task.id → TASK001

unknown status/state → TASK200/PRJ202

unknown role → PRJ203

E) Производительность (v1 expectations)

 Нет полного сканирования репозитория: поиск задач ограничен governance_root/tasks_dir/*.json (без recursive).

 workspace status выполняет быстрый путь (без глубокой проверки task schema) или чётко описано, если в v1 он эквивалентен validate.

 Нет git вызовов, нет сетевых вызовов.

F) CLI контракт

 majordomus установлен как entrypoint через pyproject.toml ([project.scripts]).

 Команды:

majordomus workspace validate|status|audit

majordomus validate (project mode)

 Флаг --format human|json работает везде.

 Exit codes соблюдены:

0 — success (нет FAIL и нет ERROR)

2 — validation fail (есть FAIL или ERROR)

3 — cli usage error

4 — internal error

G) Пакетирование и ресурсы

 Schemas лежат в src/majordomus/schemas/*.json и включены в package-data.

 Schemas загружаются через importlib.resources (не через относительные пути от cwd).

 pip install -e . работает, затем majordomus --help работает.

H) Тесты

 Unit тесты:

sort_issues

safe_join (escape prevention)

state machine invariants (initial_state, duplicate transitions)

 Integration тесты на fixtures:

workspace all pass → exit 0

workspace one fail → exit 2 + продолжение остальных

missing governance skip → SKIP + WARN

invalid workspace yaml/schema → exit 2

project broken json → TASK100

 Тесты не зависят от локального окружения (cwd, OS-specific path separators) — нормализуются.

I) Документация

 README содержит:

установку (pip install -e .)

пример majordomus.workspace.yaml

описание .majordomus/ структуры

примеры команд validate/status

exit codes

 В README явно написано: v1 без cross-project dependency rules (v2).

  ruff format не меняет файлы (код уже отформатирован)

 ruff check без ошибок

 mypy src проходит

 pytest проходит

### 5) Machine-Readable Execution Plan

Plan file: [execution_plan.yaml](execution_plan.yaml)

### 6) Dev Toolchain Baseline

- Dev extras:
  - `pytest>=7.4`
  - `ruff>=0.5`
  - `mypy>=1.8`
  - `types-PyYAML`
- Development install:
  - `pip install -e ".[dev]"`
- CI minimum commands:
  - `ruff format .`
  - `ruff check .`
  - `mypy src`
  - `pytest`
- Source of truth for tool settings:
  - `pyproject.toml` sections:
    - `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.ruff.lint.isort]`, `[tool.ruff.format]`
    - `[tool.mypy]`
    - `[tool.pytest.ini_options]`
