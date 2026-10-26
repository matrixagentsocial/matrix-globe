from datetime import date
from decimal import Decimal

import pytest

from solution import aging_buckets

AS_OF = date(2024, 6, 10)


def _one(due, amount="10.00"):
    return aging_buckets([{"due_date": due, "amount": amount}], AS_OF)


def test_hidden_day_1_first_bucket():
    assert _one(date(2024, 6, 9))["1-30"] == Decimal("10.00")


def test_hidden_day_30_boundary():
    # 2024-05-11 is exactly 30 days before 2024-06-10.
    result = _one(date(2024, 5, 11))
    assert result["1-30"] == Decimal("10.00")
    assert result["31-60"] == Decimal("0.00")


def test_hidden_day_31_boundary():
    result = _one(date(2024, 5, 10))
    assert result["31-60"] == Decimal("10.00")
    assert result["1-30"] == Decimal("0.00")


def test_hidden_day_60_boundary():
    assert _one(date(2024, 4, 11))["31-60"] == Decimal("10.00")


def test_hidden_day_61_boundary():
    assert _one(date(2024, 4, 10))["61-90"] == Decimal("10.00")


def test_hidden_day_90_boundary():
    assert _one(date(2024, 3, 12))["61-90"] == Decimal("10.00")


def test_hidden_day_91_is_90_plus():
    result = _one(date(2024, 3, 11))
    assert result["90+"] == Decimal("10.00")
    assert result["61-90"] == Decimal("0.00")


def test_hidden_future_due_is_current():
    assert _one(date(2024, 12, 25))["current"] == Decimal("10.00")


def test_hidden_sums_within_bucket():
    result = aging_buckets(
        [
            {"due_date": date(2024, 6, 1), "amount": "10.10"},
            {"due_date": date(2024, 6, 5), "amount": "20.20"},
        ],
        AS_OF,
    )
    assert result["1-30"] == Decimal("30.30")


def test_hidden_credit_note_reduces_bucket():
    result = aging_buckets(
        [
            {"due_date": date(2024, 6, 1), "amount": "100.00"},
            {"due_date": date(2024, 6, 2), "amount": "-30.00"},
        ],
        AS_OF,
    )
    assert result["1-30"] == Decimal("70.00")


def test_hidden_iso_string_dates_and_string_as_of():
    result = aging_buckets(
        [{"due_date": "2024-05-11", "amount": "5.00"}], "2024-06-10"
    )
    assert result["1-30"] == Decimal("5.00")


def test_hidden_exponent_two_places():
    result = _one(date(2024, 6, 10), amount="5")
    assert result["current"] == Decimal("5.00")
    assert result["current"].as_tuple().exponent == -2


def test_hidden_decimal_amount_accepted():
    result = aging_buckets(
        [{"due_date": date(2024, 6, 10), "amount": Decimal("3.33")}], AS_OF
    )
    assert result["current"] == Decimal("3.33")


def test_hidden_missing_amount_raises():
    with pytest.raises(ValueError):
        aging_buckets([{"due_date": date(2024, 6, 1)}], AS_OF)


def test_hidden_missing_due_date_raises():
    with pytest.raises(ValueError):
        aging_buckets([{"amount": "1.00"}], AS_OF)


def test_hidden_bad_date_string_raises():
    with pytest.raises(ValueError):
        aging_buckets([{"due_date": "10/06/2024", "amount": "1.00"}], AS_OF)


def test_hidden_float_amount_raises():
    with pytest.raises(ValueError):
        aging_buckets([{"due_date": date(2024, 6, 1), "amount": 1.5}], AS_OF)


def test_hidden_bad_amount_raises():
    with pytest.raises(ValueError):
        aging_buckets([{"due_date": date(2024, 6, 1), "amount": "abc"}], AS_OF)


def test_hidden_leap_year_day_count():
    # 2024 is a leap year: 2024-02-29 to 2024-03-30 is 30 days.
    result = aging_buckets(
        [{"due_date": date(2024, 2, 29), "amount": "10.00"}], date(2024, 3, 30)
    )
    assert result["1-30"] == Decimal("10.00")
