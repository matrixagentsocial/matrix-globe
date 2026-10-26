from decimal import Decimal

import pytest

from solution import split_installments


def test_hidden_one_cent_three_ways():
    assert split_installments("0.01", 3) == [
        Decimal("0.01"),
        Decimal("0.00"),
        Decimal("0.00"),
    ]


def test_hidden_five_cents_two_ways():
    assert split_installments("0.05", 2) == [Decimal("0.03"), Decimal("0.02")]


def test_hidden_zero_total():
    assert split_installments("0.00", 4) == [Decimal("0.00")] * 4


def test_hidden_large_remainder_order():
    parts = split_installments("100.00", 7)
    # 10000 cents = 7 * 1428 + 4, so the first 4 get the extra cent.
    assert parts[:4] == [Decimal("14.29")] * 4
    assert parts[4:] == [Decimal("14.28")] * 3
    assert sum(parts) == Decimal("100.00")


def test_hidden_max_spread_one_cent():
    parts = split_installments("99.99", 13)
    assert max(parts) - min(parts) <= Decimal("0.01")
    assert sum(parts) == Decimal("99.99")


def test_hidden_two_decimal_exponent():
    for part in split_installments("10.01", 3):
        assert part.as_tuple().exponent == -2


def test_hidden_integer_string_total():
    assert split_installments("100", 4) == [Decimal("25.00")] * 4


def test_hidden_one_decimal_total():
    assert split_installments("10.5", 2) == [Decimal("5.25"), Decimal("5.25")]


def test_hidden_negative_total_raises():
    with pytest.raises(ValueError):
        split_installments("-1.00", 2)


def test_hidden_three_decimals_raises():
    with pytest.raises(ValueError):
        split_installments("10.005", 2)


def test_hidden_non_numeric_raises():
    with pytest.raises(ValueError):
        split_installments("abc", 2)


def test_hidden_empty_raises():
    with pytest.raises(ValueError):
        split_installments("", 2)


def test_hidden_nan_raises():
    with pytest.raises(ValueError):
        split_installments("NaN", 2)


def test_hidden_negative_n_raises():
    with pytest.raises(ValueError):
        split_installments("10.00", -2)


def test_hidden_float_n_raises():
    with pytest.raises(ValueError):
        split_installments("10.00", 2.5)


def test_hidden_bool_n_raises():
    with pytest.raises(ValueError):
        split_installments("10.00", True)


def test_hidden_many_installments_sum():
    parts = split_installments("1234.56", 100)
    assert len(parts) == 100
    assert sum(parts) == Decimal("1234.56")
