#!/usr/bin/env python3
"""
Скрипт для поиска кастомных тегов в файлах продакшнов.
Сканирует файлы prodN.yml и находит все указания tag:
"""

import os
import sys
import argparse
import re
from typing import List, Dict, Tuple
from pathlib import Path


class ProductionTagScanner:
    def __init__(self, search_path: str):
        """
        Инициализация сканера.
        
        Args:
            search_path: Путь к директории с файлами продакшнов
        """
        self.search_path = Path(search_path)
        self.results: List[Dict] = []
    
    def is_prod_file(self, filename: str) -> bool:
        """
        Проверяет, является ли файл файлом продакшна.
        
        Args:
            filename: Имя файла
            
        Returns:
            True если это файл продакшна (prodN.yml)
        """
        # Паттерн: prod<число>.yml или prod<число>.yaml
        pattern = r'^prod\d+\.(yml|yaml)$'
        return bool(re.match(pattern, filename, re.IGNORECASE))
    
    def extract_tags(self, file_path: Path) -> List[Tuple[int, str]]:
        """
        Извлекает все строки с tag: из файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Список кортежей (номер_строки, значение_тега)
        """
        tags = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    # Ищем строки с "tag:" (с учетом пробелов и отступов)
                    # Паттерн: любые пробелы, tag:, любые пробелы, значение
                    match = re.search(r'^\s*tag:\s*(.+?)\s*$', line)
                    if match:
                        tag_value = match.group(1).strip()
                        tags.append((line_num, tag_value))
        except Exception as e:
            print(f"⚠️  Ошибка при чтении файла {file_path}: {e}")
        
        return tags
    
    def scan_directory(self) -> None:
        """Сканирует директорию и ищет теги в файлах продакшнов."""
        if not self.search_path.exists():
            print(f"❌ Ошибка: Путь {self.search_path} не существует")
            sys.exit(1)
        
        if not self.search_path.is_dir():
            print(f"❌ Ошибка: {self.search_path} не является директорией")
            sys.exit(1)
        
        print(f"🔍 Сканирование директории: {self.search_path.absolute()}")
        print("=" * 70)
        
        # Собираем все файлы продакшнов
        prod_files = []
        
        for item in self.search_path.iterdir():
            if item.is_file() and self.is_prod_file(item.name):
                prod_files.append(item)
        
        if not prod_files:
            print("\n⚠️  Не найдено ни одного файла продакшна (prod*.yml)")
            return
        
        # Сортируем файлы по имени
        prod_files.sort()
        
        print(f"\n✓ Найдено файлов продакшнов: {len(prod_files)}\n")
        
        # Сканируем каждый файл
        total_tags = 0
        
        for prod_file in prod_files:
            tags = self.extract_tags(prod_file)
            
            if tags:
                result = {
                    'file': prod_file.name,
                    'path': str(prod_file.absolute()),
                    'tags': tags
                }
                self.results.append(result)
                total_tags += len(tags)
        
        self.total_files = len(prod_files)
        self.files_with_tags = len(self.results)
        self.total_tags = total_tags
    
    def print_report(self, detailed: bool = True) -> None:
        """
        Выводит отчет о найденных тегах.
        
        Args:
            detailed: Если True, выводит детальную информацию с номерами строк
        """
        if not self.results:
            print("\n✅ Кастомные теги не найдены во всех файлах продакшнов")
            return
        
        print("\n" + "=" * 70)
        print("📋 ОТЧЕТ: Найденные кастомные теги")
        print("=" * 70)
        
        for idx, result in enumerate(self.results, 1):
            print(f"\n{'─' * 70}")
            print(f"📄 Файл #{idx}: {result['file']}")
            print(f"   Путь: {result['path']}")
            print(f"   Найдено тегов: {len(result['tags'])}")
            print(f"{'─' * 70}")
            
            for line_num, tag_value in result['tags']:
                if detailed:
                    print(f"   Строка {line_num:>4}: tag: {tag_value}")
                else:
                    print(f"   tag: {tag_value}")
        
        # Итоговая статистика
        print("\n" + "=" * 70)
        print("📊 СТАТИСТИКА")
        print("=" * 70)
        print(f"   Всего файлов продакшнов: {self.total_files}")
        print(f"   Файлов с кастомными тегами: {self.files_with_tags}")
        print(f"   Всего найдено тегов: {self.total_tags}")
        print("=" * 70)
    
    def export_to_file(self, output_file: str, format: str = 'txt') -> None:
        """
        Экспортирует отчет в файл.
        
        Args:
            output_file: Путь к выходному файлу
            format: Формат вывода ('txt', 'csv', 'md')
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                if format == 'txt':
                    self._export_txt(f)
                elif format == 'csv':
                    self._export_csv(f)
                elif format == 'md':
                    self._export_markdown(f)
                else:
                    print(f"⚠️  Неизвестный формат: {format}")
                    return
            
            print(f"\n✅ Отчет сохранен в файл: {output_file}")
        except Exception as e:
            print(f"❌ Ошибка при сохранении отчета: {e}")
    
    def _export_txt(self, f) -> None:
        """Экспорт в текстовый формат."""
        f.write("=" * 70 + "\n")
        f.write("ОТЧЕТ: Найденные кастомные теги в файлах продакшнов\n")
        f.write("=" * 70 + "\n\n")
        
        if not self.results:
            f.write("Кастомные теги не найдены\n")
            return
        
        for result in self.results:
            f.write(f"Файл: {result['file']}\n")
            f.write(f"Путь: {result['path']}\n")
            f.write("-" * 70 + "\n")
            
            for line_num, tag_value in result['tags']:
                f.write(f"  Строка {line_num}: tag: {tag_value}\n")
            
            f.write("\n")
        
        f.write("=" * 70 + "\n")
        f.write("СТАТИСТИКА\n")
        f.write("=" * 70 + "\n")
        f.write(f"Всего файлов продакшнов: {self.total_files}\n")
        f.write(f"Файлов с кастомными тегами: {self.files_with_tags}\n")
        f.write(f"Всего найдено тегов: {self.total_tags}\n")
    
    def _export_csv(self, f) -> None:
        """Экспорт в CSV формат."""
        f.write("Файл,Путь,Номер строки,Тег\n")
        
        for result in self.results:
            for line_num, tag_value in result['tags']:
                # Экранируем запятые и кавычки в значениях
                tag_escaped = tag_value.replace('"', '""')
                if ',' in tag_escaped:
                    tag_escaped = f'"{tag_escaped}"'
                
                f.write(f"{result['file']},{result['path']},{line_num},{tag_escaped}\n")
    
    def _export_markdown(self, f) -> None:
        """Экспорт в Markdown формат."""
        f.write("# Отчет: Кастомные теги в файлах продакшнов\n\n")
        
        if not self.results:
            f.write("**Кастомные теги не найдены**\n")
            return
        
        f.write("## Найденные теги\n\n")
        
        for result in self.results:
            f.write(f"### 📄 {result['file']}\n\n")
            f.write(f"**Путь:** `{result['path']}`\n\n")
            f.write(f"**Найдено тегов:** {len(result['tags'])}\n\n")
            
            f.write("| Строка | Тег |\n")
            f.write("|--------|-----|\n")
            
            for line_num, tag_value in result['tags']:
                f.write(f"| {line_num} | `{tag_value}` |\n")
            
            f.write("\n")
        
        f.write("## Статистика\n\n")
        f.write(f"- **Всего файлов продакшнов:** {self.total_files}\n")
        f.write(f"- **Файлов с кастомными тегами:** {self.files_with_tags}\n")
        f.write(f"- **Всего найдено тегов:** {self.total_tags}\n")


def parse_arguments():
    """Парсинг аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description='Поиск кастомных тегов в файлах продакшнов (prodN.yml)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Сканировать текущую директорию
  %(prog)s .

  # Сканировать конкретную директорию
  %(prog)s /path/to/production/configs

  # Сохранить отчет в файл
  %(prog)s /path/to/configs -o report.txt

  # Экспортировать в CSV
  %(prog)s /path/to/configs -o report.csv -f csv

  # Экспортировать в Markdown
  %(prog)s /path/to/configs -o report.md -f md

  # Краткий вывод (без номеров строк)
  %(prog)s /path/to/configs --brief
        """
    )
    
    parser.add_argument(
        'path',
        help='Путь к директории с файлами продакшнов'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Сохранить отчет в файл'
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['txt', 'csv', 'md'],
        default='txt',
        help='Формат выходного файла (по умолчанию: txt)'
    )
    
    parser.add_argument(
        '-b', '--brief',
        action='store_true',
        help='Краткий вывод без номеров строк'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Не выводить отчет на экран (только в файл)'
    )
    
    return parser.parse_args()


def main():
    """Основная функция скрипта."""
    args = parse_arguments()
    
    # Создаем сканер
    scanner = ProductionTagScanner(args.path)
    
    # Сканируем директорию
    scanner.scan_directory()
    
    # Выводим отчет на экран (если не указан флаг --quiet)
    if not args.quiet:
        scanner.print_report(detailed=not args.brief)
    
    # Экспортируем в файл (если указан)
    if args.output:
        scanner.export_to_file(args.output, args.format)


if __name__ == '__main__':
    main()
