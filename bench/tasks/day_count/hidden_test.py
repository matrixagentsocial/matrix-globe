from decimal import Decimal

import pytest

from solution import accrued_interest, day_count_fraction


def test_hidden_us_start_feb_last_adjusts_both():
    # 2023-02-28 is last day of Feb (non-leap): d1 -> 30, and Mar 31 -> 30.
    assert day_count_fraction("2023-02-28", "2023-03-31", "30/360_US") == Decimal("0.0833333333")
    assert day_count_fraction("2023-02-28", "2023-03-30", "30/360_US") == Decimal("0.0833333333")


def test_hidden_us_end_feb_last_only_when_start_feb_last():
    # Start Jan 31 is not Feb-last, so Feb 28/29 keep their real day: 28/360 and 29/360.
    assert day_count_fraction("2023-01-31", "2023-02-28", "30/360_US") == Decimal("0.0777777778")
    assert day_count_fraction("2024-01-31", "2024-02-29", "30/360_US") == Decimal("0.0805555556")


def test_hidden_us_start_feb_last_leap():
    assert day_count_fraction("2024-02-29", "2024-03-31", "30/360_US") == Decimal("0.0833333333")
    assert day_count_fraction("2024-02-29", "2024-03-29", "30/360_US") == Decimal("0.0805555556")


def test_hidden_us_end_31_kept_when_d1_below_30():
    # d1 = 1, so Dec 31 stays 31: 30*11 + 30 = 360 days.
    assert day_count_fraction("2024-01-01", "2024-12-31", "30/360_US") == Decimal("1.0000000000")
    assert day_count_fraction("2024-03-31", "2024-04-30", "30/360_US") == Decimal("0.0833333333")


def test_hidden_30e_caps_days_without_feb_rule():
    # 30E: d1 = 28 (not capped up), d2 = 30 -> 32/360, unlike US 30/360.
    assert day_count_fraction("2023-02-28", "2023-03-31", "30E/360") == Decimal("0.0888888889")
    # 30E caps Dec 31 to 30: 359/360, unlike US above.
    assert day_count_fraction("2024-01-01", "2024-12-31", "30E/360") == Decimal("0.9972222222")


def test_hidden_30e_and_us_agree_on_plain_half_year():
    assert day_count_fraction("2024-01-15", "2024-07-15", "30E/360") == Decimal("0.5000000000")
    assert day_count_fraction("2024-01-15", "2024-07-15", "30/360_US") == Decimal("0.5000000000")
    assert day_count_fraction("2024-01-31", "2024-02-01", "30/360_US") == Decimal("0.0027777778")


def test_hidden_act365f_counts_leap_day_but_denominator_365():
    # 2023-06-15 to 2024-06-15 is 366 actual days / 365.
    assert day_count_fraction("2023-06-15", "2024-06-15", "ACT/365F") == Decimal("1.0027397260")
    assert day_count_fraction("2024-01-01", "2024-01-02", "ACT/365F") == Decimal("0.0027397260")


def test_hidden_act_act_leap_and_multi_year():
    assert day_count_fraction("2024-01-01", "2025-01-01", "ACT/ACT_ISDA") == Decimal("1.0000000000")
    assert day_count_fraction("2023-01-01", "2025-01-01", "ACT/ACT_ISDA") == Decimal("2.0000000000")
    assert day_count_fraction("2023-01-01", "2023-12-31", "ACT/ACT_ISDA") == Decimal("0.9972602740")


def test_hidden_act_act_year_boundary_denominators():
    # 1 day in leap 2024 portion before 2025, and 1 day in non-leap 2023 before 2024.
    assert day_count_fraction("2024-12-31", "2025-01-01", "ACT/ACT_ISDA") == Decimal("0.0027322404")
    assert day_count_fraction("2023-12-31", "2024-01-01", "ACT/ACT_ISDA") == Decimal("0.0027397260")


def test_hidden_act_act_february_leap_vs_nonleap():
    # Feb 2020: 29/366; Feb 2019: 28/365.
    assert day_count_fraction("2020-02-01", "2020-03-01", "ACT/ACT_ISDA") == Decimal("0.0792349727")
    assert day_count_fraction("2019-02-01", "2019-03-01", "ACT/ACT_ISDA") == Decimal("0.0767123288")


def test_hidden_equal_dates_zero_all_conventions():
    for convention in ("30/360_US", "30E/360", "ACT/365F", "ACT/ACT_ISDA"):
        result = day_count_fraction("2024-02-29", "2024-02-29", convention)
        assert result == Decimal("0.0000000000")
        assert result.as_tuple().exponent == -10


def test_hidden_fraction_exponent_ten_places():
    result = day_count_fraction("2024-01-01", "2024-04-01", "ACT/365F")
    assert result.as_tuple().exponent == -10
    assert day_count_fraction("2024-02-28", "2024-02-29", "ACT/ACT_ISDA") == Decimal("0.0027322404")


def test_hidden_accrued_act_act_split():
    # 5000 * 0.06 * (31/365 + 31/366) = 50.8892... -> 50.89
    assert accrued_interest("5000.00", "6", "2023-12-01", "2024-02-01", "ACT/ACT_ISDA") == Decimal("50.89")


def test_hidden_accrued_act365f_exact():
    # 10000 * 0.05 * 91/365 = 124.6575... -> 124.66
    assert accrued_interest("10000.00", "5", "2024-01-01", "2024-04-01", "ACT/365F") == Decimal("124.66")
    assert accrued_interest("1000.00", "10", "2023-01-01", "2024-01-01", "ACT/ACT_ISDA") == Decimal("100.00")
    assert accrued_interest("12000.00", "4", "2024-01-15", "2024-07-15", "30E/360") == Decimal("240.00")


def test_hidden_accrued_uses_unrounded_fraction():
    # Unrounded: 10000000 * 1.00 * 91/365 = 2493150.6849... -> 2493150.68.
    # Using the 10dp fraction 0.2493150685 would give 2493150.69.
    assert accrued_interest("10000000.00", "100", "2024-01-01", "2024-04-01", "ACT/365F") == Decimal("2493150.68")


def test_hidden_accrued_equal_dates_and_zero_rate():
    assert accrued_interest("10000.00", "5", "2024-01-15", "2024-01-15", "ACT/365F") == Decimal("0.00")
    assert accrued_interest("10000.00", "0", "2024-01-01", "2024-12-31", "30/360_US") == Decimal("0.00")
    assert accrued_interest("0.00", "5", "2024-01-01", "2024-07-01", "ACT/365F") == Decimal("0.00")


def test_hidden_end_before_start_raises():
    with pytest.raises(ValueError):
        day_count_fraction("2024-07-01", "2024-01-01", "ACT/365F")
    with pytest.raises(ValueError):
        accrued_interest("1000.00", "5", "2024-07-01", "2024-01-01", "30/360_US")


def test_hidden_unknown_convention_raises():
    with pytest.raises(ValueError):
        day_count_fraction("2024-01-01", "2024-07-01", "ACT/360")
    with pytest.raises(ValueError):
        day_count_fraction("2024-01-01", "2024-07-01", "act/365f")
    with pytest.raises(ValueError):
        day_count_fraction("2024-01-01", "2024-07-01", None)


def test_hidden_bad_date_raises():
    with pytest.raises(ValueError):
        day_count_fraction("2024-02-30", "2024-07-01", "ACT/365F")
    with pytest.raises(ValueError):
        day_count_fraction("2024-01-01", "01/07/2024", "30E/360")


def test_hidden_accrued_invalid_money_raises():
    with pytest.raises(ValueError):
        accrued_interest("10.005", "5", "2024-01-01", "2024-07-01", "ACT/365F")
    with pytest.raises(ValueError):
        accrued_interest("-100.00", "5", "2024-01-01", "2024-07-01", "ACT/365F")
    with pytest.raises(ValueError):
        accrued_interest("100.00", "101", "2024-01-01", "2024-07-01", "ACT/365F")
    with pytest.raises(ValueError):
        accrued_interest("100.00", "-1", "2024-01-01", "2024-07-01", "ACT/365F")
