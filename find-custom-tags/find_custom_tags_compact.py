#!/usr/bin/env python3
"""
Скрипт для поиска кастомных тегов в файлах продакшнов.
Показывает только теги с префиксами (feature/, hotfix/, и т.д.)
Игнорирует версионные теги (1.0.0) и хеши коммитов.
"""

import sys
import argparse
import re
from typing import List, Dict
from pathlib import Path


class CompactTagScanner:
    def __init__(self, search_path: str):
        self.search_path = Path(search_path)
        self.results: List[Dict] = []
    
    def is_prod_file(self, filename: str) -> bool:
        """Проверяет, является ли файл файлом продакшна."""
        pattern = r'^prod\d+\.(yml|yaml)$'
        return bool(re.match(pattern, filename, re.IGNORECASE))
    
    def extract_prod_number(self, filename: str) -> str:
        """Извлекает номер прода из имени файла."""
        match = re.search(r'(prod\d+)', filename, re.IGNORECASE)
        return match.group(1).lower() if match else "unknown"
    
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
                        
                        # Проверяем, является ли тег кастомным
                        if self.is_custom_tag(tag_value):
                            self.results.append({
                                'prod': prod_name,
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
            print("⚠️  Не найдено файлов продакшнов (prod*.yml)")
            sys.exit(0)
        
        # Сортируем и сканируем
        prod_files.sort()
        for prod_file in prod_files:
            prod_name = self.extract_prod_number(prod_file.name)
            self.extract_tags(prod_file, prod_name)
    
    def print_report(self) -> None:
        """Выводит минимальный отчет."""
        if not self.results:
            print("✅ Кастомные теги не найдены")
            return
        
        for result in self.results:
            print(f"path: {result['prod']}")
            print(f"service: {result['service']}")
            print(f"tag: {result['tag']}")
            print()
    
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
            return
        
        for result in self.results:
            f.write(f"path: {result['prod']}\n")
            f.write(f"service: {result['service']}\n")
            f.write(f"tag: {result['tag']}\n")
            f.write("\n")
    
    def _export_csv(self, f) -> None:
        """Экспорт в CSV формат."""
        f.write("path,service,tag\n")
        for result in self.results:
            tag_escaped = result['tag'].replace('"', '""')
            if ',' in tag_escaped:
                tag_escaped = f'"{tag_escaped}"'
            f.write(f"{result['prod']},{result['service']},{tag_escaped}\n")
    
    def _export_markdown(self, f) -> None:
        """Экспорт в Markdown формат."""
        if not self.results:
            f.write("**Кастомные теги не найдены**\n")
            return
        
        f.write("# Кастомные теги\n\n")
        f.write("| Path | Service | Tag |\n")
        f.write("|------|---------|-----|\n")
        
        for result in self.results:
            f.write(f"| {result['prod']} | `{result['service']}` | `{result['tag']}` |\n")


def parse_arguments():
    """Парсинг аргументов."""
    parser = argparse.ArgumentParser(
        description='Поиск кастомных тегов (feature/, hotfix/, и т.д.) в файлах продакшнов',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('path', help='Путь к директории с файлами продакшнов')
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
