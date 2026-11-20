# Использование

## Установка

Требуется Python 3.10+.

```bash
python3 -m pip install -r requirements.txt
```

Запуск выполняется из корня проекта с `PYTHONPATH=src`.

## Командная строка

Скрипт запускается из корня проекта:

```bash
PYTHONPATH=src python3 -m main [address] [-t TEXT | -f PATH | -u URL] [--zoned] [--zone-pattern RE]
```

### Проверка адреса

```bash
PYTHONPATH=src python3 -m main 2001:db8::1
# Адрес '2001:db8::1' корректен.

PYTHONPATH=src python3 -m main 2001:DB8::1
# Адрес '2001:DB8::1' некорректен.
```

### Проверка адреса с зоной

```bash
PYTHONPATH=src python3 -m main --zoned fe80::1%eth0
PYTHONPATH=src python3 -m main --zoned --zone-pattern '%eth\d+' fe80::1%eth0
```

Если указан `--zone-pattern`, режим зон включается автоматически.

### Поиск адресов

```bash
PYTHONPATH=src python3 -m main --text "Сервер: 2001:db8::1, шлюз: ::1"
PYTHONPATH=src python3 -m main --zoned --text "fe80::1%eth0"
PYTHONPATH=src python3 -m main --file examples/addresses.txt
PYTHONPATH=src python3 -m main --zoned --file examples/addresses.txt
PYTHONPATH=src python3 -m main --url https://example.org
```

Источник (`--text`, `--file`, `--url`) нельзя комбинировать с адресом
для проверки. Ключи `--text`, `--file` и `--url` взаимоисключающие.

### Интерактивный режим

Если запустить программу без аргументов, появится меню:

```text
Проверка и поиск IPv6-адресов
1 — проверить адрес
2 — найти адреса в файле
3 — найти адреса на веб-странице
0 — выход
```

### Коды завершения

| Код | Значение |
| ---: | --- |
| `0` | адрес корректен или адреса найдены |
| `1` | адрес некорректен или адреса не найдены |
| `2` | ошибка ввода, чтения файла, HTTP-запроса или шаблона зоны |

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

is_valid_ipv6("2001:db8::1")                    # True
is_valid_ipv6("2001:DB8::1")                    # False
is_valid_ipv6_zoned("fe80::1%eth0")             # True
is_valid_ipv6_zoned("fe80::1%eth0", r"%eth\d+") # True

find_ipv6("Адрес: 2001:db8::1")                 # ['2001:db8::1']
find_ipv6_zoned("Шлюз: fe80::1%eth0")           # ['fe80::1%eth0']
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

Все функции проверки возвращают `bool`, функции поиска — список строк
в порядке их следования в источнике.

### Исключения

* `TypeError` — аргумент имеет неверный тип;
* `ValueError` — неверный URL или некорректное регулярное выражение
  зоны;
* `OSError` — файл не удалось прочитать;
* `requests.RequestException` — ошибка HTTP-запроса.

## Запуск тестов

```bash
python3 -m pytest -q
```

Тесты находятся в `tests/` и проверяют валидатор IPv6.
