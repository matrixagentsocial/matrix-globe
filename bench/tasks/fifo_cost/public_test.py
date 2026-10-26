from decimal import Decimal

import pytest

from solution import fifo_report


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
