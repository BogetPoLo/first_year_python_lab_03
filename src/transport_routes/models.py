from dataclasses import dataclass
from datetime import datetime, date

from transport_routes.errors import ErrorIncorrectEntity, ErrorDuplicateId, ErrorObjectNotFound


@dataclass()
class CatalogItem:
    id: str  # id элемента
    name: str  # Название маршрута
    category: str  # Категория
    data: str  # Дата, пользователь сам ее устанавливает
    start_journey: str  # Начальная точка маршрута
    end_journey: str  # Конечная точка маршрута

    def __post_init__(self) -> None:
        """Валидирует данные
        Args:
            None
        Returns:
            None
        Raises:
            ErrorIncorrectEntity - Ошибка неверных переданных данных (неверная сущность)"""
        # Проверяет, что все данные, должны быть str
        if not all([
            True if isinstance(item, str) else False
            for item in (self.id, self.name, self.category, self.data, self.start_journey, self.end_journey)
        ]):
            raise ErrorIncorrectEntity("Есть неправильный тип данных, должны быть только str")

        # Проверяет, поле пустая строка или состоящая только из пробелов
        if not all([
            True if item.strip() != "" else False
            for item in (self.id, self.name, self.category, self.data, self.start_journey, self.end_journey)
        ]):
            raise ErrorIncorrectEntity("id указан как пустая строка или состоящая только из пробелов")

        # Проверка формата времени у data
        formats: tuple[str, ...] = ("%d-%m-%Y", "%d.%m.%Y", "%d/%m/%Y")
        d: date | None = None
        for format in formats:
            try:
                d: date = datetime.strptime(self.data, format).date()
            except ValueError:
                continue
            else:
                break
        if d is None:
            raise ErrorIncorrectEntity(
                f"Не правильный формат. Должен быть: %d-%m-%Y, %d.%m.%Y, %d/%m/%Y. У тебя: {self.data}."
            )


@dataclass()
class DataCategory:
    all_element: dict[str, CatalogItem]  # все сущности
    category_id: dict[str, set[str]]  # все id по категориям
    name_id: dict[str, set[str]]  # все названия и их id
    output_category_or_name: dict[str, CatalogItem]  # для вывода категории или названия


    def make_id(self, category: str) -> str:
        """Создает id если его не указал пользователь
            Args:
                category - название категории
            Returns:
                id - личный идентификатор"""
        count_element: int = len(self.all_element)
        while True:
            id: str = f"{count_element}-{category[0].upper()}"
            if id not in self.all_element:
                return id
            count_element += 1


    def add(self, args) -> str:
        """Создание новой сущности
        Args:
            name - название маршрута
            category - категория маршрута
            data - дата добавления
            start_journey - начало маршрута
            end_journey - конец маршрута
        Returns:
            str - строка с сущностью"""
        id: str; name: str; category: str; data: str; start_journey: str; end_journey: str
        id, name, category, data, start_journey, end_journey = args

        # Проверяет на дубликат id
        if not (id is None) and id in self.all_element:
            raise ErrorDuplicateId(f"Уже существует такой id: {id}")

        if id is None:
            id = self.make_id(category)

        # Создание новой сущности
        item: CatalogItem = CatalogItem(id, name, category, data, start_journey, end_journey)

        # Добавления в словари
        self.all_element[id] = item

        # Если нет такой категории, тогда создается новый ключ, со значениями
        if category not in self.category_id:
            self.category_id[category] = set()
        # Если нет такого названия пути, тогда создается новый ключ, со значениями
        if name not in self.name_id:
            self.name_id[name] = set()

        self.name_id[name].add(id)
        self.category_id[category].add(id)

        return f"Успешно добавили сущность: {self.creating_a_string(item)}"


    def get(self, id: str) -> str:
        """Возвращает сущность по id
        Args:
            id - личный не повторяющийся идентификатор маршрута
        Returns:
            str - строка с сущностью
        Raises:
            ErrorObjectNotFound - Ошибка объект не найден"""

        if id not in self.all_element:
            raise ErrorObjectNotFound(f"Такого id нет в базе данных: {id}")
        return f"Успешно найдена сущность: {self.creating_a_string(self.all_element[id])}"


    def remove(self, id: str) -> str:
        """
        Удаляет сущность по id
        Args:
            id - личный не повторяющийся идентификатор маршрута
        Returns:
            Сущность
        Raises:
            ErrorObjectNotFound - Ошибка объект не найден
        """
        if id not in self.all_element:
            raise ErrorObjectNotFound(f"Такого id нет в базе данных: {id}")
        del_item: CatalogItem = self.all_element.pop(id)

        # Удаляет из других словарей
        self.category_id[del_item.category].remove(del_item.id)
        self.name_id[del_item.name].remove(del_item.id)

        # Если множество стало пустым, тогда удаляется ключ
        if len(self.category_id[del_item.category]) == 0:
            del self.category_id[del_item.category]
        if len(self.name_id[del_item.name]) == 0:
            del self.name_id[del_item.name]

        return f"Успешно удаленна сущность - {self.creating_a_string(del_item)}"


    def find_by_category(self, category: str):
        """Делает поиск категории (слово может быть полным или частью)
        и выводит все сущности, которые есть в этой категории
        Args:
            category - категория маршрута
        Returns:
            Все сущности этой категории
        Raises:
            ErrorObjectNotFound - Ошибка объект не найден"""
        try:
            self.search_for_subordinate_entities(category, self.category_id)
        except ErrorIncorrectEntity:
            raise ErrorIncorrectEntity(f"Не существует такой категории пути: {category}")


    def find_by_name(self, name: str) -> None:
        """Делает поиск по названию (слово может быть полным или частью)
        и выводит название, у которого есть самое лучшее совпадение
        Args:
            name - название маршрута
        Returns:
            Все сущности этой категории
        Raises:
            ErrorObjectNotFound - Ошибка объект не найден"""
        try:
            self.search_for_subordinate_entities(name, self.name_id)
        except ErrorIncorrectEntity:
            raise ErrorIncorrectEntity(f"Не существует такого названия пути: {name}")


    def search_for_subordinate_entities(self, given: str, set_id: dict[str, set[int]]) -> None:
        """По переданному названию и объекту, делает поиск по бд и возвращает все подходящие сущности
        Args:
            given - слово, которое нужно найти(или самое подходящие)
            set_id - словарь, где ключ, это название пути или категория, а значение - id
        Returns:
            Возвращает список со всеми сущностями, которые подходят
        Raises:
            ErrorObjectNotFound - Ошибка объект не найден"""
        # Ищет самую подходящую категорию
        most_suitable: list[tuple[int, str]] = []
        for key in set_id:
            level: int | None = self.most_similar_word(given.lower(), key.lower())
            if level is None:
                continue
            most_suitable.append((level, key))

        most_suitable.sort(key=lambda x: (x[0], x[1]))

        if not most_suitable:
            raise ErrorIncorrectEntity

        most_suitable: str = most_suitable[0][1]

        for id in sorted(set_id[most_suitable]):
            self.output_category_or_name[id] = self.all_element[id]


    def most_similar_word(self, given: str, need: str) -> int | None:
        """Говорит насколько похожи слова.
        1 - одинаковы, 2 - начинается с этого слова, 3 - есть в слове
        Args:
            given - вводимо слово
            need - с чем сравнивать
        Returns:
            int"""
        # Поиск самого подходящего слова
        if given == need:
            return 1
        elif need.startswith(given):
            return 2
        elif (given in need) or (need in given):
            return 3
        return None


    def __len__(self) -> int:
        """Возвращает количество элементов
        Args:
            None
        Returns:
            int - количество элементов"""
        return len(self.all_element)


    def __iter__(self):
        """Делает генератор всех сущностей, по возрастанию id
        Args:
            None
        Returns:
            CatalogItem"""
        for _, item in sorted(self.all_element.items()):
            yield self.creating_a_string(item)


    def __contains__(self, id: str) -> bool:
        """Возвращает True если id сущности есть и False если нет
        Args:
            id - личный не повторяющийся идентификатор маршрута
        Returns:
            True/False"""
        return id in self.all_element



    def creating_a_string(self, obj: CatalogItem) -> str:
        """Возвращает кортеж всех полей сущности
        Args:
            obj - объект
        Returns:
            tuple(id, name, category, data, start_journey, end_journey)"""
        return (f""
                f"id: {obj.id}, "
                f"name: {obj.name}, "
                f"category: {obj.category}, "
                f"data: {obj.data}, "
                f"start_journey: {obj.start_journey}, "
                f"end_journey: {obj.end_journey}"
                )