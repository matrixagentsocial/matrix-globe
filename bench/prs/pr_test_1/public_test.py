# --- public tests for allocate_ratios (module task_a.py) ---
from decimal import Decimal

import pytest

from task_a import allocate_by_ratios


def test_public_equal_split():
    assert allocate_by_ratios("100.00", [1, 1, 1]) == [Decimal("33.34"), Decimal("33.33"), Decimal("33.33")]


def test_public_weighted_split():
    assert allocate_by_ratios("10.00", [2, 1, 1]) == [Decimal("5.00"), Decimal("2.50"), Decimal("2.50")]


def test_public_zero_weight():
    assert allocate_by_ratios("100.00", [0, 1, 0]) == [Decimal("0.00"), Decimal("100.00"), Decimal("0.00")]


def test_public_five_cents():
    assert allocate_by_ratios("0.05", [1, 1]) == [Decimal("0.03"), Decimal("0.02")]


def test_public_empty_ratios_raises():
    with pytest.raises(ValueError):
        allocate_by_ratios("10.00", [])

# --- public tests for apr_apy (module task_b.py) ---
from decimal import Decimal

import pytest

from task_b import apr_to_apy, apy_to_apr


def test_public_apr_monthly():
    assert apr_to_apy("12", "monthly") == Decimal("12.682503")


def test_public_apr_continuous():
    assert apr_to_apy("12", "continuous") == Decimal("12.749685")


def test_public_apy_to_apr_monthly():
    assert apy_to_apr("12.682503", "monthly") == Decimal("12.000000")


def test_public_zero():
    assert apr_to_apy("0", "monthly") == Decimal("0.000000")
    assert apy_to_apr("0", "daily") == Decimal("0.000000")


def test_public_bad_frequency():
    with pytest.raises(ValueError):
        apr_to_apy("12", "hourly")

# --- public tests for bank_reconciliation (module task_c.py) ---
from decimal import Decimal

import pytest

from task_c import reconcile


def test_public_exact_match():
    r = reconcile(
        [{"id": "b1", "date": "2024-01-05", "amount": "100.00"}],
        [{"id": "k1", "date": "2024-01-06", "amount": "100.00"}],
    )
    assert r == {"matches": [{"bank_id": "k1", "book_ids": ["b1"]}], "unmatched_book": [], "unmatched_bank": []}


def test_public_one_to_many():
    r = reconcile(
        [{"id": "b1", "date": "2024-01-05", "amount": "60.00"}, {"id": "b2", "date": "2024-01-05", "amount": "40.00"}],
        [{"id": "k1", "date": "2024-01-05", "amount": "100.00"}],
    )
    assert r["matches"] == [{"bank_id": "k1", "book_ids": ["b1", "b2"]}]


def test_public_unmatched_reported():
    r = reconcile([{"id": "b1", "date": "2024-01-05", "amount": "10.00"}], [])
    assert r["unmatched_book"] == ["b1"]
    assert r["matches"] == []


def test_public_bad_tolerance_raises():
    with pytest.raises(ValueError):
        reconcile([], [], tolerance_days=32)


def test_public_empty():
    assert reconcile([], []) == {"matches": [], "unmatched_book": [], "unmatched_bank": []}
