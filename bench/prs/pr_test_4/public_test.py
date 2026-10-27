# --- public tests for idempotent_ledger (module task_a.py) ---
from decimal import Decimal

from task_a import process_payments


def _req(key, account="A", currency="EUR", amount="10.00", reference="r"):
    return {"key": key, "account": account, "currency": currency, "amount": amount, "reference": reference}


def test_public_single_payment_applied():
    result = process_payments([_req("k1")])
    assert result["applied"] == [
        {"key": "k1", "account": "A", "currency": "EUR", "amount": Decimal("10.00"), "balance_after": Decimal("10.00")}
    ]
    assert result["balances"] == {"A:EUR": Decimal("10.00")}


def test_public_worked_example_duplicate():
    result = process_payments(
        [
            _req("k1", currency="eur", amount="10.00", reference="r1"),
            _req("k2", amount="5.50", reference=""),
            _req("k1", amount="10.0", reference="r1"),
        ]
    )
    assert [a["balance_after"] for a in result["applied"]] == [Decimal("10.00"), Decimal("15.50")]
    assert result["duplicates"] == ["k1"]
    assert result["conflicts"] == []
    assert result["balances"] == {"A:EUR": Decimal("15.50")}


def test_public_conflict_not_applied():
    result = process_payments([_req("k1"), _req("k1", amount="11.00")])
    assert len(result["applied"]) == 1
    assert result["conflicts"] == [{"key": "k1", "reason": "payload differs from first occurrence"}]
    assert result["balances"] == {"A:EUR": Decimal("10.00")}


def test_public_empty_list():
    assert process_payments([]) == {"applied": [], "duplicates": [], "conflicts": [], "balances": {}}

# --- public tests for madrid_cutoff (module task_b.py) ---
import pytest

from task_b import is_madrid_business_day, payment_value_date


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

# --- public tests for percent_change (module task_c.py) ---
from decimal import Decimal

import pytest

from task_c import apply_percent_change, percent_change


def test_public_increase():
    assert percent_change("100", "110") == Decimal("10.00")


def test_public_zero_to_nonzero_none():
    assert percent_change("0", "5") is None


def test_public_zero_to_zero():
    assert percent_change("0", "0") == Decimal("0.00")


def test_public_apply():
    assert apply_percent_change("100.00", "10") == Decimal("110.00")


def test_public_bad_input_raises():
    with pytest.raises(ValueError):
        percent_change("abc", "5")
