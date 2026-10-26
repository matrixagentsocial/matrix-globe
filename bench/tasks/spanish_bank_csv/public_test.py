from decimal import Decimal

import pytest

from solution import parse_bank_csv, summarize_transactions

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
