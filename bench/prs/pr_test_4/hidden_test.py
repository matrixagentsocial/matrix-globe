# --- hidden tests for idempotent_ledger (module task_a.py) ---
from decimal import Decimal

import pytest

from task_a import process_payments


def _req(key, account="A", currency="EUR", amount="10.00", reference="r"):
    return {"key": key, "account": account, "currency": currency, "amount": amount, "reference": reference}


def test_hidden_currency_normalized_and_amount_quantized():
    result = process_payments([_req("k1", currency="usd", amount="10.5")])
    assert result["applied"][0]["currency"] == "USD"
    assert result["applied"][0]["amount"] == Decimal("10.50")
    assert result["balances"] == {"A:USD": Decimal("10.50")}


def test_hidden_separate_account_currency_balances():
    result = process_payments(
        [
            _req("k1", account="A", currency="EUR", amount="10.00"),
            _req("k2", account="A", currency="USD", amount="3.00"),
            _req("k3", account="B", currency="EUR", amount="1.25"),
            _req("k4", account="A", currency="EUR", amount="0.75"),
        ]
    )
    assert list(result["balances"].keys()) == ["A:EUR", "A:USD", "B:EUR"]
    assert result["balances"] == {"A:EUR": Decimal("10.75"), "A:USD": Decimal("3.00"), "B:EUR": Decimal("1.25")}
    assert result["applied"][-1]["balance_after"] == Decimal("10.75")


def test_hidden_duplicate_twice_counts_twice():
    result = process_payments([_req("k1"), _req("k1"), _req("k1")])
    assert result["duplicates"] == ["k1", "k1"]
    assert len(result["applied"]) == 1


def test_hidden_conflict_twice_and_compared_to_first():
    result = process_payments([_req("k1"), _req("k1", amount="11.00"), _req("k1", amount="11.00"), _req("k1")])
    assert len(result["conflicts"]) == 2
    # The last request matches the first again, so it is a duplicate, not a conflict.
    assert result["duplicates"] == ["k1"]
    assert result["balances"] == {"A:EUR": Decimal("10.00")}


def test_hidden_conflict_on_reference_only():
    result = process_payments([_req("k1", reference="a"), _req("k1", reference="b")])
    assert result["conflicts"] == [{"key": "k1", "reason": "payload differs from first occurrence"}]
    assert result["duplicates"] == []


def test_hidden_conflict_on_account_case():
    result = process_payments([_req("k1", account="A"), _req("k1", account="a")])
    assert len(result["conflicts"]) == 1


def test_hidden_conflict_account_creates_no_balance():
    result = process_payments([_req("k1", account="A"), _req("k1", account="B")])
    assert list(result["balances"].keys()) == ["A:EUR"]


def test_hidden_duplicate_order_multiple_keys():
    result = process_payments([_req("k1"), _req("k2", amount="2.00"), _req("k2", amount="2.00"), _req("k1")])
    assert result["duplicates"] == ["k2", "k1"]


def test_hidden_applied_order_and_running_balance():
    result = process_payments([_req("k2", amount="5.00"), _req("k1", amount="1.00"), _req("k3", currency="USD", amount="2.00")])
    assert [a["key"] for a in result["applied"]] == ["k2", "k1", "k3"]
    assert [a["balance_after"] for a in result["applied"]] == [Decimal("5.00"), Decimal("6.00"), Decimal("2.00")]


def test_hidden_invalid_amounts_raise():
    for bad in ["0.00", "-1.00", "10.005", "abc", "", "NaN", "Infinity"]:
        with pytest.raises(ValueError):
            process_payments([_req("k1", amount=bad)])


def test_hidden_invalid_repeat_still_raises():
    with pytest.raises(ValueError):
        process_payments([_req("k1"), _req("k1", amount="-5.00")])


def test_hidden_invalid_currency_raises():
    for bad in ["EU", "EURO", "E1R", "", 123]:
        with pytest.raises(ValueError):
            process_payments([_req("k1", currency=bad)])


def test_hidden_empty_key_or_account_raises():
    with pytest.raises(ValueError):
        process_payments([_req("")])
    with pytest.raises(ValueError):
        process_payments([_req("k1", account="")])


def test_hidden_missing_field_and_non_dict_raise():
    with pytest.raises(ValueError):
        process_payments([{"key": "k1", "account": "A", "currency": "EUR", "amount": "1.00"}])
    with pytest.raises(ValueError):
        process_payments(["not-a-dict"])


def test_hidden_non_string_reference_raises():
    with pytest.raises(ValueError):
        process_payments([_req("k1", reference=None)])


def test_hidden_empty_reference_allowed():
    result = process_payments([_req("k1", reference="")])
    assert len(result["applied"]) == 1


def test_hidden_non_list_raises():
    with pytest.raises(ValueError):
        process_payments("k1")


def test_hidden_same_key_different_keys_independent():
    # Same payload under a different key is a separate applied payment.
    result = process_payments([_req("k1"), _req("k2")])
    assert len(result["applied"]) == 2
    assert result["balances"] == {"A:EUR": Decimal("20.00")}

# --- hidden tests for madrid_cutoff (module task_b.py) ---
import pytest

from task_b import is_madrid_business_day, payment_value_date


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

# --- hidden tests for percent_change (module task_c.py) ---
from decimal import Decimal

import pytest

from task_c import apply_percent_change, percent_change


def test_hidden_decrease_rounding():
    assert percent_change("110", "100") == Decimal("-9.09")


def test_hidden_negative_base_rise():
    assert percent_change("-200", "-100") == Decimal("50.00")


def test_hidden_negative_base_fall():
    assert percent_change("-200", "-300") == Decimal("-50.00")


def test_hidden_negative_base_small():
    assert percent_change("-100", "-50") == Decimal("50.00")
    assert percent_change("-100", "-150") == Decimal("-50.00")


def test_hidden_small_values():
    assert percent_change("3", "2") == Decimal("-33.33")


def test_hidden_zero_variants():
    assert percent_change("0.00", "0.00") == Decimal("0.00")
    assert percent_change("-0", "0") == Decimal("0.00")
    assert percent_change("0", "-5") is None


def test_hidden_same_value_zero_change():
    assert percent_change("42.50", "42.50") == Decimal("0.00")


def test_hidden_half_up_rounding():
    # 1/800*100 = 0.125 -> 0.13 with HALF_UP.
    assert percent_change("800", "801") == Decimal("0.13")


def test_hidden_two_dp_exponent():
    assert percent_change("100", "110").as_tuple().exponent == -2
    assert apply_percent_change("100.00", "10").as_tuple().exponent == -2


def test_hidden_apply_negative_percent():
    assert apply_percent_change("100.00", "-10") == Decimal("90.00")


def test_hidden_apply_fractional_percent():
    assert apply_percent_change("50.00", "2.5") == Decimal("51.25")


def test_hidden_apply_zero_old():
    assert apply_percent_change("0.00", "10") == Decimal("0.00")


def test_hidden_apply_rounding():
    assert apply_percent_change("33.33", "10") == Decimal("36.66")


def test_hidden_apply_negative_old():
    assert apply_percent_change("-100.00", "10") == Decimal("-110.00")


def test_hidden_nan_raises():
    with pytest.raises(ValueError):
        percent_change("NaN", "5")


def test_hidden_infinity_percent_raises():
    with pytest.raises(ValueError):
        apply_percent_change("100.00", "Infinity")


def test_hidden_empty_raises():
    with pytest.raises(ValueError):
        apply_percent_change("", "10")


def test_hidden_many_dp_accepted():
    assert percent_change("10.005", "10.005") == Decimal("0.00")
