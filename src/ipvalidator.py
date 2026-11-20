"""Проверка и поиск IPv6-адресов.

Модуль содержит регулярные выражения для:

* проверки канонической записи IPv6 по RFC 5952;
* проверки IPv6 с идентификатором зоны по RFC 4007;
* поиска адресов в тексте, файле и на веб-странице.
"""

from __future__ import annotations

import re
from functools import lru_cache
from os import PathLike
from pathlib import Path

import requests

__all__ = [
    "find_ipv6",
    "find_ipv6_in_file",
    "find_ipv6_in_url",
    "find_ipv6_zoned",
    "is_valid_ipv6",
    "is_valid_ipv6_zoned",
]


def _consecutive_zeros(hextets: list[str]) -> int:
    """Возвращает длину самого длинного прогона нулевых гексетов."""
    longest = 0
    current = 0
    for hextet in hextets:
        if hextet == "0":
            current += 1
        else:
            longest = max(longest, current)
            current = 0
    return max(longest, current)


# RFC 5952

_H_NZ = (  # ненулевой гексет: 1..ffff без ведущих нулей
    r"(?:(?:[1-9a-f])|(?:[1-9a-f][0-9a-f])|"
    r"(?:[1-9a-f][0-9a-f]{2})|(?:[1-9a-f][0-9a-f]{3}))"
)
_H_Z = r"(?:0)"  # нулевой гексет
_H = rf"(?:{_H_NZ}|{_H_Z})"  # любой гексет

# Тело IPv6. Альтернативы перебирают все допустимые варианты
# расположения "::" и гарантируют, что "::" заменяет не менее
# двух нулевых гексетов (RFC 5952, п. 4.2.2).
_IPBASE = (
    r"(?:"
    rf"(?:{_H}:){{7}}{_H}"
    rf"|(?:{_H}:){{0,5}}{_H_NZ}::"
    rf"|(?:{_H}:){{0,4}}{_H_NZ}::{_H_NZ}"
    rf"|(?:{_H}:){{0,3}}{_H_NZ}::{_H_NZ}(?::{_H})?"
    rf"|(?:{_H}:){{0,2}}{_H_NZ}::{_H_NZ}(?::{_H}){{0,2}}"
    rf"|(?:{_H}:)?{_H_NZ}::{_H_NZ}(?::{_H}){{0,3}}"
    rf"|{_H_NZ}::{_H_NZ}(?::{_H}){{0,4}}"
    rf"|::{_H_NZ}(?::{_H}){{0,5}}"
    r"|::"
    r")"
)

_IPV6 = re.compile(_IPBASE)


def is_valid_ipv6(address: str) -> bool:
    """Проверяет каноническую запись IPv6 по стандарту RFC 5952.

    Args:
        address: Строка, которую необходимо проверить.

    Returns:
        True, если строка является канонической записью IPv6, иначе False.

    Raises:
        TypeError: Адрес не является строкой.
    """
    if not isinstance(address, str):
        raise TypeError("Адрес должен быть строкой.")

    if not _IPV6.fullmatch(address):
        return False

    # Без "::" не должно быть прогонов из двух и более нулей.
    if "::" not in address:
        return _consecutive_zeros(address.split(":")) < 2

    # "::" должно заменять самый длинный прогон нулей, а при
    # равной длине — первый из них (RFC 5952, п. 4.2.1).
    left, right = address.split("::", maxsplit=1)
    left_groups = left.split(":") if left else []
    right_groups = right.split(":") if right else []
    compressed = 8 - len(left_groups) - len(right_groups)
    return (
        _consecutive_zeros(left_groups) < compressed
        and _consecutive_zeros(right_groups) <= compressed
    )


# RFC 4007

# Формат идентификатора зоны стандартом не определён, поэтому по
# умолчанию используется последовательность букв, цифр, "_", "." и "-".
_Z = r"(?:(?:%[A-Za-z0-9_.-]+)?)"

_IPV6_Z = re.compile(rf"({_IPBASE}){_Z}")


@lru_cache(maxsize=None)
def _ipv6_z_c(zone_pattern: str) -> re.Pattern[str]:
    """Компилирует шаблон IPv6 с пользовательским идентификатором зоны."""
    return re.compile(rf"({_IPBASE}){zone_pattern}")


def is_valid_ipv6_zoned(address: str, zone_pattern: str | None = None) -> bool:
    """Проверяет IPv6 по RFC 5952 с идентификатором зоны по RFC 4007.

    RFC 4007 не определяет формат строки идентификатора зоны, поэтому
    его можно задать собственным регулярным выражением.

    Args:
        address: Строка, которую необходимо проверить.
        zone_pattern: Регулярное выражение идентификатора зоны, которое
            добавляется к шаблону IPv6. По умолчанию используется
            ``(?:%[A-Za-z0-9_.-]+)?``; пустая строка также означает
            формат по умолчанию.

    Returns:
        True, если адрес соответствует RFC 5952 и RFC 4007, иначе False.

    Raises:
        TypeError: Адрес не является строкой.
        TypeError: Шаблон зоны не является строкой или None.
        ValueError: Регулярное выражение зоны некорректно.
    """
    if not isinstance(address, str):
        raise TypeError("Адрес должен быть строкой.")

    if zone_pattern is not None and not isinstance(zone_pattern, str):
        raise TypeError(
            "RE идентификатора зоны должен быть строкой либо None."
        )

    if zone_pattern:
        try:
            pattern = _ipv6_z_c(zone_pattern)
        except re.error as error:
            raise ValueError(
                f"RE идентификатора зоны некорректен: {error}"
            ) from error

        match = pattern.fullmatch(address)
        if match:
            return is_valid_ipv6(match.group(1))
        return False

    match = _IPV6_Z.fullmatch(address)
    if match:
        return is_valid_ipv6(match.group(1))
    return False


# Поиск IPv6-адресов в тексте.
#
# Границы не позволяют вырезать адрес из более длинного токена:
# слева и справа не должно быть символов адреса или зоны, а также
# точки с цифрой (часть записи IPv4, например ::ffff:192.168.0.1).
_SEARCH_LEFT = r"(?<![0-9A-Za-z:%_-])"
_SEARCH_RIGHT = r"(?![0-9A-Za-z:%_-]|\.[0-9])"

# В режиме поиска зона записывается лениво: это не даёт захватить
# точку в конце предложения, но сохраняет зоны вида eth0.100 и my-zone.
_Z_SEARCH = r"(?:(?:%[A-Za-z0-9_.-]+?))?"

_IPV6_SEARCH = re.compile(
    rf"{_SEARCH_LEFT}({_IPBASE}){_SEARCH_RIGHT}"
)
_IPV6_ZONED_SEARCH = re.compile(
    rf"{_SEARCH_LEFT}({_IPBASE}){_Z_SEARCH}{_SEARCH_RIGHT}"
)


@lru_cache(maxsize=None)
def _ipv6_z_search_c(zone_pattern: str) -> re.Pattern[str]:
    """Компилирует шаблон поиска IPv6 с пользовательской зоной."""
    return re.compile(
        rf"{_SEARCH_LEFT}({_IPBASE}){zone_pattern}{_SEARCH_RIGHT}"
    )


def find_ipv6(text: str) -> list[str]:
    """Находит в тексте канонические IPv6-адреса без идентификатора зоны.

    Args:
        text: Произвольный текст.

    Returns:
        Список найденных адресов в порядке их следования в тексте.

    Raises:
        TypeError: Текст не является строкой.
    """
    if not isinstance(text, str):
        raise TypeError("Текст должен быть строкой.")
    return [match.group(0) for match in _IPV6_SEARCH.finditer(text)]


def find_ipv6_zoned(
    text: str, zone_pattern: str | None = None
) -> list[str]:
    """Находит в тексте IPv6-адреса, в том числе с идентификатором зоны.

    Args:
        text: Произвольный текст.
        zone_pattern: Регулярное выражение идентификатора зоны. Если
            параметр не задан, используется формат по умолчанию
            ``(?:%[A-Za-z0-9_.-]+)?``. При пользовательском шаблоне
            адреса без зоны находятся только в том случае, если шаблон
            допускает пустое совпадение.

    Returns:
        Список найденных адресов в порядке их следования в тексте.

    Raises:
        TypeError: Текст или шаблон зоны имеют неверный тип.
        ValueError: Регулярное выражение зоны некорректно.
    """
    if not isinstance(text, str):
        raise TypeError("Текст должен быть строкой.")

    if zone_pattern is not None and not isinstance(zone_pattern, str):
        raise TypeError(
            "RE идентификатора зоны должен быть строкой либо None."
        )

    if not zone_pattern:
        pattern = _IPV6_ZONED_SEARCH
    else:
        try:
            pattern = _ipv6_z_search_c(zone_pattern)
        except re.error as error:
            raise ValueError(
                f"RE идентификатора зоны некорректен: {error}"
            ) from error

    return [match.group(0) for match in pattern.finditer(text)]


def _find(text: str, zoned: bool, zone_pattern: str | None) -> list[str]:
    """Выбирает режим поиска: с идентификаторами зон или без них."""
    if zoned or zone_pattern is not None:
        return find_ipv6_zoned(text, zone_pattern)
    return find_ipv6(text)


def find_ipv6_in_file(
    path: str | PathLike[str],
    *,
    zoned: bool = False,
    zone_pattern: str | None = None,
    encoding: str = "utf-8",
) -> list[str]:
    """Находит IPv6-адреса в текстовом файле.

    Args:
        path: Путь к файлу.
        zoned: Искать ли адреса с идентификаторами зон.
        zone_pattern: Пользовательское регулярное выражение зоны.
            Если параметр задан, поиск выполняется в режиме ``zoned``.
        encoding: Кодировка файла.

    Returns:
        Список найденных адресов в порядке их следования в файле.

    Raises:
        OSError: Файл не удалось прочитать.
        TypeError: Аргументы имеют неверный тип.
        ValueError: Регулярное выражение зоны некорректно.
    """
    if not isinstance(zoned, bool):
        raise TypeError("Флаг zoned должен быть логическим значением.")

    text = Path(path).read_text(encoding=encoding, errors="replace")
    return _find(text, zoned, zone_pattern)


def find_ipv6_in_url(
    url: str,
    *,
    zoned: bool = False,
    zone_pattern: str | None = None,
    timeout: float = 10.0,
) -> list[str]:
    """Загружает веб-страницу и находит на ней IPv6-адреса.

    Args:
        url: Адрес страницы (http:// или https://).
        zoned: Искать ли адреса с идентификаторами зон.
        zone_pattern: Пользовательское регулярное выражение зоны.
            Если параметр задан, поиск выполняется в режиме ``zoned``.
        timeout: Тайм-аут HTTP-запроса в секундах.

    Returns:
        Список найденных адресов в порядке их следования на странице.

    Raises:
        ValueError: URL имеет неверный формат.
        requests.RequestException: Ошибка при выполнении HTTP-запроса.
        TypeError: Аргументы имеют неверный тип.
        ValueError: Регулярное выражение зоны некорректно.
    """
    if not isinstance(url, str):
        raise TypeError("URL должен быть строкой.")
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError("URL должен начинаться с http:// или https://.")
    if not isinstance(zoned, bool):
        raise TypeError("Флаг zoned должен быть логическим значением.")

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return _find(response.text, zoned, zone_pattern)
