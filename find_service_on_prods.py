#!/usr/bin/env python3
"""
Скрипт для поиска сервисов на продах.
Показывает, на каких продах присутствует указанный сервис.
"""

import sys
import argparse
import re
from typing import Dict, Set
from pathlib import Path
from collections import defaultdict


class ServiceFinder:
    def __init__(self, search_path: str, service_filter: str = None):
        self.search_path = Path(search_path)
        self.service_filter = service_filter
        self.services_by_prod: Dict[str, Set[str]] = defaultdict(set)  # {service: {prods}}
        self.prods_by_service: Dict[str, Set[str]] = defaultdict(set)  # {prod: {services}}
        
    def is_yml_file(self, filename: str) -> bool:
        """Проверяет, является ли файл yml/yaml файлом."""
        pattern = r'^.+\.(yml|yaml)$'
        return bool(re.match(pattern, filename, re.IGNORECASE))
    
    def extract_file_name(self, filename: str) -> str:
        """Извлекает имя файла без расширения (имя прода)."""
        name_without_ext = re.sub(r'\.(yml|yaml)$', '', filename, flags=re.IGNORECASE)
        return name_without_ext if name_without_ext else "unknown"
    
    def matches_service_filter(self, service_name: str) -> bool:
        """Проверяет, соответствует ли сервис фильтру."""
        if not self.service_filter:
            return True
        return self.service_filter.lower() in service_name.lower()
    
    def extract_services(self, file_path: Path, prod_name: str) -> None:
        """Извлекает список сервисов из файла."""
        in_services_block = False
        services_indent = -1
        current_service_indent = -1
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                for line in lines:
                    # Пропускаем пустые строки и комментарии
                    if not line.strip() or line.strip().startswith('#'):
                        continue
                    
                    # Определяем уровень отступа
                    line_indent = len(line) - len(line.lstrip())
                    
                    # Ищем блок services:
                    if re.match(r'^services:\s*$', line.strip()):
                        in_services_block = True
                        services_indent = line_indent
                        continue
                    
                    # Если мы в блоке services
                    if in_services_block:
                        # Проверяем, не вышли ли мы из блока services
                        if line_indent <= services_indent and line.strip().endswith(':'):
                            if not line.strip().startswith('-'):
                                in_services_block = False
                                continue
                        
                        # Ищем определение сервиса
                        service_match = re.match(r'^(\s*)(-\s*)?([a-zA-Z0-9_-]+):\s*$', line)
                        if service_match:
                            indent = len(service_match.group(1))
                            service_name = service_match.group(3)
                            
                            # Проверяем, что это сервис (на один уровень глубже services)
                            if indent > services_indent:
                                if current_service_indent == -1 or indent <= current_service_indent:
                                    current_service_indent = indent
                                    # Добавляем связи
                                    self.services_by_prod[service_name].add(prod_name)
                                    self.prods_by_service[prod_name].add(service_name)
                            
        except Exception as e:
            print(f"⚠️  Ошибка при чтении {file_path}: {e}", file=sys.stderr)
    
    def scan_directory(self) -> None:
        """Сканирует директорию с yml файлами."""
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
        
        self.total_files_scanned = len(yml_files)
        
        # Сканируем каждый файл
        for yml_file in yml_files:
            prod_name = self.extract_file_name(yml_file.name)
            self.extract_services(yml_file, prod_name)
    
    def print_prods_with_service(self) -> None:
        """Выводит список продов с указанным сервисом."""
        if not self.service_filter:
            print("⚠️  Укажите название сервиса с помощью -s")
            return
        
        matched_services = {s: prods for s, prods in self.services_by_prod.items() 
                          if self.matches_service_filter(s)}
        
        if not matched_services:
            print(f"❌ Сервисы, соответствующие '{self.service_filter}', не найдены")
            print(f"\nОбработано файлов: {self.total_files_scanned}")
            return
        
        print("=" * 80)
        print(f"🌍 Проды с сервисом (поиск: '{self.service_filter}')")
        print("=" * 80)
        print()
        
        for service in sorted(matched_services.keys()):
            prods = sorted(matched_services[service])
            print(f"📦 Сервис: {service}")
            print(f"   Найден на {len(prods)} проде(ах):")
            print()
            
            for prod in prods:
                print(f"   • {prod}")
            print()
        
        print("=" * 80)
        print(f"Обработано файлов: {self.total_files_scanned}")
        print("=" * 80)
    
    def print_services_on_prod(self, prod_name: str) -> None:
        """Выводит список сервисов на указанном проде."""
        if prod_name not in self.prods_by_service:
            print(f"❌ Прод '{prod_name}' не найден")
            available_prods = sorted(self.prods_by_service.keys())[:10]
            if available_prods:
                print(f"\nДоступные проды (первые 10):")
                for p in available_prods:
                    print(f"  • {p}")
            return
        
        services = sorted(self.prods_by_service[prod_name])
        
        print("=" * 80)
        print(f"📋 Сервисы на проде: {prod_name}")
        print("=" * 80)
        print()
        
        for service in services:
            print(f"  • {service}")
        
        print()
        print(f"Всего сервисов: {len(services)}")
        print("=" * 80)
    
    def print_services_summary(self) -> None:
        """Выводит сводку по всем сервисам."""
        if not self.services_by_prod:
            print("❌ Сервисы не найдены")
            return
        
        print("=" * 80)
        print("📊 Сводка по всем сервисам")
        print("=" * 80)
        print()
        
        # Сортируем по количеству продов (по убыванию)
        sorted_services = sorted(self.services_by_prod.items(), 
                                key=lambda x: (len(x[1]), x[0]), 
                                reverse=True)
        
        print(f"{'Сервис':<40} {'Кол-во продов':>15}")
        print("-" * 80)
        
        for service, prods in sorted_services:
            prod_count = len(prods)
            print(f"{service:<40} {prod_count:>15}")
        
        print()
        print("=" * 80)
        print(f"Всего уникальных сервисов: {len(self.services_by_prod)}")
        print(f"Всего продов: {len(self.prods_by_service)}")
        print("=" * 80)
    
    def print_prods_summary(self) -> None:
        """Выводит сводку по всем продам."""
        if not self.prods_by_service:
            print("❌ Проды не найдены")
            return
        
        print("=" * 80)
        print("📊 Сводка по всем продам")
        print("=" * 80)
        print()
        
        # Сортируем по количеству сервисов (по убыванию)
        sorted_prods = sorted(self.prods_by_service.items(), 
                             key=lambda x: (len(x[1]), x[0]), 
                             reverse=True)
        
        print(f"{'Прод':<40} {'Кол-во сервисов':>15}")
        print("-" * 80)
        
        for prod, services in sorted_prods:
            service_count = len(services)
            print(f"{prod:<40} {service_count:>15}")
        
        print()
        print("=" * 80)
        print(f"Всего продов: {len(self.prods_by_service)}")
        print(f"Всего уникальных сервисов: {len(self.services_by_prod)}")
        print("=" * 80)
    
    def export_to_csv(self, output_file: str, mode: str = 'services') -> None:
        """Экспортирует данные в CSV."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                if mode == 'services':
                    # Формат: service,prod
                    f.write("service,prod\n")
                    for service, prods in sorted(self.services_by_prod.items()):
                        for prod in sorted(prods):
                            f.write(f"{service},{prod}\n")
                
                elif mode == 'prods':
                    # Формат: prod,service
                    f.write("prod,service\n")
                    for prod, services in sorted(self.prods_by_service.items()):
                        for service in sorted(services):
                            f.write(f"{prod},{service}\n")
                
                elif mode == 'summary':
                    # Формат: service,prod_count
                    f.write("service,prod_count\n")
                    sorted_services = sorted(self.services_by_prod.items(), 
                                           key=lambda x: len(x[1]), 
                                           reverse=True)
                    for service, prods in sorted_services:
                        f.write(f"{service},{len(prods)}\n")
            
            print(f"\n✅ Данные сохранены: {output_file}")
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}", file=sys.stderr)


def parse_arguments():
    """Парсинг аргументов."""
    parser = argparse.ArgumentParser(
        description='Поиск сервисов на продах',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Найти, на каких продах есть operator_api
  %(prog)s /path/to/configs -s operator_api
  
  # Найти все сервисы, содержащие "api"
  %(prog)s /path/to/configs -s api
  
  # Посмотреть все сервисы на конкретном проде
  %(prog)s /path/to/configs --prod prod123
  
  # Показать сводку по всем сервисам
  %(prog)s /path/to/configs --services-summary
  
  # Показать сводку по всем продам
  %(prog)s /path/to/configs --prods-summary
  
  # Экспортировать в CSV
  %(prog)s /path/to/configs -s operator_api -o report.csv
  %(prog)s /path/to/configs --services-summary -o summary.csv --csv-mode summary
        """
    )
    
    parser.add_argument('path', help='Путь к директории с yml/yaml файлами продов')
    parser.add_argument('-s', '--service', dest='service_filter',
                       help='Название сервиса для поиска (поиск по вхождению)')
    parser.add_argument('--prod', help='Показать все сервисы на указанном проде')
    parser.add_argument('--services-summary', action='store_true',
                       help='Показать сводку по всем сервисам')
    parser.add_argument('--prods-summary', action='store_true',
                       help='Показать сводку по всем продам')
    parser.add_argument('-o', '--output', help='Сохранить результат в CSV файл')
    parser.add_argument('--csv-mode', choices=['services', 'prods', 'summary'],
                       default='services',
                       help='Режим экспорта CSV: services (по сервисам), prods (по продам), summary (сводка)')
    
    return parser.parse_args()


def main():
    args = parse_arguments()
    
    finder = ServiceFinder(args.path, args.service_filter)
    finder.scan_directory()
    
    # Определяем, что показывать
    if args.prod:
        finder.print_services_on_prod(args.prod)
    elif args.services_summary:
        finder.print_services_summary()
        if args.output:
            finder.export_to_csv(args.output, 'summary')
    elif args.prods_summary:
        finder.print_prods_summary()
    elif args.service_filter:
        finder.print_prods_with_service()
        if args.output:
            finder.export_to_csv(args.output, args.csv_mode)
    else:
        print("⚠️  Укажите один из параметров:")
        print("  -s SERVICE        - найти проды с сервисом")
        print("  --prod PROD       - показать сервисы на проде")
        print("  --services-summary - сводка по сервисам")
        print("  --prods-summary   - сводка по продам")
        sys.exit(1)


if __name__ == '__main__':
    main()