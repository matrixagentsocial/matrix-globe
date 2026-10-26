from decimal import Decimal

import pytest

from solution import closing_balance, running_balance


def _tx(i, v, b, a):
    return {"id": i, "value_date": v, "booking_date": b, "amount": a}


def test_public_worked_example():
    txs = [_tx("b", "2024-01-02", "2024-01-03", "10.00"), _tx("a", "2024-01-02", "2024-01-02", "-30.00"), _tx("c", "2024-01-01", "2024-01-05", "5.00")]
    rows = running_balance(txs, "100.00")
    assert [r["id"] for r in rows] == ["c", "a", "b"]
    assert [r["balance"] for r in rows] == [Decimal("105.00"), Decimal("75.00"), Decimal("85.00")]
    assert closing_balance(txs, "100.00") == Decimal("85.00")


def test_public_empty():
    assert running_balance([], "42.50") == []
    assert closing_balance([], "42.50") == Decimal("42.50")


def test_public_single():
    rows = running_balance([_tx("x", "2024-01-01", "2024-01-01", "-10.00")], "100.00")
    assert rows[0]["balance"] == Decimal("90.00")


def test_public_duplicate_id_raises():
    with pytest.raises(ValueError):
        running_balance([_tx("x", "2024-01-01", "2024-01-01", "1.00"), _tx("x", "2024-01-02", "2024-01-02", "1.00")], "0.00")


def test_public_bad_date_raises():
    with pytest.raises(ValueError):
        running_balance([_tx("x", "2024-13-01", "2024-01-01", "1.00")], "0.00")
