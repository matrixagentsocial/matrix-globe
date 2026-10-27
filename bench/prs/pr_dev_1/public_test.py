# --- public tests for amortization_schedule (module task_a.py) ---
from decimal import Decimal

import pytest

from task_a import amortize, total_interest


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

# --- public tests for business_days (module task_b.py) ---
from datetime import date

from task_b import add_business_days, adjust_business_day, is_business_day


def test_is_business_day_weekday():
    assert is_business_day(date(2024, 6, 3)) is True  # Monday
    assert is_business_day(date(2024, 6, 1)) is False  # Saturday


def test_add_one_from_friday():
    assert add_business_days(date(2024, 6, 7), 1) == date(2024, 6, 10)


def test_add_skips_holiday():
    assert add_business_days(date(2024, 6, 7), 1, holidays={date(2024, 6, 10)}) == date(2024, 6, 11)


def test_adjust_following_saturday():
    assert adjust_business_day(date(2024, 6, 1), convention="following") == date(2024, 6, 3)


def test_adjust_modified_following_business_day_unchanged():
    assert adjust_business_day(date(2024, 6, 3)) == date(2024, 6, 3)

# --- public tests for currency_rounding (module task_c.py) ---
from decimal import Decimal

import pytest

from task_c import round_money


def test_round_eur_half_up():
    assert round_money("1.005", "EUR") == Decimal("1.01")


def test_round_jpy_zero_places():
    assert round_money("123.5", "JPY") == Decimal("124")


def test_round_half_even():
    assert round_money("2.5", "JPY", "HALF_EVEN") == Decimal("2")


def test_round_unknown_currency():
    with pytest.raises(ValueError):
        round_money("1.00", "XXX")


def test_round_bhd_three_places():
    assert round_money("1.0005", "BHD") == Decimal("1.001")
