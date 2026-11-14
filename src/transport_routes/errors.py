class CatalogError(Exception):
    """Родительский класс всех ошибок"""
    pass


class ErrorIncorrectEntity(CatalogError):
    """Ошибка неверных переданных данных (неверная сущность)"""
    pass


class ErrorDuplicateId(CatalogError):
    """Ошибка дубликатов id"""
    pass


class ErrorObjectNotFound(CatalogError):
    """Ошибка объект не найден"""
    pass


class ErrorUnsupportedFormatVersion(CatalogError):
    """Ошибка неподдерживаемая версия формата"""
    pass


class ErrorCorruptedFile(CatalogError):
    """Ошибка поврежденный файл"""
    pass