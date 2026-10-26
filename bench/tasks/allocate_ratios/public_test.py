from decimal import Decimal

import pytest

from solution import allocate_by_ratios


def test_public_equal_split():
    assert allocate_by_ratios("100.00", [1, 1, 1]) == [Decimal("33.34"), Decimal("33.33"), Decimal("33.33")]


def test_public_weighted_split():
    assert allocate_by_ratios("10.00", [2, 1, 1]) == [Decimal("5.00"), Decimal("2.50"), Decimal("2.50")]


def test_public_zero_weight():
    assert allocate_by_ratios("100.00", [0, 1, 0]) == [Decimal("0.00"), Decimal("100.00"), Decimal("0.00")]


def test_public_five_cents():
    assert allocate_by_ratios("0.05", [1, 1]) == [Decimal("0.03"), Decimal("0.02")]


def test_public_empty_ratios_raises():
    with pytest.raises(ValueError):
        allocate_by_ratios("10.00", [])
