# --- public tests for duplicate_payments (module task_a.py) ---
from decimal import Decimal

import pytest

from task_a import find_duplicate_payments


def _p(pid, d, vendor, amount="100.00", currency="EUR"):
    return {"id": pid, "date": d, "vendor": vendor, "amount": amount, "currency": currency}


def test_public_basic_group():
    result = find_duplicate_payments([_p("p1", "2024-01-01", "Acme Ltd"), _p("p2", "2024-01-05", "ACME, LTD.")])
    assert result == [{"payment_ids": ["p1", "p2"], "vendor": "ACME", "amount": Decimal("100.00"), "currency": "EUR"}]


def test_public_no_duplicates():
    assert find_duplicate_payments([_p("p1", "2024-01-01", "Acme"), _p("p2", "2024-03-01", "Acme")]) == []


def test_public_empty():
    assert find_duplicate_payments([]) == []


def test_public_duplicate_id_raises():
    with pytest.raises(ValueError):
        find_duplicate_payments([_p("p1", "2024-01-01", "Acme"), _p("p1", "2024-01-02", "Acme")])


def test_public_window_boundary():
    result = find_duplicate_payments([_p("p1", "2024-01-01", "Acme"), _p("p2", "2024-01-08", "Acme")], window_days=7)
    assert len(result) == 1

# --- public tests for eom_roll (module task_b.py) ---
import pytest

from task_b import add_months, monthly_schedule


def test_public_jan31_plus_one_leap():
    assert add_months("2024-01-31", 1) == "2024-02-29"


def test_public_feb28_sticky():
    assert add_months("2023-02-28", 1) == "2023-03-31"


def test_public_plain_day_kept():
    assert add_months("2023-02-27", 1) == "2023-03-27"


def test_public_schedule_anchored():
    assert monthly_schedule("2024-01-31", 3) == [
        "2024-02-29",
        "2024-03-31",
        "2024-04-30",
    ]


def test_public_months_out_of_range_raises():
    with pytest.raises(ValueError):
        add_months("2024-01-15", 2401)

# --- public tests for fx_triangulation (module task_c.py) ---
from decimal import Decimal

import pytest

from task_c import convert_fx, cross_rate

RATES = {"USD": "1.10", "GBP": "0.88", "JPY": "160"}


def test_public_usd_to_gbp_example():
    assert convert_fx("110", "USD", "GBP", RATES) == Decimal("88.00")


def test_public_eur_to_jpy_zero_places():
    assert convert_fx("100", "EUR", "JPY", RATES) == Decimal("16000")


def test_public_cross_rate():
    assert cross_rate("USD", "GBP", RATES) == Decimal("0.8000000000")


def test_public_same_currency_rounds():
    assert convert_fx("10.005", "USD", "USD", RATES) == Decimal("10.01")


def test_public_unknown_currency_raises():
    with pytest.raises(ValueError):
        convert_fx("10", "USD", "XXX", RATES)
