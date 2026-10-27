# --- public tests for progressive_tax (module task_a.py) ---
from decimal import Decimal

import pytest

from task_a import effective_rate_percent, income_tax, tax_breakdown


def test_public_tax_below_first_threshold():
    assert income_tax("10000") == Decimal("1900.00")


def test_public_tax_at_first_threshold():
    assert income_tax("12450") == Decimal("2365.50")


def test_public_tax_at_second_threshold():
    assert income_tax("20200") == Decimal("4225.50")


def test_public_tax_mid_bracket_and_breakdown():
    assert income_tax("50000") == Decimal("14201.50")
    rows = tax_breakdown("50000")
    assert [r["tax"] for r in rows] == [
        Decimal("2365.50"),
        Decimal("1860.00"),
        Decimal("4500.00"),
        Decimal("5476.00"),
    ]


def test_public_effective_rate():
    assert effective_rate_percent("50000") == Decimal("28.4030")
    assert effective_rate_percent("0") == Decimal("0.0000")

# --- public tests for prorata_billing (module task_b.py) ---
from decimal import Decimal

from task_b import prorate_period


def test_public_worked_example():
    result = prorate_period(
        "2024-03-01",
        "2024-04-01",
        [
            {"date": "2024-03-01", "monthly_price": "31.00"},
            {"date": "2024-03-16", "monthly_price": "62.00"},
        ],
    )
    assert result["period_days"] == 31
    assert result["segments"] == [
        {"from": "2024-03-01", "to": "2024-03-16", "days": 15, "monthly_price": Decimal("31.00"), "amount": Decimal("15.00")},
        {"from": "2024-03-16", "to": "2024-04-01", "days": 16, "monthly_price": Decimal("62.00"), "amount": Decimal("32.00")},
    ]
    assert result["total"] == Decimal("47.00")


def test_public_single_plan_full_month():
    result = prorate_period("2024-01-01", "2024-02-01", [{"date": "2024-01-01", "monthly_price": "100.00"}])
    assert result["total"] == Decimal("100.00")
    assert len(result["segments"]) == 1


def test_public_leap_february():
    result = prorate_period("2024-02-01", "2024-03-01", [{"date": "2024-02-01", "monthly_price": "29.00"}])
    assert result["period_days"] == 29
    assert result["segments"][0]["days"] == 29
    assert result["total"] == Decimal("29.00")


def test_public_unsorted_changes():
    result = prorate_period(
        "2024-03-01",
        "2024-04-01",
        [
            {"date": "2024-03-16", "monthly_price": "62.00"},
            {"date": "2024-03-01", "monthly_price": "31.00"},
        ],
    )
    assert result["total"] == Decimal("47.00")

# --- public tests for rf_reference (module task_c.py) ---
import pytest

from task_c import is_valid_rf_reference, rf_reference


def test_public_generate_known_example():
    # ISO 11649 style example: base 539007547034 has check digits 18.
    assert rf_reference("539007547034") == "RF18539007547034"


def test_public_generate_small_base():
    # Numeric "1271500"; 1271500 % 97 = 24; 98 - 24 = 74.
    assert rf_reference("1") == "RF741"


def test_public_validate_generated():
    assert is_valid_rf_reference("RF18539007547034") is True
    assert is_valid_rf_reference(rf_reference("HELLO123")) is True


def test_public_validate_wrong_check_digits():
    assert is_valid_rf_reference("RF751") is False


def test_public_generate_empty_raises():
    with pytest.raises(ValueError):
        rf_reference("")
