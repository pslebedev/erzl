import os
import yaml
from pathlib import Path
from typing import Any, List, Dict
import textwrap


class YAMLFileFinder:
    """Класс для поиска YAML файлов в папке tests"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.path.dirname(os.path.abspath(__file__))
        self.tests_dir = os.path.join(self.project_root, 'tests')

    def find_yaml_files(self) -> List[str]:
        """Найти все YAML файлы в папке tests"""
        if not os.path.exists(self.tests_dir):
            return []

        yaml_files = []

        try:
            # Поиск .yaml и .yml файлов в tests
            for pattern in ["**/*.yaml", "**/*.yml"]:
                for file_path in Path(self.tests_dir).glob(pattern):
                    if file_path.is_file():
                        yaml_files.append(str(file_path))

        except Exception as e:
            print(f"Ошибка при поиске файлов: {e}")

        return sorted(yaml_files)


class TestCaseVisualizer:
    """
    Класс для красивого визуального отображения тест-кейсов
    """

    def __init__(self, max_width: int = 100):
        self.max_width = max_width
        self.colors = {
            'header': '\033[1;36m',  # Бирузовый
            'success': '\033[1;32m',  # Зеленый
            'warning': '\033[1;33m',  # Желтый
            'error': '\033[1;31m',  # Красный
            'info': '\033[1;34m',  # Синий
            'reset': '\033[0m',  # Сброс
        }

    def _colorize(self, text: str, color: str) -> str:
        """Добавить цвет к тексту"""
        return f"{self.colors.get(color, '')}{text}{self.colors['reset']}"

    def _wrap_text(self, text: str, width: int) -> List[str]:
        """Обернуть текст с переносами, возвращает список строк"""
        if not text:
            return [""]

        # Очищаем текст от лишних пробелов
        text = ' '.join(str(text).split())

        # Используем textwrap для переносов
        return textwrap.wrap(text, width=width)

    def _calculate_box_width(self, title: str, content_lines: List[str]) -> int:
        """Рассчитать ширину бокса на основе содержимого"""
        max_content_width = max(len(line) for line in content_lines) if content_lines else 0
        title_width = len(title)
        return max(max_content_width, title_width) + 4  # +4 для границ и отступов

    def _create_box(self, title: str, content: str, color: str = "info") -> str:
        """Создать красивый блок с рамкой"""
        content_lines = content.split('\n') if content else [""]
        box_width = self._calculate_box_width(title, content_lines)

        # Верхняя граница
        top_border = "┌" + "─" * (box_width - 2) + "┐"

        # Заголовок (центрируем)
        title_padding = box_width - 4 - len(title)
        left_padding = title_padding // 2
        right_padding = title_padding - left_padding
        title_line = f"│ {self._colorize(' ' * left_padding + title + ' ' * right_padding, color)} │"

        # Разделитель
        separator = "├" + "─" * (box_width - 2) + "┤"

        # Содержимое (выравниваем по левому краю)
        content_lines_formatted = []
        for line in content_lines:
            padded_line = line + " " * (box_width - 4 - len(line))
            content_lines_formatted.append(f"│ {padded_line} │")

        # Нижняя граница
        bottom_border = "└" + "─" * (box_width - 2) + "┘"

        # Собираем все вместе
        box_lines = [top_border, title_line, separator] + content_lines_formatted + [bottom_border]
        return "\n".join(box_lines)

    def _create_metadata_box(self, title: str, items: List[str], color: str = "info") -> str:
        """Создать бокс для метаданных с правильным выравниванием"""
        if not items:
            return ""

        # Находим максимальную длину ключа для выравнивания
        max_key_length = 0
        formatted_items = []

        for item in items:
            if ':' in item:
                key, value = item.split(':', 1)
                max_key_length = max(max_key_length, len(key.strip()))

        # Форматируем элементы с выравниванием
        aligned_items = []
        for item in items:
            if ':' in item:
                key, value = item.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Выравниваем ключи
                aligned_key = key + ':' + ' ' * (max_key_length - len(key) + 2)

                # Обрабатываем значение с переносами
                if value:
                    wrapped_value = self._wrap_text(value, self.max_width - max_key_length - 10)
                    if wrapped_value:
                        aligned_items.append(f"{aligned_key} {wrapped_value[0]}")
                        for line in wrapped_value[1:]:
                            aligned_items.append(" " * (max_key_length + 3) + line)
                else:
                    aligned_items.append(f"{aligned_key} ")
            else:
                aligned_items.append(item)

        content = "\n".join(aligned_items)
        return self._create_box(title, content, color)

    def display_test_suite(self, file_path: str) -> str:
        """Отобразить весь тест-сьют в красивом формате"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except Exception as e:
            return f"❌ Ошибка загрузки файла: {e}"

        if not data:
            return "📝 Файл пуст"

        output = []
        relative_path = os.path.relpath(file_path, os.path.dirname(os.path.abspath(__file__)))

        # Заголовок файла
        output.append(self._create_box("ТЕСТ-СЬЮТ", relative_path, "header"))
        output.append("")

        # Метаданные сьюта
        output.extend(self._display_suite_metadata(data))
        output.append("")

        # Тест-кейсы
        if 'test_cases' in data and data['test_cases']:
            output.extend(self._display_test_cases(data['test_cases']))
        else:
            output.append(self._create_box("ТЕСТ-КЕЙСЫ", "Нет тест-кейсов", "warning"))

        return "\n".join(output)

    def _display_suite_metadata(self, data: dict) -> List[str]:
        """Отобразить метаданные тест-сьюта"""
        output = []

        meta_fields = {
            'suite_name': 'Название сьюта',
            'suite_id': 'ID сьюта',
            'description': 'Описание',
            'created_at': 'Создан',
            'status': 'Статус',
            'created_by': 'Автор'
        }

        meta_items = []
        for field, label in meta_fields.items():
            if field in data and data[field]:
                value = data[field]
                meta_items.append(f"{label}: {value}")

        if meta_items:
            output.append(self._create_metadata_box("МЕТАДАННЫЕ", meta_items, "info"))

        return output

    def _display_test_cases(self, test_cases: List[dict]) -> List[str]:
        """Отобразить все тест-кейсы"""
        output = []

        # Общее количество кейсов
        total_cases = len(test_cases)
        output.append(self._create_box("ТЕСТ-КЕЙСЫ", f"Всего кейсов: {total_cases}", "success"))
        output.append("")

        # Отображаем каждый тест-кейс
        for i, test_case in enumerate(test_cases, 1):
            output.extend(self._display_single_test_case(test_case, i))
            if i < len(test_cases):  # Добавляем отступ между кейсами, но не после последнего
                output.append("")

        return output

    def _display_single_test_case(self, test_case: dict, case_num: int) -> List[str]:
        """Отобразить один тест-кейс"""
        output = []

        # Заголовок тест-кейса
        title = test_case.get('title', 'Без названия')
        case_header = f"КЕЙС #{case_num}: {title}"
        output.append(self._create_box(case_header, "", "header"))
        output.append("")

        # Основная информация о кейсе
        basic_info = self._format_basic_test_case_info(test_case)
        if basic_info:
            output.append(basic_info)
            output.append("")

        # Pre-conditions
        pre_conditions = self._format_pre_conditions(test_case.get('pre-conditions', []))
        if pre_conditions:
            output.append(pre_conditions)
            output.append("")

        # Steps
        steps = self._format_steps(test_case.get('steps', []))
        if steps:
            output.append(steps)

        return output

    def _format_basic_test_case_info(self, test_case: dict) -> str:
        """Форматировать основную информацию о тест-кейсе"""
        info_items = []

        if test_case.get('case_id'):
            # ID обрабатываем отдельно, так как он может быть длинным
            case_id = test_case['case_id']
            wrapped_id = self._wrap_text(case_id, 60)
            if wrapped_id:
                info_items.append(f"ID: {wrapped_id[0]}")
                for line in wrapped_id[1:]:
                    info_items.append("   " + line)

        if test_case.get('priority'):
            priority = test_case['priority']
            color = "error" if priority == "high" else "warning" if priority == "medium" else "success"
            priority_text = self._colorize(priority.upper(), color)
            info_items.append(f"Приоритет: {priority_text}")

        if test_case.get('description'):
            desc = test_case['description']
            wrapped_desc = self._wrap_text(desc, 70)
            if wrapped_desc:
                info_items.append(f"Описание: {wrapped_desc[0]}")
                for line in wrapped_desc[1:]:
                    info_items.append("          " + line)

        if info_items:
            return self._create_metadata_box("ОСНОВНАЯ ИНФОРМАЦИЯ", info_items, "info")
        return ""

    def _format_pre_conditions(self, pre_conditions: List[dict]) -> str:
        """Форматировать предусловия"""
        if not pre_conditions:
            return ""

        pre_cond_lines = []
        for j, condition in enumerate(pre_conditions, 1):
            action = condition.get('action', '')
            if action:
                wrapped_action = self._wrap_text(action, 70)
                if wrapped_action:
                    pre_cond_lines.append(f"{j}. {wrapped_action[0]}")
                    for line in wrapped_action[1:]:
                        pre_cond_lines.append("   " + line)

        if pre_cond_lines:
            return self._create_box("ПРЕДУСЛОВИЯ", "\n".join(pre_cond_lines), "warning")
        return ""

    def _format_steps(self, steps: List[dict]) -> str:
        """Форматировать шаги тестирования"""
        if not steps:
            return ""

        steps_content = []
        for j, step in enumerate(steps, 1):
            step_lines = []

            # Action
            action = step.get('action', '')
            if action:
                wrapped_action = self._wrap_text(action, 65)
                if wrapped_action:
                    step_lines.append(f"🔹 Действие: {wrapped_action[0]}")
                    for line in wrapped_action[1:]:
                        step_lines.append("           " + line)

            # Expected Result
            expected = step.get('expected_result', '')
            if expected:
                wrapped_expected = self._wrap_text(expected, 65)
                if wrapped_expected:
                    step_lines.append(f"✅ Ожидаемый результат: {wrapped_expected[0]}")
                    for line in wrapped_expected[1:]:
                        step_lines.append("                         " + line)

            if step_lines:
                steps_content.append(f"ШАГ {j}:")
                steps_content.extend(step_lines)
                if j < len(steps):  # Добавляем разделитель между шагами
                    steps_content.append("─" * 50)

        if steps_content:
            return self._create_box("ШАГИ ТЕСТИРОВАНИЯ", "\n".join(steps_content), "success")
        return ""


# ... (остальные функции find_all_yaml_files, show_yaml_file и т.д. остаются без изменений)

def find_all_yaml_files():
    """Найти и показать все YAML файлы в проекте"""
    finder = YAMLFileFinder()
    files = finder.find_yaml_files()

    if not files:
        print("📭 YAML файлы не найдены в папке tests")
        return

    print(f"📁 Найдено YAML файлов: {len(files)}")
    for file_path in files:
        relative_path = os.path.relpath(file_path, os.path.dirname(os.path.abspath(__file__)))
        print(f"📄 {relative_path}")


def show_yaml_file(filename: str):
    """Показать содержимое конкретного YAML файла"""
    project_root = os.path.dirname(os.path.abspath(__file__))

    # Пробуем разные пути
    possible_paths = [
        os.path.join(project_root, 'tests', filename),
        os.path.join(project_root, 'tests', filename + '.yaml'),
        os.path.join(project_root, 'tests', filename + '.yml'),
        os.path.join(project_root, filename),
    ]

    file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            file_path = path
            break

    if not file_path:
        print(f"❌ Файл не найден: {filename}")
        print("💡 Ищите в папке tests или укажите полный путь")
        return

    visualizer = TestCaseVisualizer()
    result = visualizer.display_test_suite(file_path)
    print(result)


def show_all_yaml_files():
    """Показать содержимое всех YAML файлов"""
    finder = YAMLFileFinder()
    files = finder.find_yaml_files()

    if not files:
        print("📭 YAML файлы не найдены в папке tests")
        return

    visualizer = TestCaseVisualizer()

    for file_path in files:
        print("\n" + "=" * 120)
        result = visualizer.display_test_suite(file_path)
        print(result)
        print("=" * 120)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        print("Использование:")
        print("  python yaml_utils.py find     - найти все YAML файлы")
        print("  python yaml_utils.py show-all - показать все YAML файлы полностью")
        print("  python yaml_utils.py show <file> - показать конкретный файл")
    elif sys.argv[1] == "find":
        find_all_yaml_files()
    elif sys.argv[1] == "show-all":
        show_all_yaml_files()
    elif sys.argv[1] == "show" and len(sys.argv) > 2:
        show_yaml_file(sys.argv[2])
    else:
        print("Неизвестная команда")