# Majordomus Universal Governance: majordomus

## 🛡️ Технический барьер
- **Pre-flight:** Всегда выполняйте `majordomus validate --path .` перед любым изменением кода.
- **Commit Guard:** Установите `.pre-commit-config.yaml` через `pre-commit install`.
- **Active Task:** Изменение кода запрещено без активной задачи в `.majordomus/tasks/`.

## 🚀 AI Agent Optimized Pipeline
Агентам разрешено использовать «Сжатый цикл» для экономии токенов:
- **DEV:** `APPROVED -> IN_PROGRESS -> DEV_DONE` (если работа завершена и `implementation` заполнена).
- **AUDITOR:** `DEV_DONE -> QA_DONE` (с доказательствами `evidence`).
- **ARCH:** `QA_DONE -> ARCH_REVIEW -> DONE` (при прохождении `acceptance_checks`).

Каждый переход обязан содержать время в UTC.

## 🛠️ DoD для Majordomus
Задача в статусе `done` должна иметь:
- `evidence`: ссылку на `pytest` отчет или лог `majordomus validate`.
- `verification`: список сценариев тестов, которые были запущены.
- `acceptance_checks`: все в статусе `pass`.

*Who guards the guardians? The protocol.*
