# Методология: Руководство для ARCH и DEV

Этот документ описывает рабочий метод для двух ключевых ролей:
- **ARCH (архитектор)**
- **DEV (разработчик)**

Документ ориентирован на управление задачами через `majordomus` и профиль `trinity`.

## 1. Назначение ролей

### ARCH
Отвечает за:
- постановку задачи (цель, границы, ограничения, критерии приемки),
- архитектурные решения и контракты,
- разрешение переходов `draft -> approved`, `qa_done -> arch_review`, `arch_review -> done`,
- финальную приемку по evidence.

Не делает:
- реализацию за DEV,
- тестирование за AUDITOR.

### DEV
Отвечает за:
- реализацию в рамках `assignment.scope_in`,
- обновление `implementation` и переходов `approved -> in_progress -> dev_done`,
- сохранение детерминизма и обратной совместимости,
- прохождение проверок (lint/types/tests).

Не делает:
- изменение архитектуры вне scope,
- приемку за ARCH/AUDITOR.

## 2. Канонический цикл работы

1. ARCH формирует задачу в `TASK-XXXX.json`:
- `assignment.goal`
- `assignment.scope_in`
- `assignment.scope_out`
- `assignment.constraints`
- `acceptance_checks`

2. ARCH переводит задачу `draft -> approved`.

3. DEV берет задачу, переводит `approved -> in_progress`, реализует, заполняет `implementation`, переводит `in_progress -> dev_done`.

4. AUDITOR проводит проверку, заполняет `verification`, `evidence`, обновляет `acceptance_checks`, переводит `dev_done -> qa_done` (или возвращает в `in_progress`).

5. ARCH делает финальный review:
- `qa_done -> arch_review -> done`
- либо `arch_review -> in_progress` с причиной.

## 3. Структура артефактов

Обязательные файлы governance:
- `.majordomus/roles.yaml`
- `.majordomus/state_machine.yaml`
- `.majordomus/project.yaml`
- `.majordomus/policies/role_policy.json`
- `.majordomus/tasks/TASK-XXXX.json`

Поддерживающие артефакты:
- `.majordomus/templates/*.json`
- `.majordomus/docs/pipeline.json`
- `.majordomus/docs/prompts/*.system.md`

## 4. Метод ARCH: как формировать задачу

ARCH обязан зафиксировать в задаче:

1. **Цель** (одно измеримое изменение в системе).
2. **Scope in/out** (что входит и что явно не входит).
3. **Ограничения**:
- contract-first,
- детерминизм,
- без скрытых сайд-эффектов.
4. **Критерии приемки** (`acceptance_checks`), которые можно однозначно проверить.
5. **Ресурсы** (`assignment.resources`) со ссылками на нужные документы/шаблоны.

Правило ARCH:
- если критерий нельзя проверить, он не считается критерием готовности.

## 5. Метод DEV: как реализовывать

DEV выполняет работу только после `approved`.

Порядок:
1. Подтвердить, что задача в статусе `approved`.
2. Перевести в `in_progress` с transition note.
3. Реализовать только `scope_in`.
4. Заполнить `implementation`:
- `changed_files`
- `checks_run`
- `artifacts`
5. Перевести в `dev_done`.

Правило DEV:
- любое изменение вне scope должно быть отдельной задачей.

## 6. Определение готовности (Definition of Done)

Задача может быть закрыта в `done`, только если:

1. `assignment` заполнен полностью.
2. Для статусов выше `dev_done` заполнены `implementation` и `verification`.
3. Есть непустой `evidence`.
4. `acceptance_checks` имеют итоговые статусы.
5. Переходы роли соответствуют `state_machine.yaml`.
6. Права роли соответствуют `role_policy.json`.
7. Проект проходит валидацию:
```bash
majordomus --format json validate --path .
majordomus --format json workspace validate --workspace-file majordomus.workspace.yaml
```

## 7. Стандарт коммуникации в задаче

Каждый участник (ARCH/DEV/AUDITOR) в transition note пишет:
- что сделано,
- что проверено,
- что блокирует следующий этап (если есть).

Формат note:
- коротко,
- проверяемо,
- без общих фраз.

## 8. Антипаттерны (запрещено)

- Изменение несвязанных файлов "заодно".
- Переход статуса без фактического заполнения нужных секций.
- Отсутствие evidence при `qa_done`/`done`.
- Размытые критерии приемки (невозможно проверить).
- Обход role policy и state machine.

## 9. Быстрый чеклист ARCH

Перед `approved`:
- [ ] цель и границы ясны,
- [ ] ограничения заданы,
- [ ] критерии приемки проверяемы,
- [ ] ресурсы приложены.

Перед `done`:
- [ ] evidence достаточно,
- [ ] acceptance_checks закрыты,
- [ ] validate/workspace validate зелёные.

## 10. Быстрый чеклист DEV

Перед `dev_done`:
- [ ] изменены только нужные файлы,
- [ ] implementation заполнен,
- [ ] checks_run выполнены,
- [ ] transitions оформлены корректно.

## 11. Ключевой принцип

**Сначала контракт и статусная дисциплина, потом код.**

Если контракт, роль или переход не определены явно, работа считается неготовой к исполнению.
