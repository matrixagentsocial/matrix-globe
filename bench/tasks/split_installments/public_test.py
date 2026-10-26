from decimal import Decimal

import pytest

from solution import split_installments


def test_split_even():
    assert split_installments("90.00", 3) == [Decimal("30.00")] * 3


def test_split_remainder_first():
    assert split_installments("100.00", 3) == [
        Decimal("33.34"),
        Decimal("33.33"),
        Decimal("33.33"),
    ]


def test_split_sums_exactly():
    parts = split_installments("10.00", 6)
    assert sum(parts) == Decimal("10.00")
    assert len(parts) == 6


def test_split_single():
    assert split_installments("42.50", 1) == [Decimal("42.50")]


def test_split_zero_n_raises():
    with pytest.raises(ValueError):
        split_installments("10.00", 0)
