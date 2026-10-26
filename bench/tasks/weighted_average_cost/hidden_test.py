from decimal import Decimal

import pytest

from solution import process_inventory


def buy(q, c):
    return {"type": "PURCHASE", "quantity": q, "unit_cost": c}


def test_hidden_average_after_two_purchases():
    r = process_inventory([buy(10, "10.00"), buy(10, "20.00")])
    assert r["inventory_value"] == Decimal("300.00")
    assert r["average_cost"] == Decimal("15.0000")


def test_hidden_sale_uses_average_not_fifo():
    r = process_inventory([buy(10, "10.00"), buy(10, "20.00"), {"type": "SALE", "quantity": 10}])
    assert r["total_cogs"] == Decimal("150.00")
    assert r["inventory_value"] == Decimal("150.00")
    assert r["quantity_on_hand"] == 10


def test_hidden_customer_return_at_current_average():
    r = process_inventory([buy(10, "10.00"), {"type": "SALE", "quantity": 5}, {"type": "CUSTOMER_RETURN", "quantity": 5}])
    # value 100-50=50 qty5, return 5*10=50 -> 100 qty10; cogs unchanged
    assert r["inventory_value"] == Decimal("100.00")
    assert r["total_cogs"] == Decimal("50.00")
    assert r["quantity_on_hand"] == 10


def test_hidden_customer_return_empty_raises():
    with pytest.raises(ValueError):
        process_inventory([{"type": "CUSTOMER_RETURN", "quantity": 1}])


def test_hidden_customer_return_after_selling_all_raises():
    with pytest.raises(ValueError):
        process_inventory([buy(2, "5.00"), {"type": "SALE", "quantity": 2}, {"type": "CUSTOMER_RETURN", "quantity": 1}])


def test_hidden_purchase_return_not_cogs():
    r = process_inventory([buy(10, "10.00"), {"type": "PURCHASE_RETURN", "quantity": 4}])
    assert r["total_cogs"] == Decimal("0.00")
    assert r["total_purchase_returns"] == Decimal("40.00")
    assert r["inventory_value"] == Decimal("60.00")


def test_hidden_purchase_return_exceeds_raises():
    with pytest.raises(ValueError):
        process_inventory([buy(2, "5.00"), {"type": "PURCHASE_RETURN", "quantity": 3}])


def test_hidden_fractional_average_rounding():
    # buy 3 @ 10.00 -> value 30, sell 1: avg 10 exact here; use 3@ "3.33": value 9.99 avg 3.33
    r = process_inventory([buy(3, "3.33"), {"type": "SALE", "quantity": 1}])
    assert r["total_cogs"] == Decimal("3.33")
    assert r["inventory_value"] == Decimal("6.66")
    assert r["average_cost"] == Decimal("3.3300")


def test_hidden_average_cost_four_dp():
    # buy 3 units total 10.00: avg 3.3333...
    r = process_inventory([buy(1, "4.00"), buy(2, "3.00")])
    assert r["inventory_value"] == Decimal("10.00")
    assert r["average_cost"] == Decimal("3.3333")


def test_hidden_purchase_value_quantized_cents():
    # 3 * 3.333 = 9.999 -> 10.00
    r = process_inventory([buy(3, "3.333")])
    assert r["inventory_value"] == Decimal("10.00")
    assert r["average_cost"] == Decimal("3.3333")


def test_hidden_sell_all_leaves_zero():
    r = process_inventory([buy(3, "3.33"), {"type": "SALE", "quantity": 3}])
    assert r["inventory_value"] == Decimal("0.00")
    assert r["quantity_on_hand"] == 0
    assert r["average_cost"] == Decimal("0.0000")
    assert r["total_cogs"] == Decimal("9.99")


def test_hidden_new_average_after_repurchase():
    r = process_inventory([buy(2, "10.00"), {"type": "SALE", "quantity": 2}, buy(2, "20.00")])
    assert r["average_cost"] == Decimal("20.0000")
    assert r["inventory_value"] == Decimal("40.00")


def test_hidden_unit_cost_ignored_on_sale():
    r = process_inventory([buy(5, "10.00"), {"type": "SALE", "quantity": 1, "unit_cost": "bogus"}])
    assert r["total_cogs"] == Decimal("10.00")


def test_hidden_missing_unit_cost_purchase_raises():
    with pytest.raises(ValueError):
        process_inventory([{"type": "PURCHASE", "quantity": 1}])


def test_hidden_negative_unit_cost_raises():
    with pytest.raises(ValueError):
        process_inventory([buy(1, "-1.00")])


def test_hidden_zero_unit_cost_allowed():
    r = process_inventory([buy(2, "0")])
    assert r["inventory_value"] == Decimal("0.00")
    assert r["average_cost"] == Decimal("0.0000")
    assert r["quantity_on_hand"] == 2


def test_hidden_bool_quantity_raises():
    with pytest.raises(ValueError):
        process_inventory([{"type": "PURCHASE", "quantity": True, "unit_cost": "1.00"}])


def test_hidden_zero_quantity_raises():
    with pytest.raises(ValueError):
        process_inventory([buy(0, "1.00")])


def test_hidden_bad_type_raises():
    with pytest.raises(ValueError):
        process_inventory([{"type": "purchase", "quantity": 1, "unit_cost": "1.00"}])


def test_hidden_exponents():
    r = process_inventory([buy(1, "1.00")])
    assert r["inventory_value"].as_tuple().exponent == -2
    assert r["average_cost"].as_tuple().exponent == -4
    assert r["total_cogs"].as_tuple().exponent == -2
