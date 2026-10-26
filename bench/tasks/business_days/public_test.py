from datetime import date

from solution import add_business_days, adjust_business_day, is_business_day


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
