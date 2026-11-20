# Документация к коду

## Запуск

Зависимости: `requests` и `pytest`.

```bash
python3 -m pip install -r requirements.txt

PYTHONPATH=src python3 -m main 2001:db8::1
PYTHONPATH=src python3 -m main --zoned fe80::1%eth0
PYTHONPATH=src python3 -m main --text "::1 и 2001:db8::2"
PYTHONPATH=src python3 -m main --zoned --file examples/addresses.txt
PYTHONPATH=src python3 -m main --url https://example.org
PYTHONPATH=src python3 -m main
```

Последняя команда открывает интерактивное меню. Источники `--text`,
`--file` и `--url` взаимоисключающие.

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
is_valid_ipv6_zoned("fe80::1%eth0")              # True
is_valid_ipv6_zoned("fe80::1%eth0", r"%eth\d+")  # True
find_ipv6("Адрес: 2001:db8::1")                  # ['2001:db8::1']
find_ipv6_zoned("Шлюз: fe80::1%eth0")            # ['fe80::1%eth0']
find_ipv6_in_file("examples/addresses.txt")
find_ipv6_in_url("https://example.org")
```

Функции проверки возвращают `bool`, функции поиска — список адресов в
порядке следования в источнике.

## Модули

| Файл | Назначение |
| --- | --- |
| `src/ipvalidator.py` | регулярные выражения, проверка и поиск |
| `src/main.py` | CLI и интерактивный режим |
| `tests/test_validator.py` | unit-тесты валидатора |

## Проверка IPv6

Проверка состоит из двух этапов:

1. `_IPBASE` проверяет синтаксис: гексеты, отсутствие ведущих нулей,
   допустимое расположение `::`. Шаблон не разрешает сокращать один
   нулевой гексет.
2. `_consecutive_zeros` проверяет каноничность: `::` должен заменять
   самый длинный прогон нулей, а при равной длине — первый.

Зона проверяется шаблоном `({_IPBASE}){zone_pattern}`. Формат по
умолчанию — `%[A-Za-z0-9_.-]+`; пользовательский шаблон компилируется
с кэшированием через `lru_cache`.

## Поиск

Шаблон поиска ограничен границами токена, чтобы не вырезать адрес из
строки вида `2001:db8::1::2`, `2001:db8::1.5` или
`::ffff:192.168.0.1`. Зона ищется лениво, чтобы не захватывать точку в
конце предложения, но при этом распознавать `eth0.100` и `my-zone`.

`find_ipv6_in_file()` читает файл и передаёт текст общему поиску.
`find_ipv6_in_url()` скачивает страницу через `requests`, проверяет
HTTP-статус и также вызывает общий поиск.

## Ограничения

* Поддерживается только каноническая шестнадцатеричная запись IPv6.
* Смешанная запись с IPv4 (`::ffff:192.0.2.1`) считается некорректной.
* Для URL поддерживаются только `http://` и `https://`.
* Формат идентификатора зоны не стандартизирован RFC 4007 и при
  необходимости задаётся явно.
