#!/usr/bin/env python3
"""
Скрипт для поиска кастомных тегов в yml файлах.
Сканирует все .yml и .yaml файлы в указанной директории.
Показывает только теги с префиксами (feature/, hotfix/, и т.д.)
Игнорирует версионные теги (1.0.0) и хеши коммитов.
Группирует результаты по файлам.
Исключает из статистики сервисы с суффиксом -limited.
"""

import sys
import argparse
import re
from typing import List, Dict
from pathlib import Path
from collections import defaultdict


class CompactTagScanner:
    def __init__(self, search_path: str):
        self.search_path = Path(search_path)
        self.results: Dict[str, List[Dict]] = defaultdict(list)
    
    def is_prod_file(self, filename: str) -> bool:
        """Проверяет, является ли файл yml/yaml файлом."""
        pattern = r'^.+\.(yml|yaml)$'
        return bool(re.match(pattern, filename, re.IGNORECASE))
    
    def extract_prod_number(self, filename: str) -> str:
        """Извлекает имя прода из имени файла (имя файла без расширения)."""
        # Убираем расширение .yml или .yaml
        name_without_ext = re.sub(r'\.(yml|yaml)$', '', filename, flags=re.IGNORECASE)
        return name_without_ext if name_without_ext else "unknown"
    
    def is_custom_tag(self, tag: str) -> bool:
        """
        Проверяет, является ли тег кастомным.
        Кастомные теги содержат: feature/, hotfix/, bugfix/, release/, develop/, и т.д.
        Исключает: версионные теги (1.0.0, v1.0.0) и хеши коммитов.
        """
        tag = tag.strip().strip('"\'')
        
        # Игнорируем версионные теги типа 1.0.0, v1.0.0, 1.0.0-alpha
        if re.match(r'^v?\d+\.\d+(\.\d+)?(-\w+)?$', tag):
            return False
        
        # Игнорируем хеши коммитов (7-40 символов hex)
        if re.match(r'^[a-f0-9]{7,40}$', tag, re.IGNORECASE):
            return False
        
        # Принимаем теги с префиксами (feature/, hotfix/, etc) или содержащие слеш
        if '/' in tag:
            return True
        
        # Игнорируем теги типа "latest", "stable", "production"
        if tag.lower() in ['latest', 'stable', 'production', 'main', 'master', 'develop']:
            return False
        
        return False
    
    def extract_tags(self, file_path: Path, prod_name: str) -> None:
        """Извлекает кастомные теги из файла."""
        current_service = "unknown"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    # Ищем определение сервиса
                    service_match = re.search(r'^\s*-?\s*name:\s*["\']?([a-zA-Z0-9_-]+)["\']?\s*$', line)
                    if service_match:
                        current_service = service_match.group(1).strip()
                    
                    # Альтернативный формат сервиса
                    service_key_match = re.search(r'^(\s*)([a-zA-Z0-9_-]+):\s*$', line)
                    if service_key_match:
                        indent = len(service_key_match.group(1))
                        potential_service = service_key_match.group(2).strip()
                        excluded_words = ['services', 'volumes', 'networks', 'configs', 'secrets', 
                                        'environment', 'labels', 'ports', 'image', 'deploy', 
                                        'version', 'build', 'depends_on', 'restart', 'command',
                                        'entrypoint', 'healthcheck', 'logging']
                        if potential_service not in excluded_words and indent <= 4:
                            current_service = potential_service
                    
                    # Ищем строки с "tag:" или "tag :"
                    tag_match = re.search(r'^\s*tag\s*:\s*(.+?)\s*$', line)
                    if tag_match:
                        tag_value = tag_match.group(1).strip().strip('"\'')
                        
                        # Исключаем сервисы с суффиксом -limited
                        if current_service.endswith('-limited'):
                            continue
                        
                        # Проверяем, является ли тег кастомным
                        if self.is_custom_tag(tag_value):
                            self.results[prod_name].append({
                                'service': current_service,
                                'tag': tag_value
                            })
        except Exception as e:
            print(f"⚠️  Ошибка при чтении {file_path}: {e}", file=sys.stderr)
    
    def scan_directory(self) -> None:
        """Сканирует директорию и ищет теги."""
        if not self.search_path.exists():
            print(f"❌ Путь {self.search_path} не существует")
            sys.exit(1)
        
        if not self.search_path.is_dir():
            print(f"❌ {self.search_path} не является директорией")
            sys.exit(1)
        
        # Собираем все файлы продакшнов
        prod_files = [f for f in self.search_path.iterdir() 
                     if f.is_file() and self.is_prod_file(f.name)]
        
        if not prod_files:
            print("⚠️  Не найдено yml/yaml файлов")
            sys.exit(0)
        
        # Сортируем и сканируем
        prod_files.sort()
        
        self.total_files_scanned = len(prod_files)
        self.files_with_custom_tags = 0
        
        for prod_file in prod_files:
            prod_name = self.extract_prod_number(prod_file.name)
            self.extract_tags(prod_file, prod_name)
            
            # Подсчитываем файлы с кастомными тегами
            if prod_name in self.results and len(self.results[prod_name]) > 0:
                self.files_with_custom_tags += 1
    
    def print_report(self) -> None:
        """Выводит минимальный отчет с группировкой по продам."""
        if not self.results:
            print("✅ Кастомные теги не найдены")
            print(f"\nОбработано файлов: {self.total_files_scanned}")
            return
        
        # Сортируем проды для последовательного вывода
        for prod in sorted(self.results.keys()):
            tags = self.results[prod]
            print(f"path: {prod}")
            
            for tag_info in tags:
                print(f"  service: {tag_info['service']}")
                print(f"  tag: {tag_info['tag']}")
            
            print()
        
        # Статистика
        total_tags = sum(len(tags) for tags in self.results.values())
        print(f"Статистика:")
        print(f"  Обработано файлов: {self.total_files_scanned}")
        print(f"  Файлов с кастомными тегами: {self.files_with_custom_tags}")
        print(f"  Всего найдено кастомных тегов: {total_tags}")
    
    def export_to_file(self, output_file: str, format: str = 'txt') -> None:
        """Экспортирует отчет в файл."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                if format == 'txt':
                    self._export_txt(f)
                elif format == 'csv':
                    self._export_csv(f)
                elif format == 'md':
                    self._export_markdown(f)
            
            print(f"✅ Отчет сохранен: {output_file}", file=sys.stderr)
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}", file=sys.stderr)
    
    def _export_txt(self, f) -> None:
        """Экспорт в текстовый формат."""
        if not self.results:
            f.write("Кастомные теги не найдены\n")
            f.write(f"\nОбработано файлов: {self.total_files_scanned}\n")
            return
        
        for prod in sorted(self.results.keys()):
            tags = self.results[prod]
            f.write(f"path: {prod}\n")
            
            for tag_info in tags:
                f.write(f"  service: {tag_info['service']}\n")
                f.write(f"  tag: {tag_info['tag']}\n")
            
            f.write("\n")
        
        # Статистика
        total_tags = sum(len(tags) for tags in self.results.values())
        f.write("\nСтатистика:\n")
        f.write(f"  Обработано файлов: {self.total_files_scanned}\n")
        f.write(f"  Файлов с кастомными тегами: {self.files_with_custom_tags}\n")
        f.write(f"  Всего найдено кастомных тегов: {total_tags}\n")
    
    def _export_csv(self, f) -> None:
        """Экспорт в CSV формат."""
        f.write("path,service,tag\n")
        
        for prod in sorted(self.results.keys()):
            for tag_info in self.results[prod]:
                tag_escaped = tag_info['tag'].replace('"', '""')
                service_escaped = tag_info['service'].replace('"', '""')
                
                if ',' in tag_escaped:
                    tag_escaped = f'"{tag_escaped}"'
                if ',' in service_escaped:
                    service_escaped = f'"{service_escaped}"'
                
                f.write(f"{prod},{service_escaped},{tag_escaped}\n")
    
    def _export_markdown(self, f) -> None:
        """Экспорт в Markdown формат."""
        if not self.results:
            f.write("**Кастомные теги не найдены**\n\n")
            f.write(f"Обработано файлов: {self.total_files_scanned}\n")
            return
        
        f.write("# Кастомные теги\n\n")
        
        for prod in sorted(self.results.keys()):
            tags = self.results[prod]
            f.write(f"## {prod}\n\n")
            f.write("| Service | Tag |\n")
            f.write("|---------|-----|\n")
            
            for tag_info in tags:
                f.write(f"| `{tag_info['service']}` | `{tag_info['tag']}` |\n")
            
            f.write("\n")
        
        # Статистика
        total_tags = sum(len(tags) for tags in self.results.values())
        f.write("## Статистика\n\n")
        f.write(f"- **Обработано файлов:** {self.total_files_scanned}\n")
        f.write(f"- **Файлов с кастомными тегами:** {self.files_with_custom_tags}\n")
        f.write(f"- **Всего найдено кастомных тегов:** {total_tags}\n")


def parse_arguments():
    """Парсинг аргументов."""
    parser = argparse.ArgumentParser(
        description='Поиск кастомных тегов (feature/, hotfix/, и т.д.) во всех yml/yaml файлах',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('path', help='Путь к директории с yml/yaml файлами')
    parser.add_argument('-o', '--output', help='Сохранить отчет в файл')
    parser.add_argument('-f', '--format', choices=['txt', 'csv', 'md'], 
                       default='txt', help='Формат файла (по умолчанию: txt)')
    parser.add_argument('-q', '--quiet', action='store_true', 
                       help='Не выводить на экран (только в файл)')
    
    return parser.parse_args()


def main():
    args = parse_arguments()
    
    scanner = CompactTagScanner(args.path)
    scanner.scan_directory()
    
    if not args.quiet:
        scanner.print_report()
    
    if args.output:
        scanner.export_to_file(args.output, args.format)


if __name__ == '__main__':
    main()
