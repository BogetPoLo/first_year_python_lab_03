import copy
import dataclasses
import io
import json
from pathlib import Path

import pytest
from rich.console import Console

import transport_routes.errors as errors
import transport_routes.handler as handler
import transport_routes.models as models


FIRST_ROUTE: tuple[str, str, str, str, str, str] = (
    "1-А", "Северный", "Автобус", "12.11.2025", "Вокзал", "Парк"
)
SECOND_ROUTE: tuple[str, str, str, str, str, str] = (
    "2-А", "Южный", "Автобус", "13.11.2025", "Парк", "Школа"
)
THIRD_ROUTE: tuple[str, str, str, str, str, str] = (
    "3-Т", "Кольцевой", "Трамвай", "14.11.2025", "Школа", "Вокзал"
)


def test_create_route() -> None:
    """Проверяет создание маршрута и сохранение его полей"""
    item: models.CatalogItem = models.CatalogItem(*FIRST_ROUTE)

    assert dataclasses.astuple(item) == FIRST_ROUTE


@pytest.mark.parametrize("name, data", [
    ("   ", "12.11.2025"),
    ("Северный", "31.02.2025"),
], ids=["пустое название", "неверная дата"])
def test_invalid_route(name: str, data: str) -> None:
    """Проверяет ошибку при пустом названии или неверной дате"""
    with pytest.raises(errors.ErrorIncorrectEntity):
        models.CatalogItem("1-А", name, "Автобус", data, "Вокзал", "Парк")


def test_add_get_remove() -> None:
    """Проверяет добавление, получение и удаление маршрута по ID"""
    catalog: models.DataCategory = handler.make_object()
    catalog.add(FIRST_ROUTE)

    assert len(catalog) == 1
    assert "1-А" in catalog
    assert "name: Северный," in catalog.get("1-А")

    catalog.remove("1-А")

    assert len(catalog) == 0
    assert "1-А" not in catalog
    assert catalog.category_id == {}
    assert catalog.name_id == {}

    with pytest.raises(errors.ErrorObjectNotFound):
        catalog.remove("1-А")


def test_duplicate_id() -> None:
    """Проверяет ошибку при добавлении повторного ID"""
    catalog: models.DataCategory = handler.make_object()
    catalog.add(FIRST_ROUTE)

    with pytest.raises(errors.ErrorDuplicateId):
        catalog.add(("1-А", *SECOND_ROUTE[1:]))

    assert len(catalog) == 1
    assert catalog.all_element["1-А"] == models.CatalogItem(*FIRST_ROUTE)


def test_add_without_id() -> None:
    """Проверяет генерацию ID, когда первый предложенный ID уже занят"""
    catalog: models.DataCategory = handler.make_object()
    catalog.add(FIRST_ROUTE)

    catalog.add((None, *SECOND_ROUTE[1:]))

    assert set(catalog.all_element) == {"1-А", "2-А"}
    assert catalog.all_element["2-А"] == models.CatalogItem(*SECOND_ROUTE)


def test_iteration_order() -> None:
    """Проверяет порядок итерации по строковым ID"""
    catalog: models.DataCategory = handler.make_object()
    catalog.add(SECOND_ROUTE)
    catalog.add(("10-Т", *THIRD_ROUTE[1:]))
    catalog.add(FIRST_ROUTE)

    route_ids: list[str] = [
        route.split(", ", 1)[0]
        for route in catalog
    ]

    assert route_ids == ["id: 1-А", "id: 10-Т", "id: 2-А"]


@pytest.mark.parametrize("method, query, expected_ids", [
    ("iter", None, {"1-А", "2-А", "3-Т"}),
    ("find_by_category", "Автобус", {"1-А", "2-А"}),
    ("find_by_name", "сЕвЕрНыЙ", {"1-А"}),
])
def test_routes_table(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        method: str,
        query: str | None,
        expected_ids: set[str],
) -> None:
    """Проверяет заголовки и строки таблицы для итерации и обоих видов поиска"""
    monkeypatch.chdir(tmp_path)
    catalog: models.DataCategory = handler.make_object()
    catalog.add(THIRD_ROUTE)
    catalog.add(SECOND_ROUTE)
    catalog.add(FIRST_ROUTE)
    handler.write_json(1, catalog)

    # Перехватывает вывод Rich в текстовый буфер
    stream: io.StringIO = io.StringIO()
    console: Console = Console(file=stream, width=120, color_system=None)
    monkeypatch.setattr(handler, "console", console)

    loaded_catalog: models.DataCategory = handler.make_object()
    handler.method_executor(method, loaded_catalog, query)
    output: str = stream.getvalue()

    headers: tuple[str, ...] = ("ID", "Название", "Категория", "Год", "Откуда", "Куда")
    assert all(header in output for header in headers)

    # Проверяет, что в таблицу попали только нужные маршруты
    printed_ids: set[str] = {
        route_id for route_id in catalog.all_element if route_id in output
    }
    assert printed_ids == expected_ids

    if method != "iter":
        assert set(loaded_catalog.output_category_or_name) == expected_ids


def test_json_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Проверяет сохранение и загрузку маршрутов, индексов и версии"""
    monkeypatch.chdir(tmp_path)
    catalog: models.DataCategory = handler.make_object()
    catalog.add(FIRST_ROUTE)
    catalog.add(THIRD_ROUTE)

    handler.write_json(1, catalog)

    restored_catalog: models.DataCategory = handler.make_object()
    format_version: int = handler.write_class(handler.read_json(), restored_catalog)

    assert format_version == 1
    assert restored_catalog == catalog


def test_corrupted_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Проверяет предметную ошибку при чтении поврежденного JSON"""
    monkeypatch.chdir(tmp_path)
    database: Path = tmp_path / "database.json"
    database.write_text('{"format_version": 1,', encoding="utf-8")
    catalog: models.DataCategory = handler.make_object()

    with pytest.raises(errors.ErrorCorruptedFile):
        handler.method_executor("len", catalog, None)


def test_failed_load_keeps_catalog(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Проверяет состояние каталога после ошибки во второй записи"""
    monkeypatch.chdir(tmp_path)
    catalog: models.DataCategory = handler.make_object()
    catalog.add(FIRST_ROUTE)
    original_catalog: models.DataCategory = copy.deepcopy(catalog)

    valid_record: dict[str, str] = dataclasses.asdict(models.CatalogItem(*SECOND_ROUTE))
    invalid_record: dict[str, str] = dataclasses.asdict(models.CatalogItem(*THIRD_ROUTE))
    invalid_record["data"] = "31.02.2025"

    document: dict[str, int | dict[str, dict[str, str]]] = {
        "format_version": 1,
        "all_element": {"2-А": valid_record, "3-Т": invalid_record},
    }
    database: Path = tmp_path / "database.json"
    database.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")

    with pytest.raises((errors.ErrorIncorrectEntity, errors.ErrorCorruptedFile)):
        handler.method_executor("len", catalog, None)

    assert catalog == original_catalog