from decimal import Decimal

import pytest

from solution import amortize, total_interest


def test_public_worked_example():
    schedule = amortize("100.00", "12", 3, "2024-01-15")
    assert [row["payment"] for row in schedule] == [
        Decimal("34.00"),
        Decimal("34.00"),
        Decimal("34.01"),
    ]
    assert [row["interest"] for row in schedule] == [
        Decimal("1.00"),
        Decimal("0.67"),
        Decimal("0.34"),
    ]
    assert [row["balance"] for row in schedule] == [
        Decimal("67.00"),
        Decimal("33.67"),
        Decimal("0.00"),
    ]
    assert [row["date"] for row in schedule] == ["2024-02-15", "2024-03-15", "2024-04-15"]


def test_public_zero_rate():
    schedule = amortize("100.00", "0", 3, "2024-01-15")
    assert [row["payment"] for row in schedule] == [
        Decimal("33.33"),
        Decimal("33.33"),
        Decimal("33.34"),
    ]
    assert total_interest(schedule) == Decimal("0.00")


def test_public_total_interest():
    schedule = amortize("100.00", "12", 3, "2024-01-15")
    assert total_interest(schedule) == Decimal("2.01")


def test_public_anchor_day_clamped():
    schedule = amortize("1200.00", "0", 3, "2024-01-31")
    assert [row["date"] for row in schedule] == ["2024-02-29", "2024-03-31", "2024-04-30"]


def test_public_invalid_months():
    with pytest.raises(ValueError):
        amortize("100.00", "12", 0, "2024-01-15")
