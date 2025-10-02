# Jira Release Notes Exporter

Скрипт для экспорта задач из Jira в JSON формат по fixVersion с группировкой по типам задач (improvements, bug fixes, epics) и списком всех компонентов.

📄 **[Посмотреть пример результата (example_output.json)](./example_output.json)**

## 📌 Важно: Две версии скрипта

### 🆕 **jira_export_v3.py** (Рекомендуется)
- Использует **Jira REST API v3** (`/rest/api/3/search`)
- Работает только с библиотекой `requests`
- Более простой и надежный
- **Используйте эту версию для новых проектов**

### 📦 **jira_export.py** (Устаревшая)
- Использует библиотеку `atlassian-python-api`
- Может иметь проблемы с новыми версиями Jira API
- Сохранена для обратной совместимости

## Установка

### Для jira_export_v3.py (API v3 - рекомендуется):
```bash
pip install requests
```

### Для jira_export.py (устаревшая версия):
```bash
pip install atlassian-python-api
```

## Настройка

Установите переменные окружения:

```bash
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_USERNAME="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

### Как получить API токен:
1. Зайдите в https://id.atlassian.com/manage-profile/security/api-tokens
2. Нажмите "Create API token"
3. Скопируйте токен

## Использование

### jira_export_v3.py (API v3 - рекомендуется):
```bash
# Базовое использование
python jira_export_v3.py PROJECT_KEY FIX_VERSION

# Пример
python jira_export_v3.py PROJ 1.0.0

# С указанием имени файла
python jira_export_v3.py PROJ 1.0.0 my_release_notes.json
```

### jira_export.py (устаревшая версия):
```bash
python jira_export.py PROJ 1.0.0
```

## Примеры

### Экспорт релиза v2.5.0 проекта DEV:
```bash
python jira_export_v3.py DEV 2.5.0
```

Результат будет сохранён в `release_notes_2_5_0.json`

### Пример вывода скрипта в консоли:
```
Searching for issues with JQL: project = PROJ AND fixVersion = "1.0.0" ORDER BY issuetype ASC, key ASC

Exported 8 issues to release_notes_1_0_0.json

============================================================
RELEASE NOTES SUMMARY
============================================================
Total issues: 8

IMPROVEMENTS:
  - PROJ-123 - Добавить новую функцию авторизации через OAuth2
  - PROJ-125 - Оптимизировать запросы к базе данных
  - PROJ-126 - Добавить темную тему в интерфейс
  - PROJ-127 - Настроить CI/CD pipeline для автоматического деплоя
  - PROJ-128 - Добавить unit тесты для модуля аутентификации
  - PROJ-129 - Обновить документацию API

BUG FIXES:
  - PROJ-124 - Исправить баг с отображением списка пользователей
  - PROJ-130 - Исправить проблему с кэшированием

COMPONENTS:
  - Backend
  - Database
  - DevOps
  - Documentation
  - Frontend
  - Security
  - Testing
  - UI/UX

============================================================
```

### Формат вывода JSON (release_notes_1_0_0.json):
```json
{
  "improvements": [
    "PROJ-123 - Добавить новую функцию авторизации через OAuth2",
    "PROJ-125 - Оптимизировать запросы к базе данных",
    "PROJ-126 - Добавить темную тему в интерфейс",
    "PROJ-127 - Настроить CI/CD pipeline для автоматического деплоя",
    "PROJ-128 - Добавить unit тесты для модуля аутентификации",
    "PROJ-129 - Обновить документацию API"
  ],
  "bug fixes": [
    "PROJ-124 - Исправить баг с отображением списка пользователей",
    "PROJ-130 - Исправить проблему с кэшированием"
  ],
  "components": [
    "Backend",
    "Database",
    "DevOps",
    "Documentation",
    "Frontend",
    "Security",
    "Testing",
    "UI/UX"
  ]
}
```

**Группировка по типам задач:**
- `improvements` - Story, Task, Improvement
- `bug fixes` - Bug
- `epics` - Epic
- Другие типы задач группируются по названию типа

**Примечание:** Компоненты собираются из всех задач и выводятся в отсортированном виде в поле `components`

## Дополнительные возможности

Если нужно добавить другие поля (assignee, status, description), отредактируйте строки:
- `fields='key,summary,components'` - добавьте нужные поля
- Секцию `issue_data` - добавьте извлечение нужных полей

## Troubleshooting

**Ошибка "Missing environment variables":**
- Проверьте, что все переменные окружения установлены

**Ошибка "atlassian-python-api not installed":**
- Установите библиотеку: `pip install atlassian-python-api`

**Ошибка авторизации:**
- Проверьте правильность API токена
- Убедитесь, что используете email в JIRA_USERNAME
