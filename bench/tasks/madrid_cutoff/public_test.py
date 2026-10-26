import pytest

from solution import is_madrid_business_day, payment_value_date


def test_public_friday_before_cutoff_same_day():
    assert payment_value_date("2026-03-27T16:59") == "2026-03-27"


def test_public_friday_at_cutoff_next_business_day():
    assert payment_value_date("2026-03-27T17:00") == "2026-03-30"


def test_public_saturday_rolls_to_monday():
    assert payment_value_date("2026-03-28T10:00") == "2026-03-30"


def test_public_business_day_helper():
    assert is_madrid_business_day("2026-03-27") is True
    assert is_madrid_business_day("2026-03-28") is False
    assert is_madrid_business_day("2026-03-30", holidays=["2026-03-30"]) is False


def test_public_gap_time_raises():
    with pytest.raises(ValueError):
        payment_value_date("2026-03-29T02:30")
