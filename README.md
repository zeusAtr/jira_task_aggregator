# Jira Release Notes Exporter (Updated)

Скрипт для экспорта задач из Jira в JSON формат по fixVersion с **группировкой по Release announce type** (customfield_11823) и списком всех компонентов.

📄 **[Посмотреть пример результата (example_output.json)](./example_output.json)**

## 🎯 Особенности

- ✅ Группировка по **Release announce type**
- ✅ Использует **Jira REST API v3** (`/rest/api/3/search/jql`)
- ✅ Работает только с библиотекой `requests`
- ✅ Экспорт списка всех компонентов

## Установка

```bash
pip install requests
```

## Настройка

Установите переменные окружения:

### Linux / macOS:
```bash
export JIRA_URL=".."
export JIRA_USERNAME="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

### Windows (PowerShell):
```powershell
$env:JIRA_URL="url"
$env:JIRA_USERNAME="your-email@example.com"
$env:JIRA_API_TOKEN="your-api-token"
```

### Как получить API токен:
1. Зайдите в https://id.atlassian.com/manage-profile/security/api-tokens
2. Нажмите **"Create API token"**
3. Скопируйте токен

## Использование

```bash
# Базовое использование
python jira_export_v3_fixed.py PROJECT_KEY FIX_VERSION

# Пример
python jira_export_v3_fixed.py PP 43.68.5

# С указанием имени файла
python jira_export_v3_fixed.py PP 43.68.5 my_release_notes.json
```

## Примеры

### Экспорт релиза 43.68.5 проекта PP:
```bash
python jira_export_v3_fixed.py PP 43.68.5
```

Результат будет сохранён в `release_notes_43_68_5.json`

### Пример вывода скрипта в консоли:
```
Searching for issues with JQL: project = PP AND fixVersion = "43.68.5" ORDER BY key ASC
Using API endpoint: ..
Found 12 issues (Total: 12)

Exported 12 issues to release_notes_43_68_5.json

============================================================
RELEASE NOTES SUMMARY (Grouped by Release announce type)
============================================================
Total issues: 12

NEW FEATURE:
  - PP-123 - Добавить новую функцию авторизации через OAuth2
  - PP-126 - Добавить темную тему в интерфейс
  - PP-127 - Настроить CI/CD pipeline для автоматического деплоя

BUG FIX:
  - PP-124 - Исправить баг с отображением списка пользователей
  - PP-130 - Исправить проблему с кэшированием

IMPROVEMENT:
  - PP-125 - Оптимизировать запросы к базе данных
  - PP-128 - Добавить unit тесты для модуля аутентификации

DOCUMENTATION:
  - PP-129 - Обновить документацию API

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

### Формат вывода JSON (release_notes_43_68_5.json):
```json
{
  "New Feature": [
    "PP-123 - Добавить новую функцию авторизации через OAuth2",
    "PP-126 - Добавить темную тему в интерфейс",
    "PP-127 - Настроить CI/CD pipeline для автоматического деплоя"
  ],
  "Bug Fix": [
    "PP-124 - Исправить баг с отображением списка пользователей",
    "PP-130 - Исправить проблему с кэшированием"
  ],
  "Improvement": [
    "PP-125 - Оптимизировать запросы к базе данных",
    "PP-128 - Добавить unit тесты для модуля аутентификации"
  ],
  "Documentation": [
    "PP-129 - Обновить документацию API"
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

## 📋 Группировка

Задачи группируются по значению поля **Release announce type** (customfield_11823):
- Каждое значение поля становится отдельной группой
- Если у задачи нет значения в этом поле, она попадает в группу "No announce type"
- Компоненты собираются из всех задач и выводятся отдельным списком

## 🔧 Дополнительные скрипты

### find_custom_field.py
Помогает найти ID кастомного поля:
```bash
python find_custom_field.py PP 43.68.5
```

### test_jql_queries.py  
Тестирует разные варианты JQL запросов:
```bash
python test_jql_queries.py
```

### jira_debug_full.py
Полная диагностика подключения и поиска:
```bash
python jira_debug_full.py
```

## Troubleshooting

**Ошибка "Missing environment variables":**
- Проверьте, что все переменные окружения установлены

**Ошибка "No issues found":**
- Проверьте правильность названия версии
- Убедитесь, что версия назначена как Fix Version в задачах
- Попробуйте test_jql_queries.py для диагностики

**Ошибка авторизации:**
- Проверьте правильность API токена
- Убедитесь, что используете email в JIRA_USERNAME

**Задачи без Release announce type:**
- Проверьте, что поле заполнено в задачах
- Такие задачи попадут в группу "No announce type"
