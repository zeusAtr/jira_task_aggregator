# 🔍 Find Custom Tags - Поиск кастомных тегов в продакшнах

## 🎯 Назначение

Скрипт для поиска кастомных тегов в файлах продакшнов (prod*.yml).

Сканирует директорию с конфигурационными файлами продакшнов и находит все строки с указанием `tag:`, выводя подробный отчет с названиями файлов и номерами строк.

## 📋 Формат файлов продакшнов

Скрипт работает с файлами формата `prodN.yml` или `prodN.yaml` (где N - любое число):

```yaml
# prod1.yml
service_name:
  cpu: 2
  memory: 4Gi
  tag: v1.2.3    # ← Скрипт найдет эту строку

another_service:
  cpu: 4
  memory: 8Gi
  tag: v2.0.0    # ← И эту тоже

service_without_tag:
  cpu: 1
  memory: 2Gi
```

## 🚀 Быстрый старт

### Базовое использование

```bash
# Сканировать текущую директорию
python find_custom_tags.py .

# Сканировать конкретную директорию
python find_custom_tags.py /path/to/production/configs
```

### Сохранение отчета

```bash
# Сохранить в текстовый файл
python find_custom_tags.py /path/to/configs -o report.txt

# Сохранить в CSV
python find_custom_tags.py /path/to/configs -o report.csv -f csv

# Сохранить в Markdown
python find_custom_tags.py /path/to/configs -o report.md -f md
```

## 📖 Примеры использования

### 1. Просто посмотреть, где есть теги

```bash
python find_custom_tags.py /path/to/prods
```

**Вывод:**
```
🔍 Сканирование директории: /path/to/prods
======================================================================

✓ Найдено файлов продакшнов: 4

======================================================================
📋 ОТЧЕТ: Найденные кастомные теги
======================================================================

──────────────────────────────────────────────────────────────────────
📄 Файл #1: prod1.yml
   Путь: /path/to/prods/prod1.yml
   Найдено тегов: 2
──────────────────────────────────────────────────────────────────────
   Строка    4: tag: v1.2.3
   Строка    9: tag: v2.0.1

──────────────────────────────────────────────────────────────────────
📄 Файл #2: prod3.yml
   Путь: /path/to/prods/prod3.yml
   Найдено тегов: 3
──────────────────────────────────────────────────────────────────────
   Строка    4: tag: v1.0.0-beta
   Строка    9: tag: latest
   Строка   14: tag: v2.5.1

======================================================================
📊 СТАТИСТИКА
======================================================================
   Всего файлов продакшнов: 4
   Файлов с кастомными тегами: 2
   Всего найдено тегов: 5
======================================================================
```

### 2. Краткий вывод (без номеров строк)

```bash
python find_custom_tags.py /path/to/prods --brief
```

**Вывод:**
```
📄 Файл #1: prod1.yml
   tag: v1.2.3
   tag: v2.0.1
```

### 3. Экспорт в CSV для анализа в Excel

```bash
python find_custom_tags.py /path/to/prods -o tags.csv -f csv
```

**Содержимое tags.csv:**
```csv
Файл,Путь,Номер строки,Тег
prod1.yml,/path/to/prods/prod1.yml,4,v1.2.3
prod1.yml,/path/to/prods/prod1.yml,9,v2.0.1
prod3.yml,/path/to/prods/prod3.yml,4,v1.0.0-beta
```

### 4. Экспорт в Markdown для документации

```bash
python find_custom_tags.py /path/to/prods -o tags_report.md -f md
```

**Содержимое tags_report.md:**
```markdown
# Отчет: Кастомные теги в файлах продакшнов

## Найденные теги

### 📄 prod1.yml

**Путь:** `/path/to/prods/prod1.yml`

**Найдено тегов:** 2

| Строка | Тег |
|--------|-----|
| 4 | `v1.2.3` |
| 9 | `v2.0.1` |
```

### 5. Тихий режим (только экспорт, без вывода на экран)

```bash
python find_custom_tags.py /path/to/prods -o report.txt -q
```

Полезно для автоматизации через cron или CI/CD.

## 🎛️ Параметры командной строки

```
позиционные аргументы:
  path                  Путь к директории с файлами продакшнов

опциональные аргументы:
  -h, --help            Показать справку
  -o OUTPUT, --output OUTPUT
                        Сохранить отчет в файл
  -f {txt,csv,md}, --format {txt,csv,md}
                        Формат выходного файла (по умолчанию: txt)
  -b, --brief           Краткий вывод без номеров строк
  -q, --quiet           Не выводить отчет на экран (только в файл)
```

## 📁 Структура директории

Скрипт ищет файлы в формате:
- `prod1.yml`, `prod2.yml`, `prod3.yml`, ...
- `prod10.yml`, `prod123.yml`, ...
- `prod1.yaml`, `prod2.yaml`, ... (также поддерживается)

**Примеры правильных имен:**
- ✅ `prod1.yml`
- ✅ `prod23.yml`
- ✅ `prod456.yaml`

**Примеры неправильных имен:**
- ❌ `production.yml` (нет номера)
- ❌ `prod.yml` (нет номера)
- ❌ `prod-1.yml` (дефис вместо числа)
- ❌ `config.yml` (неправильное имя)

## 🔍 Что ищет скрипт?

Скрипт находит строки в формате:
```yaml
  tag: значение
```

**Поддерживаются:**
- Любые отступы (пробелы)
- Любые значения тегов
- Комментарии после значения (игнорируются)

**Примеры:**
```yaml
service1:
  tag: v1.0.0              # ← Найдет
  tag: latest              # ← Найдет
  tag: v2.0.0-beta         # ← Найдет
  tag: sha-abc123          # ← Найдет
  tag: "v3.0.0"            # ← Найдет
  tag: 'v4.0.0'            # ← Найдет
```

## 📊 Форматы экспорта

### TXT (по умолчанию)
Простой текстовый формат для чтения человеком.

### CSV
Для импорта в Excel, Google Sheets или другие инструменты анализа.

**Структура:**
```csv
Файл,Путь,Номер строки,Тег
```

### Markdown
Для документации в README, Wiki, Confluence.

Содержит:
- Заголовки и подзаголовки
- Таблицы с тегами
- Статистику

## 🎯 Практические сценарии

### 1. Проверка версий перед деплоем

```bash
# Проверить, какие версии сейчас в продакшнах
python find_custom_tags.py /deployments/production -o current_versions.txt

# Сравнить с желаемыми версиями
```

### 2. Аудит версий

```bash
# Экспортировать все теги в CSV
python find_custom_tags.py /configs/prod -o audit_$(date +%Y%m%d).csv -f csv

# Отправить отчет команде
```

### 3. Документирование инфраструктуры

```bash
# Создать отчет в Markdown для документации
python find_custom_tags.py /infrastructure/prod -o infrastructure.md -f md

# Добавить в Wiki или Confluence
```

### 4. Автоматизация в CI/CD

```bash
#!/bin/bash
# check_prod_tags.sh

python find_custom_tags.py /prod-configs -o tags_report.txt

# Проверить, есть ли теги 'latest' (не рекомендуется в продакшне)
if grep -q "tag: latest" tags_report.txt; then
    echo "❌ Ошибка: Найден тег 'latest' в продакшне!"
    exit 1
fi

echo "✅ Все теги валидны"
```

### 5. Еженедельный отчет

```bash
#!/bin/bash
# weekly_tags_report.sh

REPORT_DATE=$(date +%Y-%m-%d)
REPORT_FILE="tags_report_${REPORT_DATE}.md"

python find_custom_tags.py /prod-configs -o "$REPORT_FILE" -f md -q

# Отправить отчет по email или в Slack
```

## 🔄 Интеграция с CI/CD

### GitLab CI

```yaml
check-prod-tags:
  stage: test
  script:
    - pip install -r requirements.txt
    - python find_custom_tags.py ./prod-configs -o tags_report.txt
    - cat tags_report.txt
  artifacts:
    paths:
      - tags_report.txt
    expire_in: 1 week
```

### GitHub Actions

```yaml
name: Check Production Tags

on:
  pull_request:
    paths:
      - 'prod-configs/**'

jobs:
  check-tags:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Check tags
        run: |
          python find_custom_tags.py ./prod-configs -o tags_report.md -f md
          cat tags_report.md
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: tags-report
          path: tags_report.md
```

## 🛠️ Требования

- Python 3.6+
- Стандартная библиотека Python (нет внешних зависимостей!)

## ⚙️ Установка

```bash
# Скачать скрипт
curl -O https://your-server/find_custom_tags.py

# Или скопировать локально
cp find_custom_tags.py /usr/local/bin/

# Сделать исполняемым
chmod +x find_custom_tags.py

# Использовать
find_custom_tags.py /path/to/configs
```

## 💡 Советы

1. **Используйте Markdown для документации** - удобно смотреть в GitLab/GitHub
   ```bash
   python find_custom_tags.py . -o TAGS.md -f md
   ```

2. **CSV для аналитики** - импортируйте в Excel/Google Sheets
   ```bash
   python find_custom_tags.py . -o tags.csv -f csv
   ```

3. **Автоматизируйте проверки** - добавьте в CI/CD pipeline

4. **Создавайте снимки** - сохраняйте отчеты с датой
   ```bash
   python find_custom_tags.py . -o "tags_$(date +%Y%m%d).txt"
   ```

5. **Используйте флаг --quiet** для автоматизации
   ```bash
   python find_custom_tags.py . -o report.txt -q
   ```

## 🐛 Решение проблем

### "Файлы не найдены"

```bash
# Проверьте, что файлы называются правильно
ls -la /path/to/configs/prod*.yml

# Убедитесь, что используете правильный путь
python find_custom_tags.py /correct/path/to/configs
```

### "Permission denied"

```bash
# Проверьте права доступа
ls -la /path/to/configs

# Добавьте права на чтение
chmod +r /path/to/configs/*.yml
```

### "No tags found"

Это нормально, если в ваших файлах действительно нет строк с `tag:`. Скрипт просто сообщит об этом.

## 📝 Примеры файлов продакшнов

### Пример 1: Простой файл

```yaml
# prod1.yml
web-service:
  cpu: 2
  memory: 4Gi
  tag: v1.2.3

api-service:
  cpu: 4
  memory: 8Gi
  tag: v2.0.1
```

### Пример 2: Без тегов

```yaml
# prod2.yml
database:
  cpu: 8
  memory: 32Gi

cache:
  cpu: 2
  memory: 4Gi
```

### Пример 3: Смешанный

```yaml
# prod3.yml
frontend:
  cpu: 2
  memory: 4Gi
  tag: v3.1.0

backend:
  cpu: 4
  memory: 8Gi
  # Нет тега - используется по умолчанию

monitoring:
  cpu: 1
  memory: 2Gi
  tag: latest
```

## 📄 Лицензия

MIT License
