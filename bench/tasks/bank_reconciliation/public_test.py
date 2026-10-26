from decimal import Decimal

import pytest

from solution import reconcile


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
