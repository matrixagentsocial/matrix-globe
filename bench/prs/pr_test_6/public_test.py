# --- public tests for running_balance (module task_a.py) ---
from decimal import Decimal

import pytest

from task_a import closing_balance, running_balance


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

# --- public tests for spanish_bank_csv (module task_b.py) ---
from decimal import Decimal

import pytest

from task_b import parse_bank_csv, summarize_transactions

HEADER = "Fecha;Concepto;Importe;Saldo"


def test_public_basic_row():
    rows = parse_bank_csv(HEADER + "\n05/01/2024;Nomina;1.500,00;2.000,00\n")
    assert rows == [{"date": "2024-01-05", "concept": "Nomina", "amount": Decimal("1500.00"), "balance": Decimal("2000.00")}]


def test_public_summary():
    rows = parse_bank_csv(HEADER + "\n05/01/2024;A;100,00;\n06/01/2024;B;-30,00;\n")
    assert summarize_transactions(rows) == {
        "count": 2, "credits": Decimal("100.00"), "debits": Decimal("-30.00"),
        "net": Decimal("70.00"), "first_date": "2024-01-05", "last_date": "2024-01-06",
    }


def test_public_header_only_empty():
    assert parse_bank_csv(HEADER + "\n") == []


def test_public_bad_header_raises():
    with pytest.raises(ValueError):
        parse_bank_csv("fecha;Concepto;Importe;Saldo\n05/01/2024;A;1,00;\n")

# --- public tests for spanish_tax_id (module task_c.py) ---
from task_c import classify_spanish_id, is_valid_spanish_id


def test_public_nif_valid():
    assert classify_spanish_id("12345678Z") == "NIF"
    assert is_valid_spanish_id("12345678Z") is True


def test_public_nie_valid():
    assert classify_spanish_id("X1234567L") == "NIE"


def test_public_cif_valid():
    assert classify_spanish_id("A58818501") == "CIF"


def test_public_wrong_control_letter_invalid():
    assert classify_spanish_id("12345678A") is None
    assert is_valid_spanish_id("12345678A") is False


def test_public_lowercase_and_spaces_normalized():
    assert classify_spanish_id("1234 5678 z") == "NIF"
