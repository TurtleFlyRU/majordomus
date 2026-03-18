# 📜 THE MAJORDOMUS BIBLE (Trinity v3 Mandate)

Этот файл является ВЫСШИМ ЗАКОНОМ для работы над проектом Majordomus.

---

## 🏛️ 1. ГЛАВНЫЕ ЗАПОВЕДИ (Core Mandates)

1.  **Dogfooding**: Мы используем `majordomus` для управления `majordomus`. Никаких изменений в `src/` без активной задачи в `.majordomus/tasks/`.
2.  **Contract First**: Изменения в логике валидации начинаются с обновления схем в `src/majordomus/schemas/`.
3.  **Strict Transitions**: Только полные и валидные переходы статусов.
4.  **Zero-Error Validation**: Перед любым коммитом `majordomus validate --path .` должен возвращать `PASS`.

---

## 🎭 2. РОЛИ (Trinity Roles)

- **🏗️ ARCH**: Управляет схемами (`schemas/`), логикой переходов и ADR.
- **💻 DEV**: Реализует CLI, core-движок и адаптеры.
- **🧪 AUDITOR**: Пишет тесты в `tests/`, проверяет корректность кодов ошибок.

---

## 🛠️ 3. КРИТИЧЕСКИЕ ТОЧКИ (Hooks)

**Перед началом работы:**
1. Выполни `pip install -e .`, чтобы использовать текущую версию CLI.
2. Выполни `majordomus validate --path .`.
3. Убедись, что задача в статусе `APPROVED` или `IN_PROGRESS`.

**После изменений:**
1. Обнови `TASK-*.json` (changed_files, checks_run).
2. Запусти тесты: `pytest`.
3. Убедись, что валидация `PASS`.

---

## 🚀 AI ЭФФЕКТИВНОСТЬ
Разрешено объединять переходы: `APPROVED -> IN_PROGRESS -> DEV_DONE` в один ход при условии полной реализации и прохождения тестов.

*Majordomus: Who guards the guardians? We do.*
