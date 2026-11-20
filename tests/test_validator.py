"""Unit-тесты проверки IPv6-адресов."""

import pytest

from ipvalidator import is_valid_ipv6, is_valid_ipv6_zoned


def test_all_valid_fixture_ipv6(valid_ipv6):
    for ip in valid_ipv6:
        assert is_valid_ipv6(ip) is True, f"должен быть валидным: {ip!r}"


def test_all_invalid_fixture_ipv6(invalid_ipv6):
    for ip in invalid_ipv6:
        assert is_valid_ipv6(ip) is False, f"должен быть невалидным: {ip!r}"


def test_all_valid_fixture_ipv6_zoned(valid_ipv6_zoned):
    for ip in valid_ipv6_zoned:
        assert is_valid_ipv6_zoned(ip) is True, f"должен быть валидным: {ip!r}"


def test_all_invalid_fixture_ipv6_zoned(invalid_ipv6_zoned):
    for ip in invalid_ipv6_zoned:
        assert (
            is_valid_ipv6_zoned(ip) is False
        ), f"должен быть невалидным: {ip!r}"


def test_ipv6_rejects_non_string():
    with pytest.raises(TypeError, match="строкой"):
        is_valid_ipv6(None)


def test_zoned_rejects_non_string_address():
    with pytest.raises(TypeError, match="строкой"):
        is_valid_ipv6_zoned(42)


def test_zoned_rejects_non_string_zone_pattern():
    with pytest.raises(TypeError, match="строкой либо None"):
        is_valid_ipv6_zoned("::1", 42)


def test_zoned_accepts_custom_zone_pattern():
    pattern = r"%eth\d+"

    assert is_valid_ipv6_zoned("fe80::1%eth0", pattern) is True
    assert is_valid_ipv6_zoned("fe80::1%eth12", pattern) is True
    assert is_valid_ipv6_zoned("fe80::1%en0", pattern) is False
    assert is_valid_ipv6_zoned("fe80::1", pattern) is False
    assert is_valid_ipv6_zoned("fe80::1%eth0%eth1", pattern) is False


def test_zoned_accepts_optional_custom_zone_pattern():
    pattern = r"(?:%eth\d+)?"

    assert is_valid_ipv6_zoned("fe80::1", pattern) is True
    assert is_valid_ipv6_zoned("fe80::1%eth7", pattern) is True
    assert is_valid_ipv6_zoned("fe80::1%en0", pattern) is False


def test_zoned_empty_pattern_uses_default_format():
    assert is_valid_ipv6_zoned("fe80::1%eth0", "") is True
    assert is_valid_ipv6_zoned("fe80::1%", "") is False


def test_zoned_rejects_invalid_zone_pattern():
    with pytest.raises(ValueError, match="некорректен"):
        is_valid_ipv6_zoned("::1", "(")
