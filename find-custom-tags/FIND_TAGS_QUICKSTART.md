# 🔍 Find Custom Tags - Быстрый старт

## ⚡ За 30 секунд

```bash
# 1. Запустите скрипт (указав путь к директории с prod*.yml файлами)
python find_custom_tags.py /path/to/your/production/configs

# 2. Готово! Увидите отчет на экране
```

---

## 🎯 Что делает скрипт?

Ищет все строки с `tag:` в файлах `prod*.yml` и показывает:
- ✅ В каком файле найден тег
- ✅ На какой строке
- ✅ Какое значение тега
- ✅ Статистику по всем файлам

---

## 📋 Примеры команд

### Базовое использование
```bash
# Текущая директория
python find_custom_tags.py .

# Конкретная директория
python find_custom_tags.py /prod-configs
```

### Сохранить отчет
```bash
# Текстовый файл
python find_custom_tags.py /prod-configs -o report.txt

# CSV для Excel
python find_custom_tags.py /prod-configs -o report.csv -f csv

# Markdown для документации
python find_custom_tags.py /prod-configs -o report.md -f md
```

### Дополнительные опции
```bash
# Краткий вывод (без номеров строк)
python find_custom_tags.py /prod-configs --brief

# Тихий режим (только файл, без экрана)
python find_custom_tags.py /prod-configs -o report.txt -q

# Справка
python find_custom_tags.py --help
```

---

## 📁 Какие файлы сканирует?

Скрипт ищет файлы формата:
- `prod1.yml`, `prod2.yml`, `prod3.yml`, ...
- `prod10.yml`, `prod123.yml`, ...
- `prod1.yaml`, `prod2.yaml`, ...

---

## 💡 Примеры файлов

### prod1.yml (с тегами)
```yaml
auth-service:
  cpu: 2
  memory: 4Gi
  tag: v1.2.3    # ← Скрипт найдет

payment-service:
  cpu: 4
  memory: 8Gi
  tag: v2.0.1    # ← Скрипт найдет
```

### prod2.yml (без тегов)
```yaml
database:
  cpu: 8
  memory: 32Gi

cache:
  cpu: 2
  memory: 4Gi
```

---

## 📊 Пример вывода

```
🔍 Сканирование директории: /prod-configs
======================================================================

✓ Найдено файлов продакшнов: 4

======================================================================
📋 ОТЧЕТ: Найденные кастомные теги
======================================================================

──────────────────────────────────────────────────────────────────────
📄 Файл #1: prod1.yml
   Путь: /prod-configs/prod1.yml
   Найдено тегов: 2
──────────────────────────────────────────────────────────────────────
   Строка    4: tag: v1.2.3
   Строка    9: tag: v2.0.1

──────────────────────────────────────────────────────────────────────
📄 Файл #2: prod3.yml
   Путь: /prod-configs/prod3.yml
   Найдено тегов: 1
──────────────────────────────────────────────────────────────────────
   Строка    8: tag: v3.1.0

======================================================================
📊 СТАТИСТИКА
======================================================================
   Всего файлов продакшнов: 4
   Файлов с кастомными тегами: 2
   Всего найдено тегов: 3
======================================================================
```

---

## 🎭 Практические примеры

### 1. Проверка версий перед деплоем
```bash
python find_custom_tags.py /prod-configs -o current_versions.txt
cat current_versions.txt  # Посмотреть, что сейчас в продакшне
```

### 2. Экспорт для анализа в Excel
```bash
python find_custom_tags.py /prod-configs -o versions.csv -f csv
# Откройте versions.csv в Excel
```

### 3. Создание документации
```bash
python find_custom_tags.py /prod-configs -o VERSIONS.md -f md
# Добавьте VERSIONS.md в репозиторий
```

### 4. Автоматическая проверка в CI/CD
```bash
#!/bin/bash
python find_custom_tags.py /configs -o check.txt -q

# Проверить, нет ли тега 'latest' в продакшне
if grep -q "tag: latest" check.txt; then
    echo "❌ Тег 'latest' не разрешен в продакшне!"
    exit 1
fi

echo "✅ Все теги валидны"
```

---

## 🔧 Требования

- Python 3.6+
- Нет внешних зависимостей!

---

## 📖 Полная документация

Для детальной информации смотрите:
**[FIND_TAGS_README.md](computer:///mnt/user-data/outputs/FIND_TAGS_README.md)**

---

## 🎁 Примеры файлов

В директории `example_prods/` есть примеры файлов для тестирования:
```bash
# Протестируйте на примерах
python find_custom_tags.py example_prods
```

---

## 💡 Совет

Добавьте алиас для удобства:
```bash
# В ~/.bashrc или ~/.zshrc
alias check-tags='python /path/to/find_custom_tags.py'

# Теперь можно использовать:
check-tags /prod-configs
```

---

**Начните прямо сейчас!** 🚀

```bash
python find_custom_tags.py /your/prod/configs
```
