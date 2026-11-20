# IPv6 Validator

Инструмент для проверки и поиска IPv6-адресов на Python. Проверяет
каноническую запись по RFC 5952, поддерживает идентификаторы зон по
RFC 4007, ищет адреса в тексте, файлах и на веб-страницах. Есть
командная строка и интерактивный режим.

## Возможности

* проверка канонической записи IPv6 (RFC 5952);
* проверка адресов с идентификатором зоны (RFC 4007) и настраиваемым
  форматом зоны;
* поиск адресов в тексте, файле и на странице по URL;
* командная строка и интерактивное меню;
* unit-тесты валидатора.

## Требования и установка

* Python 3.10+;
* `requests` — для поиска на веб-страницах;
* `pytest` — для запуска тестов.

```bash
python3 -m pip install -r requirements.txt
```

Запуск выполняется из корня проекта с `PYTHONPATH=src`.

## Быстрый старт

Проверка адреса:

```bash
PYTHONPATH=src python3 -m main 2001:db8::1
# Адрес '2001:db8::1' корректен.

PYTHONPATH=src python3 -m main 2001:DB8::1
# Адрес '2001:DB8::1' некорректен.
```

Проверка адреса с зоной:

```bash
PYTHONPATH=src python3 -m main --zoned fe80::1%eth0
PYTHONPATH=src python3 -m main --zoned --zone-pattern '%eth\d+' fe80::1%eth0
```

Поиск адресов:

```bash
PYTHONPATH=src python3 -m main --text "Сервер: 2001:db8::1, шлюз: ::1"
PYTHONPATH=src python3 -m main --zoned --file examples/addresses.txt
PYTHONPATH=src python3 -m main --url https://example.org
```

Интерактивный режим:

```bash
PYTHONPATH=src python3 -m main
```

Коды завершения:

* `0` — адрес корректен или адреса найдены;
* `1` — адрес некорректен или адреса не найдены;
* `2` — ошибка ввода, чтения файла, HTTP-запроса или шаблона зоны.

## Python API

```python
from ipvalidator import (
    find_ipv6,
    find_ipv6_in_file,
    find_ipv6_in_url,
    find_ipv6_zoned,
    is_valid_ipv6,
    is_valid_ipv6_zoned,
)

is_valid_ipv6("2001:db8::1")                     # True
is_valid_ipv6("2001:DB8::1")                     # False
is_valid_ipv6_zoned("fe80::1%eth0")              # True
is_valid_ipv6_zoned("fe80::1%eth0", r"%eth\d+")  # True

find_ipv6("Адрес: 2001:db8::1")                  # ['2001:db8::1']
find_ipv6_zoned("Шлюз: fe80::1%eth0")            # ['fe80::1%eth0']
find_ipv6_in_file("examples/addresses.txt")
find_ipv6_in_url("https://example.org")
```

| Функция | Назначение |
| --- | --- |
| `is_valid_ipv6(address)` | проверка канонической записи IPv6 |
| `is_valid_ipv6_zoned(address, zone_pattern=None)` | проверка IPv6 с зоной |
| `find_ipv6(text)` | поиск адресов без зон |
| `find_ipv6_zoned(text, zone_pattern=None)` | поиск адресов с зонами |
| `find_ipv6_in_file(path, ...)` | поиск в текстовом файле |
| `find_ipv6_in_url(url, ...)` | загрузка страницы и поиск адресов |

## Структура проекта

```text
.
├── src/
│   ├── ipvalidator.py      # валидатор и поиск адресов
│   └── main.py             # командная строка и интерактивный режим
├── tests/
│   ├── conftest.py         # наборы тестовых адресов
│   └── test_validator.py   # unit-тесты валидатора
├── docs/
│   ├── README.md           # индекс документации
│   ├── usage.md            # командная строка и Python API
│   └── architecture.md     # устройство валидатора и поиска
├── examples/
│   └── addresses.txt       # пример файла для поиска
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Документация

* [Использование](docs/usage.md) — команды, API и коды завершения.
* [Устройство проекта](docs/architecture.md) — регулярное выражение,
  проверка каноничности, зоны и поиск.

## Тесты

```bash
python3 -m pytest -q
```

Тесты находятся в `tests/` и проверяют валидатор IPv6: корректные и
некорректные адреса, каноническое сжатие `::`, идентификаторы зон,
пользовательские шаблоны зон и обработку ошибок аргументов.

## Ограничения

* Поддерживается только каноническая шестнадцатеричная запись IPv6.
* Смешанная запись с IPv4 (`::ffff:192.0.2.1`) считается некорректной.
* Для поиска по URL поддерживаются только схемы `http://` и `https://`.
* Формат идентификатора зоны не стандартизирован RFC 4007, поэтому
  при необходимости его нужно задавать явно.
