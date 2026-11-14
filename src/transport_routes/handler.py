from copy import deepcopy
from typing import Any
from dataclasses import asdict
from rich.table import Table
from rich.text import Text
from rich import box, markup
from rich.console import Console
import json

from transport_routes.models import DataCategory
from transport_routes.errors import ErrorCorruptedFile, ErrorUnsupportedFormatVersion

console: Console = Console()


def make_object() -> DataCategory:
    """Создает объект класса DataCategory
    Args:
        None
    Returns:
        DataCategory"""
    return DataCategory({}, {}, {}, {})


def method_executor(name_method: str, obj: DataCategory, args: Any):
    """Функция вызывает другие функции, загрузка, выгрузка файла json, вызывает методы DataCategory
    Args:
        name_method - название метода
        obj - объект DataCategory
        args - аргументы, которые передал пользователь
    Returns:
        None"""
    all_methods = {
        "add": obj.add,
        "get": obj.get,
        "remove": obj.remove,
        "len": lambda _: len(obj),
        "contains": obj.__contains__
    }

    format_version: int = 0

    try:
        read_file = read_json()
        format_version = write_class(read_file, obj)
    except json.JSONDecodeError:  # Некорректный файл json
        raise ErrorCorruptedFile("Файл json был некорректен")
    except KeyError:
        raise ErrorUnsupportedFormatVersion("Пропущены обязательные поля в файле JSON")
    except FileNotFoundError:  # файла не было, нужно создать новый
        pass

    if name_method == "iter":
        output_logs(obj.all_element)
    elif name_method == "find_by_name":
        obj.find_by_name(args)
        output_logs(obj.output_category_or_name)
    elif name_method == "find_by_category":
        obj.find_by_category(args)
        output_logs(obj.output_category_or_name)
    else:
        console.print(all_methods[name_method](args), markup=False)


    if name_method in {"add", "remove"}:
        format_version += 1

    write_json(format_version, obj)


def output_logs(di) -> None:
    """Выводит маршруты таблицей в порядке ID
    Args:
        obj - объект DataCategory
    Returns:
        None"""
    table = Table(
        box=box.SIMPLE,
        header_style="bold cyan",
        padding=(0, 1),
    )

    table.add_column("ID", style="cyan")
    table.add_column("Название")
    table.add_column("Категория")
    table.add_column("Год", justify="right")
    table.add_column("Откуда")
    table.add_column("Куда")

    for route_id in sorted(di):
        item = di[route_id]
        table.add_row(
            Text(item.id),
            Text(item.name),
            Text(item.category),
            item.data[-4:],
            Text(item.start_journey),
            Text(item.end_journey),
        )

    console.print(table)


def write_json(format_version: int, obj: DataCategory) -> None:
    """Запись в json файл
    Args:
        obj - DataCategory
        format_version - число изменений в файле
    Returns:
        None"""
    res: dict[str, dict[str, str]] = {}

    for key, value in obj.all_element.items():
        res[key] = asdict(value)

    write_element: dict[str, int | dict[str, dict[str, str]]] = {
        "format_version": format_version,
        "all_element": res
    }

    with open("database.json", mode="w", encoding="utf8") as wfile:
        json.dump(
            write_element,
            wfile,
            ensure_ascii=False,
            indent=4
        )


def read_json() -> dict[str, int | dict[str, dict[str, str]]]:
    """Читает данные из json файла
    Args:
        None
    Returns:
        словарь из json файла"""
    with open("database.json", mode="r", encoding="utf8") as rfile:
        return json.load(rfile)


def write_class(dict_element: dict, obj: DataCategory) -> int:
    """Записывает поля, которые были в json
    Args:
        obj - DataCategory
        dict_element - поля загруженные из json
    Returns:
        int - число из format_version"""
    format_version: int = dict_element["format_version"]
    all_element: dict[int, str] = dict_element["all_element"]

    load_catalog: DataCategory = deepcopy(obj)

    for value in all_element.values():
        if value.keys() != {"id", "name", "category", "data", "start_journey", "end_journey"}:
            raise KeyError

        load_catalog.add((
            value["id"],
            value["name"],
            value["category"],
            value["data"],
            value["start_journey"],
            value["end_journey"]
        ))

    obj.all_element = load_catalog.all_element
    obj.category_id = load_catalog.category_id
    obj.name_id = load_catalog.name_id

    return format_version
