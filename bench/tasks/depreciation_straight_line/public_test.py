from decimal import Decimal

import pytest

from solution import straight_line_schedule


def test_public_worked_example():
    rows = straight_line_schedule("12000", "0", 5, 2024, 7)
    assert [r["year"] for r in rows] == [2024, 2025, 2026, 2027, 2028, 2029]
    assert [r["amount"] for r in rows] == [Decimal("1100.00"), Decimal("2400.00"), Decimal("2400.00"), Decimal("2400.00"), Decimal("2400.00"), Decimal("1300.00")]
    assert rows[-1]["book_value"] == Decimal("0.00")
    assert sum(r["amount"] for r in rows) == Decimal("12000.00")


def test_public_salvage_book_value():
    rows = straight_line_schedule("6000", "600", 3, 2021, 12)
    assert rows[-1]["book_value"] == Decimal("600.00")
    assert sum(r["amount"] for r in rows) == Decimal("5400.00")


def test_public_first_year_january():
    rows = straight_line_schedule("12000", "0", 4, 2023, 1)
    assert rows[0]["amount"] == Decimal("2875.00")
    assert rows[0]["year"] == 2023


def test_public_invalid_life():
    with pytest.raises(ValueError):
        straight_line_schedule("1000", "0", 0, 2024, 1)


def test_public_invalid_month():
    with pytest.raises(ValueError):
        straight_line_schedule("1000", "0", 5, 2024, 13)
