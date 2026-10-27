# --- public tests for day_count (module task_a.py) ---
from decimal import Decimal

import pytest

from task_a import accrued_interest, day_count_fraction


def test_public_us_example():
    assert day_count_fraction("2024-01-31", "2024-07-31", "30/360_US") == Decimal("0.5000000000")


def test_public_act_act_whole_year():
    assert day_count_fraction("2023-01-01", "2024-01-01", "ACT/ACT_ISDA") == Decimal("1.0000000000")


def test_public_act_act_split_years():
    assert day_count_fraction("2023-12-01", "2024-02-01", "ACT/ACT_ISDA") == Decimal("0.1696309604")


def test_public_act_365f():
    assert day_count_fraction("2024-01-01", "2024-04-01", "ACT/365F") == Decimal("0.2493150685")


def test_public_accrued_example():
    assert accrued_interest("10000.00", "5", "2024-01-31", "2024-07-31", "30/360_US") == Decimal("250.00")

# --- public tests for fifo_cost (module task_b.py) ---
from decimal import Decimal

import pytest

from task_b import fifo_report


def _buy(date, qty, price, fee="0.00"):
    return {"date": date, "side": "BUY", "quantity": qty, "price": price, "fee": fee}


def _sell(date, qty, price, fee="0.00"):
    return {"date": date, "side": "SELL", "quantity": qty, "price": price, "fee": fee}


def test_public_worked_example():
    result = fifo_report(
        [
            _buy("2024-01-01", 10, "10"),
            _buy("2024-01-02", 10, "20"),
            _sell("2024-01-03", 15, "30"),
        ]
    )
    assert result["sales"] == [
        {
            "date": "2024-01-03",
            "quantity": 15,
            "proceeds": Decimal("450.00"),
            "cost": Decimal("200.00"),
            "realized": Decimal("250.00"),
        }
    ]
    assert result["total_realized"] == Decimal("250.00")
    assert result["remaining"] == [
        {"quantity": 5, "unit_cost": Decimal("20.0000"), "total_cost": Decimal("100.00")}
    ]
    assert result["inventory_quantity"] == 5


def test_public_empty():
    assert fifo_report([]) == {
        "sales": [],
        "total_realized": Decimal("0.00"),
        "remaining": [],
        "inventory_quantity": 0,
    }


def test_public_sell_all():
    result = fifo_report(
        [_buy("2024-01-01", 5, "10.00"), _sell("2024-01-02", 5, "12.00")]
    )
    assert result["sales"][0]["realized"] == Decimal("10.00")
    assert result["remaining"] == []
    assert result["inventory_quantity"] == 0


def test_public_oversell_raises():
    with pytest.raises(ValueError):
        fifo_report([_buy("2024-01-01", 5, "10.00"), _sell("2024-01-02", 6, "12.00")])

# --- public tests for iban_validation (module task_c.py) ---
from task_c import normalize_iban, validate_iban


def test_valid_gb_iban_with_spaces():
    assert validate_iban("GB29 NWBK 6016 1331 9268 19") is True


def test_valid_de_iban():
    assert validate_iban("DE89 3704 0044 0532 0130 00") is True


def test_invalid_checksum():
    assert validate_iban("GB29 NWBK 6016 1331 9268 18") is False


def test_normalize_uppercases_and_strips_spaces():
    assert normalize_iban("gb29 nwbk") == "GB29NWBK"


def test_invalid_wrong_length():
    assert validate_iban("DE89 3704 0044 0532 0130") is False
