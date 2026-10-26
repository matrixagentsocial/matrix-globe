from decimal import Decimal

import pytest

from solution import parse_number


def test_hidden_single_comma_is_decimal():
    assert parse_number("1,234") == Decimal("1.234")


def test_hidden_single_dot_is_decimal():
    assert parse_number("1.234") == Decimal("1.234")


def test_hidden_multiple_commas_are_thousands():
    assert parse_number("1,234,567") == Decimal("1234567")


def test_hidden_multiple_dots_are_thousands():
    assert parse_number("1.234.567") == Decimal("1234567")


def test_hidden_full_european_millions():
    assert parse_number("1.234.567,89") == Decimal("1234567.89")


def test_hidden_full_us_millions():
    assert parse_number("1,234,567.89") == Decimal("1234567.89")


def test_hidden_nbsp_thousands():
    assert parse_number("1\u00a0234,56") == Decimal("1234.56")


def test_hidden_plus_sign():
    assert parse_number("+12,5") == Decimal("12.5")


def test_hidden_parentheses_us_format():
    assert parse_number("(1,234.56)") == Decimal("-1234.56")


def test_hidden_surrounding_whitespace():
    assert parse_number("  1.234,56  ") == Decimal("1234.56")


def test_hidden_zero_decimal():
    assert parse_number("0,00") == Decimal("0.00")


def test_hidden_negative_decimal_comma():
    assert parse_number("-0,5") == Decimal("-0.5")


def test_hidden_bad_grouping_commas_raises():
    with pytest.raises(ValueError):
        parse_number("12,34,56")


def test_hidden_bad_grouping_dots_raises():
    with pytest.raises(ValueError):
        parse_number("1.23.456")


def test_hidden_sign_with_parentheses_raises():
    with pytest.raises(ValueError):
        parse_number("-(1,5)")


def test_hidden_sign_inside_parentheses_raises():
    with pytest.raises(ValueError):
        parse_number("(-1,5)")


def test_hidden_empty_raises():
    with pytest.raises(ValueError):
        parse_number("")


def test_hidden_letters_raise():
    with pytest.raises(ValueError):
        parse_number("12a34")


def test_hidden_trailing_separator_raises():
    with pytest.raises(ValueError):
        parse_number("5.")


def test_hidden_leading_separator_raises():
    with pytest.raises(ValueError):
        parse_number(".5")


def test_hidden_double_sign_raises():
    with pytest.raises(ValueError):
        parse_number("--5")
