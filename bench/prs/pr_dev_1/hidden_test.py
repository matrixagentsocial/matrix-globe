# --- hidden tests for amortization_schedule (module task_a.py) ---
from decimal import Decimal

import pytest

from task_a import amortize, total_interest


def test_hidden_worked_example_full_rows():
    assert amortize("100.00", "12", 3, "2024-01-15") == [
        {"n": 1, "date": "2024-02-15", "payment": Decimal("34.00"), "interest": Decimal("1.00"), "principal": Decimal("33.00"), "balance": Decimal("67.00")},
        {"n": 2, "date": "2024-03-15", "payment": Decimal("34.00"), "interest": Decimal("0.67"), "principal": Decimal("33.33"), "balance": Decimal("33.67")},
        {"n": 3, "date": "2024-04-15", "payment": Decimal("34.01"), "interest": Decimal("0.34"), "principal": Decimal("33.67"), "balance": Decimal("0.00")},
    ]


def test_hidden_zero_rate_final_cent():
    schedule = amortize("100.00", "0", 3, "2024-01-15")
    assert [row["principal"] for row in schedule] == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
    assert [row["balance"] for row in schedule] == [Decimal("66.67"), Decimal("33.34"), Decimal("0.00")]
    assert all(row["interest"] == Decimal("0.00") for row in schedule)


def test_hidden_single_month():
    assert amortize("100.00", "12", 1, "2024-01-15") == [
        {"n": 1, "date": "2024-02-15", "payment": Decimal("101.00"), "interest": Decimal("1.00"), "principal": Decimal("100.00"), "balance": Decimal("0.00")}
    ]


def test_hidden_anchor_31_dates_full_year():
    schedule = amortize("1200.00", "0", 12, "2024-01-31")
    assert [row["date"] for row in schedule] == [
        "2024-02-29", "2024-03-31", "2024-04-30", "2024-05-31",
        "2024-06-30", "2024-07-31", "2024-08-31", "2024-09-30",
        "2024-10-31", "2024-11-30", "2024-12-31", "2025-01-31",
    ]
    assert [row["payment"] for row in schedule] == [Decimal("100.00")] * 12


def test_hidden_anchor_restored_after_feb_clamp():
    schedule = amortize("100.00", "12", 2, "2024-01-31")
    assert [row["date"] for row in schedule] == ["2024-02-29", "2024-03-31"]
    assert [row["payment"] for row in schedule] == [Decimal("50.75"), Decimal("50.75")]
    assert [row["interest"] for row in schedule] == [Decimal("1.00"), Decimal("0.50")]
    assert schedule[-1]["balance"] == Decimal("0.00")


def test_hidden_year_rollover_with_interest():
    schedule = amortize("500.00", "6", 6, "2023-12-31")
    assert [row["date"] for row in schedule] == [
        "2024-01-31", "2024-02-29", "2024-03-31",
        "2024-04-30", "2024-05-31", "2024-06-30",
    ]
    assert [row["payment"] for row in schedule] == [Decimal("84.80")] * 5 + [Decimal("84.78")]
    assert [row["interest"] for row in schedule] == [
        Decimal("2.50"), Decimal("2.09"), Decimal("1.67"),
        Decimal("1.26"), Decimal("0.84"), Decimal("0.42"),
    ]
    assert total_interest(schedule) == Decimal("8.78")


def test_hidden_twelve_month_known_schedule():
    schedule = amortize("1000.00", "12", 12, "2024-01-01")
    assert schedule[0]["payment"] == Decimal("88.85")
    assert schedule[0]["interest"] == Decimal("10.00")
    assert schedule[0]["balance"] == Decimal("921.15")
    assert schedule[-1]["payment"] == Decimal("88.84")
    assert schedule[-1]["interest"] == Decimal("0.88")
    assert schedule[-1]["balance"] == Decimal("0.00")
    assert sum(row["principal"] for row in schedule) == Decimal("1000.00")
    assert total_interest(schedule) == Decimal("66.19")


def test_hidden_money_exponents_and_keys():
    schedule = amortize("250.00", "9", 5, "2024-03-10")
    assert len(schedule) == 5
    for index, row in enumerate(schedule, start=1):
        assert set(row.keys()) == {"n", "date", "payment", "interest", "principal", "balance"}
        assert row["n"] == index
        for key in ("payment", "interest", "principal", "balance"):
            assert row[key].as_tuple().exponent == -2
    assert schedule[-1]["balance"] == Decimal("0.00")


def test_hidden_total_interest_empty():
    assert total_interest([]) == Decimal("0.00")
    assert total_interest([]).as_tuple().exponent == -2


def test_hidden_principal_three_decimals_raises():
    with pytest.raises(ValueError):
        amortize("10.005", "12", 3, "2024-01-15")


def test_hidden_principal_zero_and_negative_raise():
    with pytest.raises(ValueError):
        amortize("0.00", "12", 3, "2024-01-15")
    with pytest.raises(ValueError):
        amortize("-100.00", "12", 3, "2024-01-15")


def test_hidden_principal_nonstring_and_nan_raise():
    with pytest.raises(ValueError):
        amortize(100, "12", 3, "2024-01-15")
    with pytest.raises(ValueError):
        amortize("NaN", "12", 3, "2024-01-15")
    with pytest.raises(ValueError):
        amortize("abc", "12", 3, "2024-01-15")


def test_hidden_rate_out_of_range_raises():
    with pytest.raises(ValueError):
        amortize("100.00", "100.01", 3, "2024-01-15")
    with pytest.raises(ValueError):
        amortize("100.00", "-0.01", 3, "2024-01-15")


def test_hidden_rate_invalid_raises():
    with pytest.raises(ValueError):
        amortize("100.00", "abc", 3, "2024-01-15")
    with pytest.raises(ValueError):
        amortize("100.00", 12, 3, "2024-01-15")


def test_hidden_months_bool_raises():
    with pytest.raises(ValueError):
        amortize("100.00", "12", True, "2024-01-15")


def test_hidden_months_bounds_raise():
    with pytest.raises(ValueError):
        amortize("100.00", "12", 361, "2024-01-15")
    with pytest.raises(ValueError):
        amortize("100.00", "12", -1, "2024-01-15")


def test_hidden_months_nonint_raises():
    with pytest.raises(ValueError):
        amortize("100.00", "12", 2.5, "2024-01-15")
    with pytest.raises(ValueError):
        amortize("100.00", "12", "3", "2024-01-15")


def test_hidden_bad_start_date_raises():
    with pytest.raises(ValueError):
        amortize("100.00", "12", 3, "2024-02-30")
    with pytest.raises(ValueError):
        amortize("100.00", "12", 3, "15/01/2024")
    with pytest.raises(ValueError):
        amortize("100.00", "12", 3, "2024-13-01")

# --- hidden tests for business_days (module task_b.py) ---
from datetime import date

import pytest

from task_b import add_business_days, adjust_business_day, is_business_day


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

# --- hidden tests for currency_rounding (module task_c.py) ---
from decimal import Decimal

import pytest

from task_c import round_money


def test_hidden_half_even_up_to_even():
    assert round_money("3.5", "JPY", "HALF_EVEN") == Decimal("4")


def test_hidden_half_even_eur_tie():
    assert round_money("1.015", "EUR", "HALF_EVEN") == Decimal("1.02")
    assert round_money("1.005", "EUR", "HALF_EVEN") == Decimal("1.00")


def test_hidden_half_up_negative_tie():
    assert round_money("-2.5", "JPY", "HALF_UP") == Decimal("-3")


def test_hidden_half_even_negative_tie():
    assert round_money("-2.5", "JPY", "HALF_EVEN") == Decimal("-2")


def test_hidden_down_truncates_positive():
    assert round_money("1.239", "EUR", "DOWN") == Decimal("1.23")


def test_hidden_down_truncates_negative_toward_zero():
    assert round_money("-1.239", "EUR", "DOWN") == Decimal("-1.23")


def test_hidden_up_away_from_zero_positive():
    assert round_money("1.231", "EUR", "UP") == Decimal("1.24")


def test_hidden_up_away_from_zero_negative():
    assert round_money("-1.231", "EUR", "UP") == Decimal("-1.24")


def test_hidden_kwd_three_places_half_up():
    assert round_money("0.0005", "KWD") == Decimal("0.001")


def test_hidden_krw_zero_places():
    result = round_money("999.4", "KRW")
    assert result == Decimal("999")
    assert result.as_tuple().exponent == 0


def test_hidden_eur_exponent_two():
    assert round_money("1.2", "EUR").as_tuple().exponent == -2


def test_hidden_lowercase_currency_and_mode():
    assert round_money("1.005", "eur", "half_up") == Decimal("1.01")


def test_hidden_no_cash_rounding_chf():
    assert round_money("1.03", "CHF") == Decimal("1.03")
    assert round_money("1.025", "CHF", "HALF_UP") == Decimal("1.03")


def test_hidden_zero_amount():
    assert round_money("0", "JPY") == Decimal("0")
    assert round_money("0.000", "BHD") == Decimal("0.000")


def test_hidden_unknown_mode_raises():
    with pytest.raises(ValueError):
        round_money("1.00", "EUR", "CEILING")


def test_hidden_unknown_currency_raises():
    with pytest.raises(ValueError):
        round_money("1.00", "BTC")


def test_hidden_invalid_amount_raises():
    with pytest.raises(ValueError):
        round_money("abc", "EUR")


def test_hidden_nan_raises():
    with pytest.raises(ValueError):
        round_money("NaN", "EUR")


def test_hidden_exact_tie_bhd_half_even():
    # 1.0025 at 3 places: tie, even neighbour is 1.002.
    assert round_money("1.0025", "BHD", "HALF_EVEN") == Decimal("1.002")
    assert round_money("1.0035", "BHD", "HALF_EVEN") == Decimal("1.004")
