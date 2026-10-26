from decimal import Decimal

from solution import parse_number


def test_european_format():
    assert parse_number("1.234,56") == Decimal("1234.56")


def test_us_format():
    assert parse_number("1,234.56") == Decimal("1234.56")


def test_parentheses_negative():
    assert parse_number("(1.234,56)") == Decimal("-1234.56")


def test_space_thousands_european():
    assert parse_number("-1 234,56") == Decimal("-1234.56")


def test_plain_integer():
    assert parse_number("42") == Decimal("42")
