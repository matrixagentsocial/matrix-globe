from decimal import Decimal

import pytest

from solution import fifo_report


def _buy(date, qty, price, fee="0.00"):
    return {"date": date, "side": "BUY", "quantity": qty, "price": price, "fee": fee}


def _sell(date, qty, price, fee="0.00"):
    return {"date": date, "side": "SELL", "quantity": qty, "price": price, "fee": fee}


def test_hidden_buy_only_fee_in_lot_cost():
    result = fifo_report([_buy("2024-01-01", 10, "10.00", "5.00")])
    assert result["sales"] == []
    assert result["total_realized"] == Decimal("0.00")
    assert result["remaining"] == [
        {"quantity": 10, "unit_cost": Decimal("10.5000"), "total_cost": Decimal("105.00")}
    ]
    assert result["inventory_quantity"] == 10


def test_hidden_buy_and_sell_fees():
    result = fifo_report(
        [
            _buy("2024-01-01", 10, "10.00", "10.00"),
            _sell("2024-01-02", 5, "20.00", "5.00"),
        ]
    )
    # Lot total 110; half consumed = 55; proceeds 100-5=95; realized 40.
    assert result["sales"][0]["proceeds"] == Decimal("95.00")
    assert result["sales"][0]["cost"] == Decimal("55.00")
    assert result["sales"][0]["realized"] == Decimal("40.00")
    assert result["remaining"] == [
        {"quantity": 5, "unit_cost": Decimal("11.0000"), "total_cost": Decimal("55.00")}
    ]


def test_hidden_fee_default_omitted():
    trades = [
        {"date": "2024-01-01", "side": "BUY", "quantity": 10, "price": "10.00"},
        {"date": "2024-01-02", "side": "SELL", "quantity": 5, "price": "12.00"},
    ]
    result = fifo_report(trades)
    assert result["sales"][0]["proceeds"] == Decimal("60.00")
    assert result["sales"][0]["cost"] == Decimal("50.00")
    assert result["sales"][0]["realized"] == Decimal("10.00")


def test_hidden_proportional_partial_cost_four_dp_price():
    result = fifo_report(
        [_buy("2024-01-01", 3, "3.3333"), _sell("2024-01-02", 1, "10.00")]
    )
    # Lot total 9.9999; 1/3 consumed 3.3333 -> cost 3.33, realized 6.67.
    assert result["sales"][0]["cost"] == Decimal("3.33")
    assert result["sales"][0]["realized"] == Decimal("6.67")
    assert result["remaining"] == [
        {"quantity": 2, "unit_cost": Decimal("3.3333"), "total_cost": Decimal("6.67")}
    ]


def test_hidden_two_sales_total_is_sum_of_realized():
    result = fifo_report(
        [
            _buy("2024-01-01", 10, "10.00"),
            _sell("2024-01-02", 4, "15.00"),
            _sell("2024-01-03", 6, "15.00"),
        ]
    )
    assert [s["realized"] for s in result["sales"]] == [
        Decimal("20.00"),
        Decimal("30.00"),
    ]
    assert result["total_realized"] == Decimal("50.00")
    assert result["remaining"] == []


def test_hidden_interleaved_fifo_across_buys():
    result = fifo_report(
        [
            _buy("2024-01-01", 10, "10.00"),
            _sell("2024-01-02", 5, "30.00"),
            _buy("2024-01-03", 10, "20.00"),
            _sell("2024-01-04", 10, "30.00"),
        ]
    )
    assert result["sales"][0]["realized"] == Decimal("100.00")
    # Second sale: 5 @10 (50) + 5 @20 (100) = 150 cost, 300 proceeds.
    assert result["sales"][1]["cost"] == Decimal("150.00")
    assert result["sales"][1]["realized"] == Decimal("150.00")
    assert result["total_realized"] == Decimal("250.00")
    assert result["remaining"] == [
        {"quantity": 5, "unit_cost": Decimal("20.0000"), "total_cost": Decimal("100.00")}
    ]


def test_hidden_process_in_given_order_not_sorted():
    result = fifo_report(
        [_buy("2024-02-01", 10, "10.00"), _sell("2024-01-01", 5, "20.00")]
    )
    assert result["sales"][0]["date"] == "2024-01-01"
    assert result["sales"][0]["realized"] == Decimal("50.00")
    assert result["inventory_quantity"] == 5


def test_hidden_remaining_multiple_lots_oldest_first():
    result = fifo_report(
        [
            _buy("2024-01-01", 5, "10.00"),
            _buy("2024-01-02", 5, "20.00"),
            _sell("2024-01-03", 3, "15.00"),
        ]
    )
    assert result["sales"][0]["proceeds"] == Decimal("45.00")
    assert result["sales"][0]["cost"] == Decimal("30.00")
    assert result["sales"][0]["realized"] == Decimal("15.00")
    assert result["remaining"] == [
        {"quantity": 2, "unit_cost": Decimal("10.0000"), "total_cost": Decimal("20.00")},
        {"quantity": 5, "unit_cost": Decimal("20.0000"), "total_cost": Decimal("100.00")},
    ]
    assert result["inventory_quantity"] == 7


def test_hidden_four_dp_price_quantization():
    result = fifo_report(
        [_buy("2024-01-01", 10, "10.1234"), _sell("2024-01-02", 3, "20.5555")]
    )
    # Proceeds 61.6665 -> 61.67; cost 101.234*3/10=30.3702 -> 30.37;
    # realized 31.2963 -> 31.30.
    assert result["sales"][0]["proceeds"] == Decimal("61.67")
    assert result["sales"][0]["cost"] == Decimal("30.37")
    assert result["sales"][0]["realized"] == Decimal("31.30")


def test_hidden_exponents_two_and_four_dp():
    result = fifo_report(
        [_buy("2024-01-01", 10, "10.00"), _sell("2024-01-02", 4, "15.00")]
    )
    sale = result["sales"][0]
    for key in ("proceeds", "cost", "realized"):
        assert sale[key].as_tuple().exponent == -2
    assert result["total_realized"].as_tuple().exponent == -2
    assert result["remaining"][0]["unit_cost"].as_tuple().exponent == -4
    assert result["remaining"][0]["total_cost"].as_tuple().exponent == -2


def test_hidden_oversell_despite_later_buy_raises():
    with pytest.raises(ValueError):
        fifo_report(
            [
                _buy("2024-01-01", 5, "10.00"),
                _sell("2024-01-02", 6, "12.00"),
                _buy("2024-01-03", 10, "10.00"),
            ]
        )


def test_hidden_sell_with_no_inventory_raises():
    with pytest.raises(ValueError):
        fifo_report([_sell("2024-01-01", 1, "10.00")])


def test_hidden_invalid_dates_raise():
    with pytest.raises(ValueError):
        fifo_report([_buy("2024-02-30", 1, "10.00")])
    with pytest.raises(ValueError):
        fifo_report([_buy("2024-1-01", 1, "10.00")])
    with pytest.raises(ValueError):
        fifo_report([_buy("01/01/2024", 1, "10.00")])


def test_hidden_bad_side_raises():
    with pytest.raises(ValueError):
        fifo_report(
            [{"date": "2024-01-01", "side": "buy", "quantity": 1, "price": "10.00"}]
        )
    with pytest.raises(ValueError):
        fifo_report(
            [{"date": "2024-01-01", "side": "HOLD", "quantity": 1, "price": "10.00"}]
        )


def test_hidden_bool_and_zero_quantity_raise():
    with pytest.raises(ValueError):
        fifo_report([_buy("2024-01-01", True, "10.00")])
    with pytest.raises(ValueError):
        fifo_report([_buy("2024-01-01", 0, "10.00")])


def test_hidden_price_zero_and_too_many_places_raise():
    with pytest.raises(ValueError):
        fifo_report([_buy("2024-01-01", 1, "0")])
    with pytest.raises(ValueError):
        fifo_report([_buy("2024-01-01", 1, "10.12345")])


def test_hidden_negative_fee_and_missing_key_raise():
    with pytest.raises(ValueError):
        fifo_report([_buy("2024-01-01", 1, "10.00", "-1.00")])
    with pytest.raises(ValueError):
        fifo_report([{"date": "2024-01-01", "side": "BUY", "quantity": 1}])
    with pytest.raises(ValueError):
        fifo_report(["not-a-dict"])
