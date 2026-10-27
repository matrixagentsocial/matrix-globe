# --- hidden tests for duplicate_payments (module task_a.py) ---
from decimal import Decimal

import pytest

from task_a import find_duplicate_payments


def _p(pid, d, vendor, amount="100.00", currency="EUR"):
    return {"id": pid, "date": d, "vendor": vendor, "amount": amount, "currency": currency}


def test_hidden_legal_suffix_punct_case_variants():
    result = find_duplicate_payments([_p("p1", "2024-01-01", "ACME, S.L."), _p("p2", "2024-01-03", "acme sl"), _p("p3", "2024-01-04", "Acme S.L.U.")])
    assert result == [{"payment_ids": ["p1", "p2", "p3"], "vendor": "ACME", "amount": Decimal("100.00"), "currency": "EUR"}]


def test_hidden_chain_transitive_group():
    result = find_duplicate_payments([_p("a", "2024-01-01", "Acme"), _p("b", "2024-01-07", "Acme"), _p("c", "2024-01-13", "Acme")], window_days=7)
    assert len(result) == 1
    assert result[0]["payment_ids"] == ["a", "b", "c"]


def test_hidden_same_amount_different_vendor_no():
    assert find_duplicate_payments([_p("p1", "2024-01-01", "Acme"), _p("p2", "2024-01-01", "Other")]) == []


def test_hidden_refund_sign_not_duplicate():
    assert find_duplicate_payments([_p("p1", "2024-01-01", "Acme", "50.00"), _p("p2", "2024-01-01", "Acme", "-50.00")]) == []


def test_hidden_window_exactly_n_yes():
    result = find_duplicate_payments([_p("p1", "2024-01-01", "Acme"), _p("p2", "2024-01-11", "Acme")], window_days=10)
    assert len(result) == 1


def test_hidden_window_n_plus_one_no():
    assert find_duplicate_payments([_p("p1", "2024-01-01", "Acme"), _p("p2", "2024-01-12", "Acme")], window_days=10) == []


def test_hidden_different_currency_no():
    assert find_duplicate_payments([_p("p1", "2024-01-01", "Acme", currency="EUR"), _p("p2", "2024-01-01", "Acme", currency="USD")]) == []


def test_hidden_currency_case_normalized():
    result = find_duplicate_payments([_p("p1", "2024-01-01", "Acme", currency="eur"), _p("p2", "2024-01-01", "Acme", currency=" EUR ")])
    assert len(result) == 1 and result[0]["currency"] == "EUR"


def test_hidden_ids_sorted_by_date_then_id():
    result = find_duplicate_payments([_p("z", "2024-01-02", "Acme"), _p("a", "2024-01-02", "Acme"), _p("m", "2024-01-01", "Acme")])
    assert result[0]["payment_ids"] == ["m", "a", "z"]


def test_hidden_groups_sorted_by_earliest_date():
    payments = [_p("b1", "2024-02-01", "Beta", "20.00"), _p("b2", "2024-02-02", "Beta", "20.00"), _p("a1", "2024-01-01", "Acme"), _p("a2", "2024-01-02", "Acme")]
    result = find_duplicate_payments(payments)
    assert [g["vendor"] for g in result] == ["ACME", "BETA"]


def test_hidden_bad_date_raises():
    with pytest.raises(ValueError):
        find_duplicate_payments([_p("p1", "2024-02-30", "Acme")])


def test_hidden_bad_amount_raises():
    with pytest.raises(ValueError):
        find_duplicate_payments([_p("p1", "2024-01-01", "Acme", "abc")])


def test_hidden_window_too_large_raises():
    with pytest.raises(ValueError):
        find_duplicate_payments([], window_days=366)


def test_hidden_negative_window_raises():
    with pytest.raises(ValueError):
        find_duplicate_payments([], window_days=-1)


def test_hidden_empty_normalized_vendor_raises():
    with pytest.raises(ValueError):
        find_duplicate_payments([_p("p1", "2024-01-01", "LTD")])


def test_hidden_repeated_legal_suffix_dropped():
    result = find_duplicate_payments([_p("p1", "2024-01-01", "Acme Limited Ltd"), _p("p2", "2024-01-01", "ACME")])
    assert len(result) == 1 and result[0]["vendor"] == "ACME"


def test_hidden_leading_legal_token_kept():
    # "SA Holdings" -> "SA HOLDINGS" (leading SA not dropped), so not a duplicate of "Holdings".
    assert find_duplicate_payments([_p("p1", "2024-01-01", "SA Holdings"), _p("p2", "2024-01-01", "Holdings")]) == []


def test_hidden_amount_three_dp_raises():
    with pytest.raises(ValueError):
        find_duplicate_payments([_p("p1", "2024-01-01", "Acme", "10.005")])

# --- hidden tests for eom_roll (module task_b.py) ---
import pytest

from task_b import add_months, monthly_schedule


def test_hidden_jan31_plus_two_returns_to_31():
    assert add_months("2024-01-31", 2) == "2024-03-31"


def test_hidden_jan31_plus_one_non_leap():
    assert add_months("2023-01-31", 1) == "2023-02-28"


def test_hidden_leap_day_plus_twelve():
    assert add_months("2024-02-29", 12) == "2025-02-28"


def test_hidden_leap_day_plus_one_sticky():
    assert add_months("2024-02-29", 1) == "2024-03-31"


def test_hidden_mar31_minus_one_leap():
    assert add_months("2024-03-31", -1) == "2024-02-29"


def test_hidden_mar31_minus_one_non_leap():
    assert add_months("2023-03-31", -1) == "2023-02-28"


def test_hidden_apr30_plus_one_sticky_to_31():
    # 2023-04-30 is the last day of April, so it sticks to 2023-05-31.
    assert add_months("2023-04-30", 1) == "2023-05-31"


def test_hidden_apr29_plus_one_not_sticky():
    assert add_months("2023-04-29", 1) == "2023-05-29"


def test_hidden_clamp_without_sticky():
    # May 31 -> April has only 30 days (clamp; also end-of-month).
    assert add_months("2023-05-31", -1) == "2023-04-30"


def test_hidden_year_rollover_forward():
    assert add_months("2024-12-15", 1) == "2025-01-15"
    assert add_months("2024-01-31", -1) == "2023-12-31"


def test_hidden_zero_months_identity():
    assert add_months("2023-06-15", 0) == "2023-06-15"
    assert add_months("2024-02-29", 0) == "2024-02-29"


def test_hidden_months_extreme_bounds():
    assert add_months("2023-06-30", 2400) == "2223-06-30"
    assert add_months("2023-06-15", -2400) == "1823-06-15"


def test_hidden_months_out_of_bounds_raise():
    with pytest.raises(ValueError):
        add_months("2023-06-15", -2401)
    with pytest.raises(ValueError):
        add_months("2023-06-15", 2401)


def test_hidden_months_type_errors():
    with pytest.raises(ValueError):
        add_months("2023-06-15", True)
    with pytest.raises(ValueError):
        add_months("2023-06-15", 1.5)
    with pytest.raises(ValueError):
        add_months("2023-06-15", "2")


def test_hidden_bad_dates_raise():
    with pytest.raises(ValueError):
        add_months("2023-02-29", 1)
    with pytest.raises(ValueError):
        add_months("2023-13-01", 1)
    with pytest.raises(ValueError):
        add_months("not-a-date", 1)
    with pytest.raises(ValueError):
        add_months(20230615, 1)


def test_hidden_schedule_anchor_not_iterative():
    # Anchored: Jan 30 -> Feb 28 (clamp) -> Mar 30 (from Jan 30).
    # Iterative stepping would give Mar 31 because Feb 28 is EOM.
    assert monthly_schedule("2023-01-30", 2) == ["2023-02-28", "2023-03-30"]


def test_hidden_schedule_feb28_anchor():
    assert monthly_schedule("2023-02-28", 2) == ["2023-03-31", "2023-04-30"]


def test_hidden_schedule_mid_month_and_length():
    assert monthly_schedule("2023-01-15", 3) == [
        "2023-02-15",
        "2023-03-15",
        "2023-04-15",
    ]
    schedule = monthly_schedule("2023-06-15", 120)
    assert len(schedule) == 120
    assert schedule[-1] == "2033-06-15"


def test_hidden_schedule_count_bounds():
    assert monthly_schedule("2023-01-15", 1) == ["2023-02-15"]
    with pytest.raises(ValueError):
        monthly_schedule("2023-01-15", 0)
    with pytest.raises(ValueError):
        monthly_schedule("2023-01-15", 121)
    with pytest.raises(ValueError):
        monthly_schedule("2023-01-15", True)


def test_hidden_schedule_bad_start_raises():
    with pytest.raises(ValueError):
        monthly_schedule("2023-02-29", 3)

# --- hidden tests for fx_triangulation (module task_c.py) ---
from decimal import Decimal

import pytest

from task_c import convert_fx, cross_rate

RATES = {"USD": "1.10", "GBP": "0.88", "JPY": "160", "KRW": "1400", "CHF": "0.95"}


def test_hidden_lowercase_codes():
    assert convert_fx("110", "usd", "gbp", RATES) == Decimal("88.00")


def test_hidden_lowercase_rate_keys():
    assert convert_fx("110", "USD", "GBP", {"usd": "1.10", "gbp": "0.88"}) == Decimal("88.00")


def test_hidden_eur_omitted_and_to_eur():
    assert convert_fx("110", "USD", "EUR", {"USD": "1.10"}) == Decimal("100.00")


def test_hidden_eur_rate_not_one_raises():
    with pytest.raises(ValueError):
        convert_fx("10", "EUR", "USD", {"EUR": "1.01", "USD": "1.10"})


def test_hidden_no_intermediate_rounding():
    # 1 / 3 = 0.333... EUR; * 3 back would be 1 if rounded, exact chain: 1/3*2 -> 0.67 (via rate 2 currency XYZ known, 2dp)
    assert convert_fx("1", "AAA", "BBB", {"AAA": "3", "BBB": "2"}) == Decimal("0.67")


def test_hidden_unknown_currency_uses_two_minor_units():
    # XYZ is only known because it is in rates; outside table -> 2dp
    assert convert_fx("10", "EUR", "XYZ", {"XYZ": "2.005"}) == Decimal("20.05")


def test_hidden_jpy_half_up_zero_dp():
    # 1 EUR = 160.5 JPY -> 161 at 0dp HALF_UP (use exact rate)
    assert convert_fx("1", "EUR", "JPY", {"JPY": "160.5"}) == Decimal("161")


def test_hidden_negative_half_up_away_from_zero():
    assert convert_fx("-100.5", "JPY", "JPY", {"JPY": "160"}) == Decimal("-101")


def test_hidden_negative_conversion():
    assert convert_fx("-110", "USD", "GBP", RATES) == Decimal("-88.00")


def test_hidden_same_currency_unknown_no_lookup():
    assert convert_fx("10.004", "XYZ", "XYZ", {}) == Decimal("10.00")


def test_hidden_same_currency_bad_rates_ignored():
    assert convert_fx("10.00", "USD", "USD", {"USD": "0"}) == Decimal("10.00")


def test_hidden_krw_zero_dp_conversion():
    assert convert_fx("2", "EUR", "KRW", RATES) == Decimal("2800")


def test_hidden_cross_rate_same_known():
    result = cross_rate("USD", "USD", RATES)
    assert result == Decimal("1.0000000000")
    assert result.as_tuple().exponent == -10


def test_hidden_cross_rate_jpy_usd():
    # 1.10 / 160 = 0.006875 exactly
    assert cross_rate("JPY", "USD", RATES) == Decimal("0.0068750000")


def test_hidden_cross_rate_unknown_raises():
    with pytest.raises(ValueError):
        cross_rate("USD", "XXX", RATES)


def test_hidden_zero_rate_raises():
    with pytest.raises(ValueError):
        convert_fx("10", "USD", "GBP", {"USD": "0", "GBP": "0.88"})


def test_hidden_negative_unused_rate_raises():
    with pytest.raises(ValueError):
        convert_fx("10", "USD", "GBP", {"USD": "1.10", "GBP": "0.88", "CHF": "-1"})


def test_hidden_invalid_amount_raises():
    with pytest.raises(ValueError):
        convert_fx("NaN", "USD", "GBP", RATES)


def test_hidden_short_code_raises():
    with pytest.raises(ValueError):
        convert_fx("10", "US", "GBP", RATES)


def test_hidden_float_rate_raises():
    with pytest.raises(ValueError):
        convert_fx("10", "USD", "GBP", {"USD": 1.10, "GBP": "0.88"})
