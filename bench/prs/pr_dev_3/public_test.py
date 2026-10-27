# --- public tests for number_parsing (module task_a.py) ---
from decimal import Decimal

from task_a import parse_number


def test_european_format():
    assert parse_number("1.234,56") == Decimal("1234.56")


def test_us_format():
    assert parse_number("1,234.56") == Decimal("1234.56")


def test_parentheses_negative():
    assert parse_number("(1.234,56)") == Decimal("-1234.56")


def test_space_thousands_european():
    assert parse_number("-1 234,56") == Decimal("-1234.56")


def test_plain_integer():
    assert parse_number("42") == Decimal("42")

# --- public tests for receivables_aging (module task_b.py) ---
from datetime import date
from decimal import Decimal

from task_b import aging_buckets


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

# --- public tests for split_installments (module task_c.py) ---
from decimal import Decimal

import pytest

from task_c import split_installments


def test_split_even():
    assert split_installments("90.00", 3) == [Decimal("30.00")] * 3


def test_split_remainder_first():
    assert split_installments("100.00", 3) == [
        Decimal("33.34"),
        Decimal("33.33"),
        Decimal("33.33"),
    ]


def test_split_sums_exactly():
    parts = split_installments("10.00", 6)
    assert sum(parts) == Decimal("10.00")
    assert len(parts) == 6


def test_split_single():
    assert split_installments("42.50", 1) == [Decimal("42.50")]


def test_split_zero_n_raises():
    with pytest.raises(ValueError):
        split_installments("10.00", 0)
