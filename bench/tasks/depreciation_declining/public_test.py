from decimal import Decimal

import pytest

from solution import declining_schedule


def test_public_worked_example_a():
    rows = declining_schedule("10000", "1000", 4, "2")
    assert [r["amount"] for r in rows] == [Decimal("5000.00"), Decimal("2500.00"), Decimal("1250.00"), Decimal("250.00")]
    assert rows[-1]["book_value"] == Decimal("1000.00")


def test_public_worked_example_b_sl_switch():
    rows = declining_schedule("10000", "0", 5, "2")
    assert [r["amount"] for r in rows] == [Decimal("4000.00"), Decimal("2400.00"), Decimal("1440.00"), Decimal("1080.00"), Decimal("1080.00")]


def test_public_default_factor():
    assert declining_schedule("10000", "1000", 4) == declining_schedule("10000", "1000", 4, "2")


def test_public_years_are_one_based():
    rows = declining_schedule("5000", "0", 3, "2")
    assert [r["year"] for r in rows] == [1, 2, 3]


def test_public_invalid_factor():
    with pytest.raises(ValueError):
        declining_schedule("10000", "0", 5, "4")
