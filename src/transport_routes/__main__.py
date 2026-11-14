from typing import Annotated
import typer

from transport_routes.handler import method_executor, make_object

app = typer.Typer()


@app.callback()
def main() -> None:
    pass


@app.command()
def add(
        name: Annotated[
            str,
            typer.Argument(help="Название маршрута")
        ],
        category: Annotated[
            str,
            typer.Argument(help="Категория маршрута")
        ],
        data: Annotated[
            str,
            typer.Argument(help="Дата добавления маршрута")
        ],
        start_journey: Annotated[
            str,
            typer.Argument(help="Точка отправление маршрута")
        ],
        end_journey: Annotated[
            str,
            typer.Argument(help="Точка завершение маршрута")
        ],
        id: Annotated[
            str | None,
            typer.Argument(help="личный идентификатор")
        ] = None
) -> None:
    """Добавляет новый маршрут
    Args:
        name - название маршрута
        category - категория маршрута
        data - дата добавления
        start_journey - начало маршрута
        end_journey - конец маршрута
    Returns:
        None"""
    method_executor("add", make_object(), (id, name, category, data, start_journey, end_journey))


@app.command()
def get(
        id: Annotated[
            str | None,
            typer.Argument(help="Id по которому будет выводится информация про элемент")
        ]
) -> None:
    """Выводит информацию по id
    Args:
        id - личный не повторяющийся идентификатор маршрута
    Returns:
        None"""
    method_executor("get", make_object(), id)


@app.command()
def remove(
        id: Annotated[
            str | None,
            typer.Argument(help="Удаляет элемента по id")
        ]
) -> None:
    """Удаляет элемента по id
    Args:
        id - личный не повторяющийся идентификатор маршрута
    Returns:
        None"""
    method_executor("remove", make_object(), id)


@app.command()
def find_by_category(
        category: Annotated[
            str | None,
            typer.Argument(help="Выводит всю информацию по этой категории")
        ]
) -> None:
    """Выводит всю информацию по этой категории
    Args:
        category - категория маршрутов
    Returns:
        None"""
    method_executor("find_by_category", make_object(), category)


@app.command()
def find_by_name(
        query: Annotated[
            str | None,
            typer.Argument(help="Делает поиск по названию и выводит информацию")
        ]
) -> None:
    """Выводит всю информацию по этому названию
    Args:
        query - название маршрута
    Returns:
        None"""
    method_executor("find_by_name", make_object(), query)


@app.command()
def len() -> None:
    """Выводит количество сущностей
    Args:
        None
    Returns:
        None"""
    obj = make_object()
    method_executor("len", obj, None)


@app.command()
def iter() -> None:
    """Выводит все элементы
    Args:
        None
    Returns:
        None"""
    obj = make_object()
    method_executor("iter", obj, obj)


@app.command()
def contains(
        id: Annotated[
            str | None,
            typer.Argument(help="Проверяет, есть ли id в json-файле или нет")
        ]
) -> None:
    """Проверяет, есть ли id в json-файле или нет
    Args:
        id - личный не повторяющийся идентификатор маршрута
    Returns:
        None"""
    obj = make_object()
    method_executor("contains", obj, id)


if __name__ == "__main__":
    app()
