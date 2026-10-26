from datetime import date
from decimal import Decimal

from solution import aging_buckets


def test_current_invoice():
    result = aging_buckets(
        [{"due_date": date(2024, 6, 15), "amount": "100.00"}], date(2024, 6, 10)
    )
    assert result["current"] == Decimal("100.00")


def test_due_today_is_current():
    result = aging_buckets(
        [{"due_date": "2024-06-10", "amount": "50.00"}], date(2024, 6, 10)
    )
    assert result["current"] == Decimal("50.00")


def test_thirty_days_in_first_bucket():
    result = aging_buckets(
        [{"due_date": date(2024, 5, 11), "amount": "10.00"}], date(2024, 6, 10)
    )
    assert result["1-30"] == Decimal("10.00")


def test_all_keys_present_empty():
    result = aging_buckets([], date(2024, 6, 10))
    assert list(result) == ["current", "1-30", "31-60", "61-90", "90+"]
    assert all(v == Decimal("0.00") for v in result.values())


def test_old_invoice_in_90_plus():
    result = aging_buckets(
        [{"due_date": date(2024, 1, 1), "amount": "7.50"}], date(2024, 6, 10)
    )
    assert result["90+"] == Decimal("7.50")
