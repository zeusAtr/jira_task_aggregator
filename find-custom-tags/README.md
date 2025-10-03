# 🔍 Custom Tags Scanner

Скрипт для поиска кастомных тегов в YAML файлах конфигураций.

## 📋 Описание

Сканирует все `.yml` и `.yaml` файлы в указанной директории и находит кастомные теги Docker-образов (feature/, hotfix/, release/, и т.д.), исключая стандартные версионные теги и хеши коммитов.

## ✨ Особенности

- ✅ Обрабатывает **все** .yml и .yaml файлы в директории
- ✅ Поддерживает файлы с любыми именами (prod1.yml, prodsg1.yml, docker-compose.yml, и т.д.)
- ✅ Группирует результаты по файлам
- ✅ Показывает статистику обработанных файлов
- ✅ Фильтрует кастомные теги (с префиксами feature/, hotfix/, release/, и т.д.)
- ✅ Исключает сервисы с суффиксом `-limited`
- ✅ Экспорт в форматы: TXT, CSV, Markdown

## 🎯 Что считается кастомным тегом

### Включается в отчет:
- `feature/new-feature`
- `hotfix/critical-fix`
- `bugfix/login-issue`
- `release/v2.0-rc1`
- `develop/experimental`
- Любой тег содержащий `/` (слеш)

### Исключается из отчета:
- `1.0.0` (версионные теги)
- `v1.2.3` (версионные теги с префиксом v)
- `1.0.0-alpha` (версионные теги с суффиксом)
- `4fe602bc` (хеши коммитов, 7-40 символов hex)
- `latest` (стандартные теги)
- `stable` (стандартные теги)
- `production` (стандартные теги)

## 🚫 Фильтрация сервисов

Сервисы с суффиксом `-limited` **полностью исключаются** из отчета:
- ❌ `api-service-limited`
- ❌ `worker-limited`
- ❌ `backend-limited`

## 📦 Требования

- Python 3.6+
- Стандартные библиотеки (re, argparse, pathlib)

## 🚀 Использование

### Базовое использование

```bash
# Сканировать текущую директорию
./find_custom_tags_grouped.py .

# Сканировать конкретную директорию
./find_custom_tags_grouped.py /path/to/configs
```

### Экспорт в файл

```bash
# Экспорт в текстовый формат
./find_custom_tags_grouped.py /path/to/configs -o report.txt

# Экспорт в CSV
./find_custom_tags_grouped.py /path/to/configs -o report.csv -f csv

# Экспорт в Markdown
./find_custom_tags_grouped.py /path/to/configs -o report.md -f md
```

### Дополнительные опции

```bash
# Только сохранить в файл, без вывода на экран
./find_custom_tags_grouped.py /path/to/configs -o report.txt -q
```

## 📊 Формат вывода

### Консольный вывод (текст)

```
path: prod1
  service: api-service
  tag: feature/new-api
  service: web-service
  tag: hotfix/login-fix

path: prodsg1
  service: backend
  tag: release/v2.0-rc

Статистика:
  Обработано файлов: 5
  Файлов с кастомными тегами: 2
  Всего найдено кастомных тегов: 3
```

### CSV формат

```csv
path,service,tag
prod1,api-service,feature/new-api
prod1,web-service,hotfix/login-fix
prodsg1,backend,release/v2.0-rc
```

### Markdown формат

```markdown
# Кастомные теги

## prod1

| Service | Tag |
|---------|-----|
| `api-service` | `feature/new-api` |
| `web-service` | `hotfix/login-fix` |

## prodsg1

| Service | Tag |
|---------|-----|
| `backend` | `release/v2.0-rc` |

## Статистика

- **Обработано файлов:** 5
- **Файлов с кастомными тегами:** 2
- **Всего найдено кастомных тегов:** 3
```

## 🔧 Параметры командной строки

| Параметр | Описание |
|----------|----------|
| `path` | Путь к директории с yml/yaml файлами (обязательный) |
| `-o, --output` | Сохранить отчет в файл |
| `-f, --format` | Формат выходного файла: txt, csv, md (по умолчанию: txt) |
| `-q, --quiet` | Не выводить отчет на экран (только в файл) |
| `-h, --help` | Показать справку |

## 💡 Примеры использования

### Пример 1: Быстрая проверка
```bash
./find_custom_tags_grouped.py /srv/deployments
```

### Пример 2: Генерация отчета для команды
```bash
./find_custom_tags_grouped.py /srv/deployments -o custom_tags_report.md -f md
```

### Пример 3: Экспорт для обработки в Excel
```bash
./find_custom_tags_grouped.py /srv/deployments -o tags.csv -f csv
```

### Пример 4: Автоматизация в CI/CD
```bash
./find_custom_tags_grouped.py /srv/deployments -o report.txt -q
if [ $? -eq 0 ]; then
    echo "Отчет создан успешно"
    cat report.txt
fi
```

## 📝 Структура YAML файлов

Скрипт работает с различными форматами определения сервисов:

### Формат 1: Docker Compose
```yaml
services:
  api-service:
    image: registry.example.com/api
    tag: feature/new-endpoint
```

### Формат 2: Kubernetes-style
```yaml
- name: web-service
  image: registry.example.com/web
  tag: hotfix/security-patch
```

### Формат 3: Custom format
```yaml
my-service:
  container:
    image: registry.example.com/app
    tag: release/v1.5-candidate
```

## 🐛 Известные ограничения

1. Скрипт предполагает, что имя сервиса определяется перед тегом в файле
2. Вложенность YAML структур ограничена (глубина отступа <= 4 пробела для определения сервиса)
3. Не обрабатывает закомментированные строки

## 📄 Лицензия

Free to use and modify

## 👤 Автор

Created for infrastructure automation and monitoring
