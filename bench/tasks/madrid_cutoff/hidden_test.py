import pytest

from solution import is_madrid_business_day, payment_value_date


def test_hidden_weekday_before_cutoff_with_seconds():
    assert payment_value_date("2026-03-27T16:59:59") == "2026-03-27"


def test_hidden_exact_cutoff_with_seconds_rolls():
    assert payment_value_date("2026-03-27T17:00:00") == "2026-03-30"


def test_hidden_after_cutoff_weekday_rolls_one_day():
    # Tuesday 2026-03-31 after cutoff -> Wednesday 2026-04-01
    assert payment_value_date("2026-03-31T17:30") == "2026-04-01"


def test_hidden_just_after_midnight_business_day():
    assert payment_value_date("2026-03-30T00:00") == "2026-03-30"


def test_hidden_sunday_rolls_to_monday():
    assert payment_value_date("2026-03-29T12:00") == "2026-03-30"


def test_hidden_holiday_monday_pushes_to_tuesday():
    assert payment_value_date("2026-03-27T17:00", holidays=["2026-03-30"]) == "2026-03-31"


def test_hidden_holiday_on_submitted_day_rolls():
    assert payment_value_date("2026-03-30T10:00", holidays=("2026-03-30",)) == "2026-03-31"


def test_hidden_consecutive_holidays_and_weekend():
    # Fri after cutoff, Mon+Tue holidays -> Wed 2026-04-01
    assert payment_value_date("2026-03-27T18:00", holidays={"2026-03-30", "2026-03-31"}) == "2026-04-01"


def test_hidden_dst_spring_weekend_friday_cutoff():
    # 2026-03-29 is the spring-forward Sunday; Fri 17:00 still -> Mon 03-30
    assert payment_value_date("2026-03-27T17:00") == "2026-03-30"


def test_hidden_gap_time_raises_on_weekend():
    with pytest.raises(ValueError):
        payment_value_date("2026-03-29T02:30:00")


def test_hidden_ambiguous_fallback_accepted():
    # Sunday 2026-10-25 02:30 is ambiguous but valid; Sunday -> Mon 10-26
    assert payment_value_date("2026-10-25T02:30") == "2026-10-26"


def test_hidden_fallback_friday_same_and_roll():
    assert payment_value_date("2026-10-23T16:00") == "2026-10-23"
    assert payment_value_date("2026-10-23T17:00") == "2026-10-26"


def test_hidden_business_day_weekdays():
    assert is_madrid_business_day("2026-10-23") is True  # Friday
    assert is_madrid_business_day("2026-10-24") is False  # Saturday
    assert is_madrid_business_day("2026-10-25") is False  # Sunday
    assert is_madrid_business_day("2026-10-26") is True  # Monday


def test_hidden_offset_suffix_raises():
    with pytest.raises(ValueError):
        payment_value_date("2026-03-27T16:00+01:00")
    with pytest.raises(ValueError):
        payment_value_date("2026-03-27T16:00Z")


def test_hidden_bad_formats_raise():
    for bad in ["2026-03-27 16:00", "2026-03-27", "27-03-2026T16:00", "2026-03-27T16:00:00.5", "2026-02-30T10:00", "2026-03-27T25:00", ""]:
        with pytest.raises(ValueError):
            payment_value_date(bad)


def test_hidden_invalid_holiday_raises():
    with pytest.raises(ValueError):
        payment_value_date("2026-03-27T10:00", holidays=["2026-13-01"])
    with pytest.raises(ValueError):
        is_madrid_business_day("2026-03-27", holidays=["not-a-date"])


def test_hidden_invalid_business_day_date_raises():
    with pytest.raises(ValueError):
        is_madrid_business_day("2026-02-30")
    with pytest.raises(ValueError):
        is_madrid_business_day("30/03/2026")


def test_hidden_holiday_as_single_string_raises():
    with pytest.raises(ValueError):
        payment_value_date("2026-03-27T10:00", holidays="2026-03-27")


def test_hidden_duplicate_holidays_allowed_and_irrelevant_holiday():
    assert payment_value_date("2026-03-27T10:00", holidays=["2026-01-01", "2026-01-01"]) == "2026-03-27"
