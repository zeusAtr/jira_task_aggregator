#!/usr/bin/env python3
"""
Скрипт для анализа jvm_run_opts из указанных сервисов во всех yml файлах.
Находит все JVM опции, группирует их и показывает уникальные значения.
"""

import sys
import argparse
import re
from typing import List, Dict, Set
from pathlib import Path
from collections import defaultdict


class JVMOptsScanner:
    def __init__(self, search_path: str, service_filter: str = None):
        self.search_path = Path(search_path)
        self.service_filter = service_filter
        self.results: Dict[str, Dict] = {}  # {file: {service: opts}}
        self.all_opts: Set[str] = set()
        self.all_services: Dict[str, Set[str]] = defaultdict(set)  # {file: {services}}
        
    def is_yml_file(self, filename: str) -> bool:
        """Проверяет, является ли файл yml/yaml файлом."""
        pattern = r'^.+\.(yml|yaml)$'
        return bool(re.match(pattern, filename, re.IGNORECASE))
    
    def extract_file_name(self, filename: str) -> str:
        """Извлекает имя файла без расширения."""
        name_without_ext = re.sub(r'\.(yml|yaml)$', '', filename, flags=re.IGNORECASE)
        return name_without_ext if name_without_ext else "unknown"
    
    def matches_service_filter(self, service_name: str) -> bool:
        """Проверяет, соответствует ли сервис фильтру."""
        if not self.service_filter:
            return True  # Если фильтр не задан, берём все сервисы
        return self.service_filter.lower() in service_name.lower()
    
    def parse_jvm_opts_line(self, line: str) -> List[str]:
        """
        Парсит строку с jvm_run_opts и извлекает отдельные опции.
        Поддерживает форматы:
        - jvm_run_opts: "-Xmx2g -XX:+UseG1GC"
        - jvm_run_opts: -Xmx2g -XX:+UseG1GC
        """
        # Убираем jvm_run_opts: и кавычки
        opts_str = re.sub(r'^\s*jvm_run_opts\s*:\s*', '', line)
        opts_str = opts_str.strip().strip('"\'')
        
        if not opts_str:
            return []
        
        # Разбиваем по пробелам, учитывая опции с пробелами в значениях
        opts = []
        current_opt = []
        in_quotes = False
        
        tokens = opts_str.split()
        for token in tokens:
            if token.startswith('"') or token.startswith("'"):
                in_quotes = True
                current_opt.append(token)
            elif in_quotes:
                current_opt.append(token)
                if token.endswith('"') or token.endswith("'"):
                    in_quotes = False
                    opts.append(' '.join(current_opt))
                    current_opt = []
            else:
                opts.append(token)
        
        # Если остались незакрытые кавычки
        if current_opt:
            opts.append(' '.join(current_opt))
        
        return [opt.strip('"\'') for opt in opts if opt]
    
    def extract_jvm_opts(self, file_path: Path, file_name: str) -> None:
        """Извлекает jvm_run_opts из сервисов в файле."""
        current_service = None
        in_services_block = False
        services_indent = -1
        current_service_indent = -1
        matches_filter = False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    # Пропускаем пустые строки и комментарии
                    if not line.strip() or line.strip().startswith('#'):
                        continue
                    
                    # Определяем уровень отступа
                    line_indent = len(line) - len(line.lstrip())
                    
                    # Ищем блок services:
                    if re.match(r'^services:\s*$', line.strip()):
                        in_services_block = True
                        services_indent = line_indent
                        current_service = None
                        continue
                    
                    # Если мы в блоке services
                    if in_services_block:
                        # Проверяем, не вышли ли мы из блока services
                        if line_indent <= services_indent and line.strip().endswith(':'):
                            # Это новый блок на том же уровне, что и services
                            if not line.strip().startswith('-'):
                                in_services_block = False
                                current_service = None
                                continue
                        
                        # Ищем определение сервиса внутри блока services
                        # Формат: service_name: или - service_name:
                        service_match = re.match(r'^(\s*)(-\s*)?([a-zA-Z0-9_-]+):\s*$', line)
                        if service_match:
                            indent = len(service_match.group(1))
                            service_name = service_match.group(3)
                            
                            # Проверяем, что это сервис (на один уровень глубже services)
                            if indent > services_indent:
                                # Если это на том же уровне, что предыдущий сервис, или глубже services
                                if current_service is None or indent <= current_service_indent:
                                    current_service = service_name
                                    current_service_indent = indent
                                    self.all_services[file_name].add(current_service)
                                    matches_filter = self.matches_service_filter(current_service)
                            continue
                        
                        # Альтернативный формат: name: service_name внутри блока сервиса
                        name_match = re.match(r'^\s*name:\s*["\']?([a-zA-Z0-9_-]+)["\']?\s*$', line)
                        if name_match and current_service:
                            # Обновляем имя сервиса, если оно задано через name:
                            service_name_from_field = name_match.group(1)
                            # Можно использовать это имя вместо ключа
                            # Но для сохранения совместимости, оставим ключ как основное имя
                            pass
                        
                        # Ищем jvm_run_opts только для подходящих сервисов
                        if matches_filter and current_service:
                            jvm_match = re.search(r'^\s*jvm_run_opts\s*:\s*(.+?)\s*$', line)
                            if jvm_match:
                                # Проверяем, что это внутри текущего сервиса
                                if line_indent > current_service_indent:
                                    opts = self.parse_jvm_opts_line(line)
                                    
                                    if opts:
                                        # Сохраняем результаты
                                        if file_name not in self.results:
                                            self.results[file_name] = {}
                                        
                                        if current_service not in self.results[file_name]:
                                            self.results[file_name][current_service] = []
                                        
                                        self.results[file_name][current_service].extend(opts)
                                        
                                        # Добавляем в общий набор
                                        self.all_opts.update(opts)
                            
        except Exception as e:
            print(f"⚠️  Ошибка при чтении {file_path}: {e}", file=sys.stderr)
    
    def scan_directory(self) -> None:
        """Сканирует директорию и ищет jvm_run_opts."""
        if not self.search_path.exists():
            print(f"❌ Путь {self.search_path} не существует")
            sys.exit(1)
        
        if not self.search_path.is_dir():
            print(f"❌ {self.search_path} не является директорией")
            sys.exit(1)
        
        # Собираем все yml файлы
        yml_files = [f for f in self.search_path.iterdir() 
                     if f.is_file() and self.is_yml_file(f.name)]
        
        if not yml_files:
            print("⚠️  Не найдено yml/yaml файлов")
            sys.exit(0)
        
        # Сортируем и сканируем
        yml_files.sort()
        
        self.total_files_scanned = len(yml_files)
        self.files_with_services = 0
        
        for yml_file in yml_files:
            file_name = self.extract_file_name(yml_file.name)
            self.extract_jvm_opts(yml_file, file_name)
            
            if file_name in self.results:
                self.files_with_services += 1
    
    def print_all_services(self) -> None:
        """Выводит список всех найденных сервисов."""
        if not self.all_services:
            print("❌ Сервисы не найдены")
            return
        
        print("=" * 80)
        print("📋 Все найденные сервисы")
        print("=" * 80)
        print()
        
        for file_name in sorted(self.all_services.keys()):
            services = sorted(self.all_services[file_name])
            if services:
                print(f"Файл: {file_name}")
                for service in services:
                    print(f"  - {service}")
                print()
        
        total_services = sum(len(services) for services in self.all_services.values())
        print(f"Всего найдено сервисов: {total_services}")
        print("=" * 80)
    
    def print_report(self) -> None:
        """Выводит отчет о найденных JVM опциях."""
        filter_text = f" (фильтр: '{self.service_filter}')" if self.service_filter else ""
        
        if not self.results:
            print(f"✅ JVM опции в сервисах{filter_text} не найдены")
            print(f"\nОбработано файлов: {self.total_files_scanned}")
            return
        
        print("=" * 80)
        print(f"📋 JVM_RUN_OPTS в сервисах{filter_text}")
        print("=" * 80)
        print()
        
        # Детальный вывод по файлам и сервисам
        for file_name in sorted(self.results.keys()):
            services = self.results[file_name]
            print(f"Файл: {file_name}")
            
            for service_name in sorted(services.keys()):
                opts = services[service_name]
                print(f"  Сервис: {service_name}")
                print(f"    jvm_run_opts:")
                for opt in opts:
                    print(f"      {opt}")
            print()
        
        # Уникальные опции
        print("=" * 80)
        print("📊 Уникальные JVM опции (сгруппированные)")
        print("=" * 80)
        print()
        
        for opt in sorted(self.all_opts):
            print(f"  {opt}")
        
        # Статистика
        total_services = sum(len(services) for services in self.results.values())
        print()
        print("=" * 80)
        print("📈 Статистика")
        print("=" * 80)
        print(f"  Обработано файлов: {self.total_files_scanned}")
        print(f"  Файлов с найденными сервисами: {self.files_with_services}")
        print(f"  Найдено сервисов с JVM опциями: {total_services}")
        print(f"  Уникальных JVM опций: {len(self.all_opts)}")
        if self.service_filter:
            print(f"  Фильтр сервисов: '{self.service_filter}'")
        print("=" * 80)
    
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
            
            print(f"\n✅ Отчет сохранен: {output_file}", file=sys.stderr)
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}", file=sys.stderr)
    
    def _export_txt(self, f) -> None:
        """Экспорт в текстовый формат."""
        filter_text = f" (фильтр: '{self.service_filter}')" if self.service_filter else ""
        
        if not self.results:
            f.write(f"JVM опции в сервисах{filter_text} не найдены\n")
            f.write(f"\nОбработано файлов: {self.total_files_scanned}\n")
            return
        
        f.write("=" * 80 + "\n")
        f.write(f"JVM_RUN_OPTS в сервисах{filter_text}\n")
        f.write("=" * 80 + "\n\n")
        
        # Детальный вывод
        for file_name in sorted(self.results.keys()):
            services = self.results[file_name]
            f.write(f"Файл: {file_name}\n")
            
            for service_name in sorted(services.keys()):
                opts = services[service_name]
                f.write(f"  Сервис: {service_name}\n")
                f.write(f"    jvm_run_opts:\n")
                for opt in opts:
                    f.write(f"      {opt}\n")
            f.write("\n")
        
        # Уникальные опции
        f.write("=" * 80 + "\n")
        f.write("Уникальные JVM опции (сгруппированные)\n")
        f.write("=" * 80 + "\n\n")
        
        for opt in sorted(self.all_opts):
            f.write(f"  {opt}\n")
        
        # Статистика
        total_services = sum(len(services) for services in self.results.values())
        f.write("\n" + "=" * 80 + "\n")
        f.write("Статистика\n")
        f.write("=" * 80 + "\n")
        f.write(f"  Обработано файлов: {self.total_files_scanned}\n")
        f.write(f"  Файлов с найденными сервисами: {self.files_with_services}\n")
        f.write(f"  Найдено сервисов с JVM опциями: {total_services}\n")
        f.write(f"  Уникальных JVM опций: {len(self.all_opts)}\n")
        if self.service_filter:
            f.write(f"  Фильтр сервисов: '{self.service_filter}'\n")
    
    def _export_csv(self, f) -> None:
        """Экспорт в CSV формат."""
        # Детальный CSV
        f.write("file,service,jvm_option\n")
        
        for file_name in sorted(self.results.keys()):
            services = self.results[file_name]
            for service_name in sorted(services.keys()):
                opts = services[service_name]
                for opt in opts:
                    opt_escaped = opt.replace('"', '""')
                    if ',' in opt_escaped:
                        opt_escaped = f'"{opt_escaped}"'
                    f.write(f"{file_name},{service_name},{opt_escaped}\n")
    
    def _export_markdown(self, f) -> None:
        """Экспорт в Markdown формат."""
        filter_text = f" (фильтр: `{self.service_filter}`)" if self.service_filter else ""
        
        if not self.results:
            f.write(f"**JVM опции в сервисах{filter_text} не найдены**\n\n")
            f.write(f"Обработано файлов: {self.total_files_scanned}\n")
            return
        
        f.write(f"# JVM_RUN_OPTS в сервисах{filter_text}\n\n")
        
        # Детальный вывод
        for file_name in sorted(self.results.keys()):
            services = self.results[file_name]
            f.write(f"## Файл: {file_name}\n\n")
            
            for service_name in sorted(services.keys()):
                opts = services[service_name]
                f.write(f"### Сервис: `{service_name}`\n\n")
                f.write("```\n")
                for opt in opts:
                    f.write(f"{opt}\n")
                f.write("```\n\n")
        
        # Уникальные опции
        f.write("## Уникальные JVM опции (сгруппированные)\n\n")
        f.write("```\n")
        for opt in sorted(self.all_opts):
            f.write(f"{opt}\n")
        f.write("```\n\n")
        
        # Статистика
        total_services = sum(len(services) for services in self.results.values())
        f.write("## Статистика\n\n")
        f.write(f"- **Обработано файлов:** {self.total_files_scanned}\n")
        f.write(f"- **Файлов с найденными сервисами:** {self.files_with_services}\n")
        f.write(f"- **Найдено сервисов с JVM опциями:** {total_services}\n")
        f.write(f"- **Уникальных JVM опций:** {len(self.all_opts)}\n")
        if self.service_filter:
            f.write(f"- **Фильтр сервисов:** `{self.service_filter}`\n")


def parse_arguments():
    """Парсинг аргументов."""
    parser = argparse.ArgumentParser(
        description='Анализ jvm_run_opts из указанных сервисов во всех yml/yaml файлах',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s /path/to/configs -s admin             # Искать только admin сервисы
  %(prog)s /path/to/configs -s announcing        # Искать announcing сервисы
  %(prog)s /path/to/configs                      # Искать во всех сервисах
  %(prog)s /path/to/configs -s api -o report.txt # Сохранить в файл
  %(prog)s /path/to/configs --list-services      # Показать все найденные сервисы
        """
    )
    
    parser.add_argument('path', help='Путь к директории с yml/yaml файлами')
    parser.add_argument('-s', '--service', dest='service_filter',
                       help='Фильтр по имени сервиса (поиск по вхождению, например: admin, announcing)')
    parser.add_argument('-o', '--output', help='Сохранить отчет в файл')
    parser.add_argument('-f', '--format', choices=['txt', 'csv', 'md'], 
                       default='txt', help='Формат файла (по умолчанию: txt)')
    parser.add_argument('-q', '--quiet', action='store_true', 
                       help='Не выводить на экран (только в файл)')
    parser.add_argument('--list-services', action='store_true',
                       help='Показать список всех найденных сервисов')
    
    return parser.parse_args()


def main():
    args = parse_arguments()
    
    scanner = JVMOptsScanner(args.path, args.service_filter)
    scanner.scan_directory()
    
    if args.list_services:
        scanner.print_all_services()
        return
    
    if not args.quiet:
        scanner.print_report()
    
    if args.output:
        scanner.export_to_file(args.output, args.format)


if __name__ == '__main__':
    main()