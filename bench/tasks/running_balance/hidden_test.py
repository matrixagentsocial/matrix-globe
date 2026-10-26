import copy
from decimal import Decimal

import pytest

from solution import closing_balance, running_balance


def _tx(i, v, b, a):
    return {"id": i, "value_date": v, "booking_date": b, "amount": a}


def test_hidden_tie_booking_date_order():
    txs = [_tx("b", "2024-01-02", "2024-01-03", "10.00"), _tx("a", "2024-01-02", "2024-01-02", "-30.00"), _tx("c", "2024-01-01", "2024-01-05", "5.00")]
    rows = running_balance(txs, "100.00")
    assert [r["id"] for r in rows] == ["c", "a", "b"]
    assert [r["balance"] for r in rows] == [Decimal("105.00"), Decimal("75.00"), Decimal("85.00")]
    assert closing_balance(txs, "100.00") == Decimal("85.00")


def test_hidden_tie_id_order_same_dates():
    txs = [_tx("b", "2024-01-01", "2024-01-01", "10.00"), _tx("a", "2024-01-01", "2024-01-01", "20.00"), _tx("c", "2024-01-01", "2024-01-01", "-5.00")]
    rows = running_balance(txs, "0.00")
    assert [r["id"] for r in rows] == ["a", "b", "c"]
    assert [r["balance"] for r in rows] == [Decimal("20.00"), Decimal("30.00"), Decimal("25.00")]


def test_hidden_id_plain_string_order():
    # plain string ascending: "10" < "2" < "a"
    txs = [_tx("a", "2024-01-01", "2024-01-01", "1.00"), _tx("2", "2024-01-01", "2024-01-01", "2.00"), _tx("10", "2024-01-01", "2024-01-01", "4.00")]
    rows = running_balance(txs, "0.00")
    assert [r["id"] for r in rows] == ["10", "2", "a"]
    assert [r["balance"] for r in rows] == [Decimal("4.00"), Decimal("6.00"), Decimal("7.00")]


def test_hidden_value_date_primary_over_booking():
    txs = [_tx("x", "2024-01-03", "2024-01-01", "100.00"), _tx("y", "2024-01-01", "2024-01-09", "1.00")]
    rows = running_balance(txs, "0.00")
    assert [r["id"] for r in rows] == ["y", "x"]
    assert [r["balance"] for r in rows] == [Decimal("1.00"), Decimal("101.00")]


def test_hidden_full_row_shape_and_normalization():
    rows = running_balance([_tx("x", "2024-01-01", "2024-01-02", "10.5")], "0")
    assert rows == [{"id": "x", "value_date": "2024-01-01", "booking_date": "2024-01-02", "amount": Decimal("10.50"), "balance": Decimal("10.50")}]
    assert rows[0]["amount"].as_tuple().exponent == -2
    assert rows[0]["balance"].as_tuple().exponent == -2


def test_hidden_zero_amount_allowed():
    rows = running_balance([_tx("x", "2024-01-01", "2024-01-01", "0.00")], "50.00")
    assert rows[0]["amount"] == Decimal("0.00")
    assert rows[0]["balance"] == Decimal("50.00")


def test_hidden_negative_opening_and_overdraft():
    txs = [_tx("a", "2024-01-01", "2024-01-01", "-20.00"), _tx("b", "2024-01-02", "2024-01-02", "5.00")]
    rows = running_balance(txs, "-10.00")
    assert [r["balance"] for r in rows] == [Decimal("-30.00"), Decimal("-25.00")]
    assert closing_balance(txs, "-10.00") == Decimal("-25.00")


def test_hidden_empty_closing_quantized():
    assert running_balance([], "42.5") == []
    result = closing_balance([], "42.5")
    assert result == Decimal("42.50")
    assert result.as_tuple().exponent == -2


def test_hidden_does_not_mutate_input():
    txs = [_tx("b", "2024-01-02", "2024-01-03", "10.00"), _tx("a", "2024-01-01", "2024-01-01", "-1.00")]
    snapshot = copy.deepcopy(txs)
    running_balance(txs, "100.00")
    closing_balance(txs, "100.00")
    assert txs == snapshot


def test_hidden_duplicate_id_raises():
    with pytest.raises(ValueError):
        running_balance([_tx("x", "2024-01-01", "2024-01-01", "1.00"), _tx("x", "2024-01-03", "2024-01-03", "2.00")], "0.00")


def test_hidden_missing_key_raises():
    with pytest.raises(ValueError):
        running_balance([{"id": "x", "value_date": "2024-01-01", "amount": "1.00"}], "0.00")


def test_hidden_invalid_calendar_date_raises():
    with pytest.raises(ValueError):
        running_balance([_tx("x", "2024-02-30", "2024-01-01", "1.00")], "0.00")


def test_hidden_bad_date_format_raises():
    with pytest.raises(ValueError):
        running_balance([_tx("x", "2024-1-1", "2024-01-01", "1.00")], "0.00")


def test_hidden_amount_three_decimals_raises():
    with pytest.raises(ValueError):
        running_balance([_tx("x", "2024-01-01", "2024-01-01", "1.005")], "0.00")


def test_hidden_amount_non_string_raises():
    with pytest.raises(ValueError):
        running_balance([_tx("x", "2024-01-01", "2024-01-01", 10.0)], "0.00")


def test_hidden_opening_three_decimals_raises():
    with pytest.raises(ValueError):
        closing_balance([], "10.005")


def test_hidden_empty_id_raises():
    with pytest.raises(ValueError):
        running_balance([_tx("", "2024-01-01", "2024-01-01", "1.00")], "0.00")


def test_hidden_closing_matches_last_balance():
    txs = [_tx("b", "2024-03-01", "2024-03-01", "7.25"), _tx("a", "2024-03-01", "2024-03-01", "-2.25")]
    # tie on both dates, id a first: 10-2.25=7.75, +7.25=15.00
    rows = running_balance(txs, "10.00")
    assert [r["balance"] for r in rows] == [Decimal("7.75"), Decimal("15.00")]
    assert closing_balance(txs, "10.00") == rows[-1]["balance"] == Decimal("15.00")


def test_hidden_leap_date_valid():
    rows = running_balance([_tx("x", "2024-02-29", "2024-02-29", "1.00")], "0.00")
    assert rows[0]["balance"] == Decimal("1.00")
    with pytest.raises(ValueError):
        running_balance([_tx("y", "2023-02-29", "2023-02-29", "1.00")], "0.00")
