from decimal import Decimal

import pytest

from solution import process_inventory


def test_public_worked_example():
    result = process_inventory([
        {"type": "PURCHASE", "quantity": 10, "unit_cost": "10.00"},
        {"type": "PURCHASE", "quantity": 10, "unit_cost": "20.00"},
        {"type": "SALE", "quantity": 5},
        {"type": "CUSTOMER_RETURN", "quantity": 2},
        {"type": "PURCHASE_RETURN", "quantity": 3},
    ])
    assert result == {
        "quantity_on_hand": 14,
        "inventory_value": Decimal("210.00"),
        "average_cost": Decimal("15.0000"),
        "total_cogs": Decimal("75.00"),
        "total_purchase_returns": Decimal("45.00"),
    }


def test_public_empty():
    assert process_inventory([]) == {
        "quantity_on_hand": 0,
        "inventory_value": Decimal("0.00"),
        "average_cost": Decimal("0.0000"),
        "total_cogs": Decimal("0.00"),
        "total_purchase_returns": Decimal("0.00"),
    }


def test_public_single_purchase_average():
    result = process_inventory([{"type": "PURCHASE", "quantity": 4, "unit_cost": "2.50"}])
    assert result["inventory_value"] == Decimal("10.00")
    assert result["average_cost"] == Decimal("2.5000")


def test_public_oversell_raises():
    with pytest.raises(ValueError):
        process_inventory([{"type": "SALE", "quantity": 1}])
