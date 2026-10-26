from datetime import date

import pytest

from solution import add_business_days, adjust_business_day, is_business_day


def test_hidden_holiday_not_business():
    assert is_business_day(date(2024, 6, 3), holidays=[date(2024, 6, 3)]) is False


def test_hidden_weekend_holiday_no_effect():
    assert add_business_days(date(2024, 6, 7), 1, holidays={date(2024, 6, 8)}) == date(2024, 6, 10)


def test_hidden_add_zero_returns_start_on_weekend():
    assert add_business_days(date(2024, 6, 1), 0) == date(2024, 6, 1)


def test_hidden_add_negative():
    assert add_business_days(date(2024, 6, 10), -1) == date(2024, 6, 7)


def test_hidden_add_negative_over_holiday():
    assert add_business_days(date(2024, 6, 11), -1, holidays={date(2024, 6, 10)}) == date(2024, 6, 7)


def test_hidden_add_five_full_week():
    assert add_business_days(date(2024, 6, 3), 5) == date(2024, 6, 10)


def test_hidden_add_start_on_weekend_not_counted():
    # Saturday start, +1 counts Monday.
    assert add_business_days(date(2024, 6, 1), 1) == date(2024, 6, 3)


def test_hidden_add_across_year_with_holiday():
    hols = {date(2025, 1, 1)}
    assert add_business_days(date(2024, 12, 31), 1, holidays=hols) == date(2025, 1, 2)


def test_hidden_following_same_month():
    assert adjust_business_day(date(2024, 6, 1), convention="following") == date(2024, 6, 3)


def test_hidden_modified_following_crosses_month_goes_back():
    # 2024-08-31 is a Saturday; following is Mon 2024-09-02 (next month),
    # so modified following returns Fri 2024-08-30.
    assert adjust_business_day(date(2024, 8, 31), convention="modified_following") == date(2024, 8, 30)


def test_hidden_following_crosses_month_goes_forward():
    assert adjust_business_day(date(2024, 8, 31), convention="following") == date(2024, 9, 2)


def test_hidden_modified_following_with_holiday_at_month_end():
    # Fri 2024-03-29 is a holiday, Sat 30, Sun 31; following is Mon Apr 1
    # (different month) so MF returns the previous business day Thu Mar 28.
    hols = {date(2024, 3, 29)}
    assert adjust_business_day(date(2024, 3, 29), holidays=hols, convention="modified_following") == date(2024, 3, 28)


def test_hidden_modified_following_within_month():
    assert adjust_business_day(date(2024, 6, 1), convention="modified_following") == date(2024, 6, 3)


def test_hidden_preceding_sunday():
    assert adjust_business_day(date(2024, 6, 2), convention="preceding") == date(2024, 5, 31)


def test_hidden_convention_case_insensitive():
    assert adjust_business_day(date(2024, 6, 1), convention="FOLLOWING") == date(2024, 6, 3)


def test_hidden_unknown_convention_raises():
    with pytest.raises(ValueError):
        adjust_business_day(date(2024, 6, 3), convention="nearest")


def test_hidden_bool_n_raises():
    with pytest.raises(ValueError):
        add_business_days(date(2024, 6, 3), True)


def test_hidden_leap_year_february():
    # 2024-02-28 Wed +1 -> Thu 2024-02-29 (leap day, a business day).
    assert add_business_days(date(2024, 2, 28), 1) == date(2024, 2, 29)


def test_hidden_duplicate_holidays_list():
    hols = [date(2024, 6, 10), date(2024, 6, 10)]
    assert add_business_days(date(2024, 6, 7), 1, holidays=hols) == date(2024, 6, 11)
