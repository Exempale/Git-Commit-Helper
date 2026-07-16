#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess
from typing import Tuple, List, Optional

class Colors:
    """ANSI цветовые коды для форматирования вывода."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

class GitHelper:
    """Утилиты для безопасного взаимодействия с Git."""
    
    @staticmethod
    def run(args: List[str], exit_on_error: bool = False) -> Tuple[int, str, str]:
        """Безопасное выполнение команды без shell=True."""
        try:
            result = subprocess.run(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if exit_on_error and result.returncode != 0:
                print(f"{Colors.FAIL}✖ Ошибка выполнения: {' '.join(args)}{Colors.ENDC}")
                print(f"{Colors.DIM}{result.stderr.strip()}{Colors.ENDC}")
                sys.exit(1)
                
            return result.returncode, result.stdout.strip(), result.stderr.strip()
            
        except FileNotFoundError:
            print(f"{Colors.FAIL}✖ Команда не найдена: {args[0]}. Убедитесь, что Git установлен.{Colors.ENDC}")
            sys.exit(1)

class ConventionalCommitCLI:
    """Главный класс CLI-приложения для создания коммитов."""
    
    COMMIT_TYPES = [
        {"type": "feat", "emoji": "✨", "desc": "Новая функциональность (A new feature)"},
        {"type": "fix", "emoji": "🐛", "desc": "Исправление бага (A bug fix)"},
        {"type": "docs", "emoji": "📚", "desc": "Обновление документации (Documentation only changes)"},
        {"type": "style", "emoji": "💎", "desc": "Форматирование кода (No logic changes)"},
        {"type": "refactor", "emoji": "♻️ ", "desc": "Рефакторинг (Neither fixes a bug nor adds a feature)"},
        {"type": "perf", "emoji": "⚡️", "desc": "Улучшение производительности (Improves performance)"},
        {"type": "test", "emoji": "🚨", "desc": "Добавление/исправление тестов (Adding/fixing tests)"},
        {"type": "build", "emoji": "📦", "desc": "Изменения сборки/зависимостей (npm, pip, docker)"},
        {"type": "ci", "emoji": "👷", "desc": "Настройки CI/CD (GitHub Actions, GitLab CI)"},
        {"type": "chore", "emoji": "🔧", "desc": "Рутинные задачи (Other changes)"},
        {"type": "revert", "emoji": "⏪", "desc": "Откат коммита (Reverts a previous commit)"},
    ]

    def check_environment(self) -> None:
        """Проверяет состояние репозитория и предлагает авто-индексацию."""
        code, _, _ = GitHelper.run(["git", "rev-parse", "--is-inside-work-tree"])
        if code != 0:
            print(f"{Colors.FAIL}✖ Текущая директория не является Git репозиторием!{Colors.ENDC}")
            sys.exit(1)

        _, staged, _ = GitHelper.run(["git", "diff", "--cached", "--name-only"])
        if not staged:
            _, unstaged, _ = GitHelper.run(["git", "status", "--porcelain"])
            if not unstaged:
                print(f"{Colors.CYAN}ℹ Нет изменений для коммита. Рабочее дерево чистое.{Colors.ENDC}")
                sys.exit(0)
                
            print(f"{Colors.WARNING}⚠ Нет проиндексированных файлов (staged), но есть изменения.{Colors.ENDC}")
            ans = input(f"{Colors.BOLD}Добавить все изменения (git add -A)? [Y/n]: {Colors.ENDC}").strip().lower()
            
            if ans in ['', 'y', 'yes', 'да', 'д']:
                GitHelper.run(["git", "add", "-A"], exit_on_error=True)
                print(f"{Colors.GREEN}✔ Все изменения добавлены.{Colors.ENDC}\n")
            else:
                print(f"{Colors.FAIL}✖ Коммит отменен. Добавьте файлы вручную.{Colors.ENDC}")
                sys.exit(0)
        else:
            files = staged.split('\n')
            print(f"{Colors.CYAN}ℹ Подготовлено к коммиту файлов: {len(files)}{Colors.ENDC}")
            for f in files[:3]:
                print(f"  + {Colors.GREEN}{f}{Colors.ENDC}")
            if len(files) > 3:
                print(f"  {Colors.DIM}...и еще {len(files) - 3} файлов{Colors.ENDC}")
            print()

    def get_commit_type(self) -> dict:
        """Интерактивный выбор типа коммита."""
        print(f"{Colors.HEADER}{Colors.BOLD}--- Выберите тип коммита ---{Colors.ENDC}")
        for i, t in enumerate(self.COMMIT_TYPES, 1):
            emoji_type = f"{t['emoji']} {t['type']}".ljust(15)
            print(f" {Colors.CYAN}{i:2d}.{Colors.ENDC} {Colors.GREEN}{emoji_type}{Colors.ENDC} │ {t['desc']}")
        
        while True:
            choice = input(f"\n{Colors.BOLD}Номер типа [1]: {Colors.ENDC}").strip()
            if not choice:
                return self.COMMIT_TYPES[0]
            
            if choice.isdigit() and 1 <= int(choice) <= len(self.COMMIT_TYPES):
                return self.COMMIT_TYPES[int(choice) - 1]
            
            print(f"{Colors.FAIL}✖ Ошибка: Введите число от 1 до {len(self.COMMIT_TYPES)}{Colors.ENDC}")

    def get_commit_details(self, selected_type: dict) -> Tuple[str, str, str, str, bool]:
        """Сбор данных для коммита."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}--- Детали коммита ---{Colors.ENDC}")
        
        scope = input(f"{Colors.BLUE}Область (Scope){Colors.ENDC} {Colors.DIM}[опционально]: {Colors.ENDC}").strip()
        
        # Запрос описания с валидацией длины
        while True:
            desc = input(f"{Colors.BLUE}Краткое описание{Colors.ENDC} {Colors.FAIL}*{Colors.ENDC}: ").strip()
            if not desc:
                print(f"{Colors.FAIL}✖ Описание не может быть пустым!{Colors.ENDC}")
                continue
            if len(desc) > 72:
                print(f"{Colors.WARNING}⚠ Внимание: Длина описания {len(desc)} символов. Рекомендуется до 72.{Colors.ENDC}")
            break

        is_breaking = input(f"{Colors.WARNING}Это ломающее изменение (Breaking Change)? [y/N]: {Colors.ENDC}").strip().lower() in ['y', 'yes', 'да', 'д']
        
        body = input(f"{Colors.BLUE}Подробное описание (Body){Colors.ENDC} {Colors.DIM}[опционально]: {Colors.ENDC}").strip()
        footer = input(f"{Colors.BLUE}Связанные задачи (Footer){Colors.ENDC} {Colors.DIM}[например: Closes #123]: {Colors.ENDC}").strip()

        return scope, desc, body, footer, is_breaking

    def run(self):
        """Запуск утилиты."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}🚀 Git Commit Helper (Conventional Commits){Colors.ENDC}\n")
        
        try:
            self.check_environment()
            
            selected_type = self.get_commit_type()
            scope, desc, body, footer, is_breaking = self.get_commit_details(selected_type)

            # Формирование заголовка коммита
            scope_str = f"({scope})" if scope else ""
            breaking_str = "!" if is_breaking else ""
            commit_title = f"{selected_type['type']}{scope_str}{breaking_str}: {selected_type['emoji']} {desc}"

            # Формирование аргументов команды
            git_args = ['git', 'commit', '-m', commit_title]
            
            if body:
                git_args.extend(['-m', body])
            if footer:
                git_args.extend(['-m', footer])

            # Отображение превью
            print(f"\n{Colors.HEADER}{Colors.BOLD}--- Превью коммита ---{Colors.ENDC}")
            print(f"{Colors.GREEN}{commit_title}{Colors.ENDC}")
            if body: print(f"{Colors.DIM}{body}{Colors.ENDC}")
            if footer: print(f"{Colors.DIM}{footer}{Colors.ENDC}")
            print("-" * 22)

            confirm = input(f"\n{Colors.BOLD}Создать этот коммит? [Y/n]: {Colors.ENDC}").strip().lower()
            if confirm in ['', 'y', 'yes', 'да', 'д']:
                code, stdout, stderr = GitHelper.run(git_args)
                if code == 0:
                    print(f"\n{Colors.GREEN}✔ Коммит успешно создан!{Colors.ENDC}")
                else:
                    print(f"\n{Colors.FAIL}✖ Ошибка при создании коммита:{Colors.ENDC}")
                    print(stderr)
            else:
                print(f"{Colors.WARNING}⚠ Коммит отменен пользователем.{Colors.ENDC}")

        except KeyboardInterrupt:
            print(f"\n\n{Colors.WARNING}⚠ Операция прервана пользователем.{Colors.ENDC}")
            sys.exit(0)

if __name__ == "__main__":
    app = ConventionalCommitCLI()
    app.run()
