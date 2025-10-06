# Jira Release Notes Exporter v3

Скрипт для экспорта release notes из Jira с автоматической группировкой сервисов по системам.

## Основные возможности

- ✅ Экспорт issues по fixVersion
- ✅ Группировка по Release announce type (customfield_11823)
- ✅ **Автоматическое разделение сервисов по группам:**
  - **GP** - все сервисы по умолчанию
  - **Jackpot system** - сервисы с префиксом `jackpot-*`
  - **SPE system** - сервисы с префиксом `spe-*`
- ✅ Полный список всех компонентов

## Установка

```bash
pip install requests
```

## Настройка environment variables

```bash
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_USERNAME="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

## Использование

```bash
# Базовое использование
python jira_export_v3.py PROJECT_KEY FIX_VERSION

# С указанием имени выходного файла
python jira_export_v3.py PROJECT_KEY FIX_VERSION output.json

# Примеры
python jira_export_v3.py PROJ 1.0.0
python jira_export_v3.py LIONS "2024.10.15" release_notes_oct.json
```

## Структура выходного файла

```json
{
  "New Feature": [
    "PROJ-123 - Add new authentication flow",
    "PROJ-124 - Implement jackpot bonus system"
  ],
  "Bug Fix": [
    "PROJ-125 - Fix SPE calculation error"
  ],
  "services": {
    "GP": [
      "api-gateway",
      "auth-service",
      "user-service"
    ],
    "Jackpot system": [
      "jackpot-api",
      "jackpot-calculator"
    ],
    "SPE system": [
      "spe-calculator",
      "spe-processor"
    ]
  },
  "all_components": [
    "api-gateway",
    "auth-service",
    "jackpot-api",
    "jackpot-calculator",
    "spe-calculator",
    "spe-processor",
    "user-service"
  ]
}
```

## Логика группировки сервисов

Скрипт автоматически анализирует имена компонентов и группирует их:

- **jackpot-api**, **jackpot-calculator** → Jackpot system
- **spe-calculator**, **spe-processor** → SPE system
- **api-gateway**, **user-service** → GP (по умолчанию)

## Пример вывода в консоли

```
Searching for issues with JQL: project = PROJ AND fixVersion = "1.0.0" ORDER BY key ASC
Using API endpoint: https://your-domain.atlassian.net/rest/api/3/search/jql
Found 15 issues (Total: 15)

Exported 15 issues to release_notes_1_0_0.json

============================================================
RELEASE NOTES SUMMARY (Grouped by Release announce type)
============================================================
Total issues: 15

NEW FEATURE:
  - PROJ-123 - Add new authentication flow
  - PROJ-124 - Implement jackpot bonus system

BUG FIX:
  - PROJ-125 - Fix SPE calculation error
  - PROJ-126 - Resolve payment gateway timeout

SERVICE GROUPS:

  GP:
    - api-gateway
    - auth-service
    - user-service

  Jackpot system:
    - jackpot-api
    - jackpot-calculator

  SPE system:
    - spe-calculator
    - spe-processor

ALL COMPONENTS:
  - api-gateway
  - auth-service
  - jackpot-api
  - jackpot-calculator
  - spe-calculator
  - spe-processor
  - user-service

============================================================
```

## Добавление новых групп сервисов

Чтобы добавить новую группу, отредактируйте функцию `get_service_group()`:

```python
def get_service_group(component_name: str) -> str:
    if component_name.startswith('jackpot-'):
        return 'Jackpot system'
    elif component_name.startswith('spe-'):
        return 'SPE system'
    elif component_name.startswith('new-prefix-'):  # Новая группа
        return 'New System'
    else:
        return 'GP'
```

И добавьте новую группу в словарь `service_groups`:

```python
service_groups = {
    'GP': set(),
    'Jackpot system': set(),
    'SPE system': set(),
    'New System': set()  # Новая группа
}
```

## Troubleshooting

### Ошибка "Missing environment variables"
Проверьте, что все три переменные окружения установлены:
```bash
echo $JIRA_URL
echo $JIRA_USERNAME
echo $JIRA_API_TOKEN
```

### HTTP Error 401
Проверьте правильность API token. Создать новый можно здесь:
https://id.atlassian.com/manage-profile/security/api-tokens

### Пустой список issues
Проверьте:
- Существует ли указанный fixVersion в проекте
- Есть ли у вас права на просмотр issues в проекте
- Правильно ли указан PROJECT_KEY (должен быть в uppercase)
