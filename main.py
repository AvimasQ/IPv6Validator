"""Командная строка для проверки и поиска IPv6-адресов."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

import requests

from ipvalidator import (
    find_ipv6,
    find_ipv6_in_file,
    find_ipv6_in_url,
    find_ipv6_zoned,
    is_valid_ipv6,
    is_valid_ipv6_zoned,
)

__all__ = ["build_parser", "main"]


def _fail(message: object) -> int:
    """Выводит сообщение об ошибке и возвращает код завершения 2."""
    print(f"Ошибка: {message}", file=sys.stderr)
    return 2


def _check(
    address: str, zoned: bool, zone_pattern: str | None
) -> int:
    """Проверяет один адрес и печатает результат."""
    try:
        if zoned or zone_pattern is not None:
            valid = is_valid_ipv6_zoned(address, zone_pattern)
        else:
            valid = is_valid_ipv6(address)
    except (TypeError, ValueError) as error:
        return _fail(error)

    if valid:
        print(f"Адрес {address!r} корректен.")
        return 0

    print(f"Адрес {address!r} некорректен.")
    return 1


def _report(matches: list[str], source: str) -> int:
    """Печатает найденные адреса и возвращает код завершения."""
    if not matches:
        print(f"IPv6-адреса {source} не найдены.")
        return 1

    print(f"Найдено адресов: {len(matches)} ({source}).")
    for number, address in enumerate(matches, start=1):
        print(f"{number:>3}. {address}")
    return 0


def _search_text(
    text: str, zoned: bool, zone_pattern: str | None
) -> int:
    """Ищет адреса в переданном тексте."""
    try:
        if zoned or zone_pattern is not None:
            matches = find_ipv6_zoned(text, zone_pattern)
        else:
            matches = find_ipv6(text)
    except (TypeError, ValueError) as error:
        return _fail(error)
    return _report(matches, "в тексте")


def _search_file(
    path: str, zoned: bool, zone_pattern: str | None
) -> int:
    """Ищет адреса в файле."""
    try:
        matches = find_ipv6_in_file(
            path, zoned=zoned, zone_pattern=zone_pattern
        )
    except (OSError, TypeError, ValueError) as error:
        return _fail(error)
    return _report(matches, f"в файле {path!r}")


def _search_url(
    url: str, zoned: bool, zone_pattern: str | None
) -> int:
    """Ищет адреса на веб-странице."""
    try:
        matches = find_ipv6_in_url(
            url, zoned=zoned, zone_pattern=zone_pattern
        )
    except (requests.RequestException, TypeError, ValueError) as error:
        return _fail(error)
    return _report(matches, f"на странице {url!r}")


def _ask_yes_no(prompt: str) -> bool:
    """Запрашивает ответ «да/нет»; по умолчанию выбран ответ «нет»."""
    answer = input(prompt).strip().lower()
    return answer in {"y", "yes", "д", "да", "1"}


def _interactive() -> int:
    """Запускает простой интерактивный интерфейс."""
    print("Проверка и поиск IPv6-адресов")
    print("1 — проверить адрес")
    print("2 — найти адреса в файле")
    print("3 — найти адреса на веб-странице")
    print("0 — выход")

    choice = input("Выберите пункт: ").strip()

    if choice in {"", "0"}:
        print("Выход.")
        return 0

    if choice == "1":
        address = input("Введите IPv6-адрес: ").strip()
        zoned = _ask_yes_no(
            "Учитывать идентификатор зоны? [y/N]: "
        )
        return _check(address, zoned, None)

    if choice == "2":
        path = input("Путь к файлу: ").strip()
        zoned = _ask_yes_no(
            "Искать адреса с идентификатором зоны? [y/N]: "
        )
        return _search_file(path, zoned, None)

    if choice == "3":
        url = input("URL страницы: ").strip()
        zoned = _ask_yes_no(
            "Искать адреса с идентификатором зоны? [y/N]: "
        )
        return _search_url(url, zoned, None)

    return _fail("неизвестный пункт меню.")


def build_parser() -> argparse.ArgumentParser:
    """Создаёт парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="ipvalidator",
        description=(
            "Проверка и поиск IPv6-адресов по RFC 5952 и RFC 4007."
        ),
    )
    parser.add_argument(
        "address",
        nargs="?",
        help="IPv6-адрес для проверки",
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "-t",
        "--text",
        help="текст для поиска адресов",
    )
    source.add_argument(
        "-f",
        "--file",
        metavar="PATH",
        help="файл для поиска адресов",
    )
    source.add_argument(
        "-u",
        "--url",
        help="URL страницы для поиска адресов",
    )
    parser.add_argument(
        "--zoned",
        action="store_true",
        help="учитывать идентификатор зоны (RFC 4007)",
    )
    parser.add_argument(
        "--zone-pattern",
        metavar="RE",
        help="регулярное выражение идентификатора зоны",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Точка входа командной строки.

    Args:
        argv: Аргументы командной строки без имени программы. Если
            параметр не задан, используются аргументы из ``sys.argv``.

    Returns:
        Код завершения: 0 — успех, 1 — адрес некорректен или ничего
        не найдено, 2 — ошибка ввода или выполнения.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    has_source = (
        args.text is not None
        or args.file is not None
        or args.url is not None
    )
    if args.address is not None and has_source:
        parser.error(
            "укажите либо адрес, либо источник для поиска, но не оба."
        )

    if args.address is None and not has_source:
        return _interactive()

    zoned = args.zoned or args.zone_pattern is not None

    if args.address is not None:
        return _check(args.address, zoned, args.zone_pattern)
    if args.text is not None:
        return _search_text(args.text, zoned, args.zone_pattern)
    if args.file is not None:
        return _search_file(args.file, zoned, args.zone_pattern)
    if args.url is not None:
        return _search_url(args.url, zoned, args.zone_pattern)

    return _fail("не удалось определить режим работы.")  # pragma: no cover


if __name__ == "__main__":
    sys.exit(main())
