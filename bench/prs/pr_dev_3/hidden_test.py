# --- hidden tests for number_parsing (module task_a.py) ---
from decimal import Decimal

import pytest

from task_a import parse_number


def test_hidden_single_comma_is_decimal():
    assert parse_number("1,234") == Decimal("1.234")


def test_hidden_single_dot_is_decimal():
    assert parse_number("1.234") == Decimal("1.234")


def test_hidden_multiple_commas_are_thousands():
    assert parse_number("1,234,567") == Decimal("1234567")


def test_hidden_multiple_dots_are_thousands():
    assert parse_number("1.234.567") == Decimal("1234567")


def test_hidden_full_european_millions():
    assert parse_number("1.234.567,89") == Decimal("1234567.89")


def test_hidden_full_us_millions():
    assert parse_number("1,234,567.89") == Decimal("1234567.89")


def test_hidden_nbsp_thousands():
    assert parse_number("1\u00a0234,56") == Decimal("1234.56")


def test_hidden_plus_sign():
    assert parse_number("+12,5") == Decimal("12.5")


def test_hidden_parentheses_us_format():
    assert parse_number("(1,234.56)") == Decimal("-1234.56")


def test_hidden_surrounding_whitespace():
    assert parse_number("  1.234,56  ") == Decimal("1234.56")


def test_hidden_zero_decimal():
    assert parse_number("0,00") == Decimal("0.00")


def test_hidden_negative_decimal_comma():
    assert parse_number("-0,5") == Decimal("-0.5")


def test_hidden_bad_grouping_commas_raises():
    with pytest.raises(ValueError):
        parse_number("12,34,56")


def test_hidden_bad_grouping_dots_raises():
    with pytest.raises(ValueError):
        parse_number("1.23.456")


def test_hidden_sign_with_parentheses_raises():
    with pytest.raises(ValueError):
        parse_number("-(1,5)")


def test_hidden_sign_inside_parentheses_raises():
    with pytest.raises(ValueError):
        parse_number("(-1,5)")


def test_hidden_empty_raises():
    with pytest.raises(ValueError):
        parse_number("")


def test_hidden_letters_raise():
    with pytest.raises(ValueError):
        parse_number("12a34")


def test_hidden_trailing_separator_raises():
    with pytest.raises(ValueError):
        parse_number("5.")


def test_hidden_leading_separator_raises():
    with pytest.raises(ValueError):
        parse_number(".5")


def test_hidden_double_sign_raises():
    with pytest.raises(ValueError):
        parse_number("--5")

# --- hidden tests for receivables_aging (module task_b.py) ---
from datetime import date
from decimal import Decimal

import pytest

from task_b import aging_buckets

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

# --- hidden tests for split_installments (module task_c.py) ---
from decimal import Decimal

import pytest

from task_c import split_installments


def test_hidden_one_cent_three_ways():
    assert split_installments("0.01", 3) == [
        Decimal("0.01"),
        Decimal("0.00"),
        Decimal("0.00"),
    ]


def test_hidden_five_cents_two_ways():
    assert split_installments("0.05", 2) == [Decimal("0.03"), Decimal("0.02")]


def test_hidden_zero_total():
    assert split_installments("0.00", 4) == [Decimal("0.00")] * 4


def test_hidden_large_remainder_order():
    parts = split_installments("100.00", 7)
    # 10000 cents = 7 * 1428 + 4, so the first 4 get the extra cent.
    assert parts[:4] == [Decimal("14.29")] * 4
    assert parts[4:] == [Decimal("14.28")] * 3
    assert sum(parts) == Decimal("100.00")


def test_hidden_max_spread_one_cent():
    parts = split_installments("99.99", 13)
    assert max(parts) - min(parts) <= Decimal("0.01")
    assert sum(parts) == Decimal("99.99")


def test_hidden_two_decimal_exponent():
    for part in split_installments("10.01", 3):
        assert part.as_tuple().exponent == -2


def test_hidden_integer_string_total():
    assert split_installments("100", 4) == [Decimal("25.00")] * 4


def test_hidden_one_decimal_total():
    assert split_installments("10.5", 2) == [Decimal("5.25"), Decimal("5.25")]


def test_hidden_negative_total_raises():
    with pytest.raises(ValueError):
        split_installments("-1.00", 2)


def test_hidden_three_decimals_raises():
    with pytest.raises(ValueError):
        split_installments("10.005", 2)


def test_hidden_non_numeric_raises():
    with pytest.raises(ValueError):
        split_installments("abc", 2)


def test_hidden_empty_raises__split_installments():
    with pytest.raises(ValueError):
        split_installments("", 2)


def test_hidden_nan_raises():
    with pytest.raises(ValueError):
        split_installments("NaN", 2)


def test_hidden_negative_n_raises():
    with pytest.raises(ValueError):
        split_installments("10.00", -2)


def test_hidden_float_n_raises():
    with pytest.raises(ValueError):
        split_installments("10.00", 2.5)


def test_hidden_bool_n_raises():
    with pytest.raises(ValueError):
        split_installments("10.00", True)


def test_hidden_many_installments_sum():
    parts = split_installments("1234.56", 100)
    assert len(parts) == 100
    assert sum(parts) == Decimal("1234.56")
