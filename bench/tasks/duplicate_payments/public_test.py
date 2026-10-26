from decimal import Decimal

import pytest

from solution import find_duplicate_payments


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
