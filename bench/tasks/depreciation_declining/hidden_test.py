from decimal import Decimal

import pytest

from solution import declining_schedule


def test_hidden_example_a_full_rows():
    rows = declining_schedule("10000", "1000", 4, "2")
    assert rows == [
        {"year": 1, "amount": Decimal("5000.00"), "accumulated": Decimal("5000.00"), "book_value": Decimal("5000.00")},
        {"year": 2, "amount": Decimal("2500.00"), "accumulated": Decimal("7500.00"), "book_value": Decimal("2500.00")},
        {"year": 3, "amount": Decimal("1250.00"), "accumulated": Decimal("8750.00"), "book_value": Decimal("1250.00")},
        {"year": 4, "amount": Decimal("250.00"), "accumulated": Decimal("9000.00"), "book_value": Decimal("1000.00")},
    ]


def test_hidden_example_b_sl_wins_year4():
    rows = declining_schedule("10000", "0", 5, "2")
    assert [r["amount"] for r in rows] == [Decimal("4000.00"), Decimal("2400.00"), Decimal("1440.00"), Decimal("1080.00"), Decimal("1080.00")]
    assert sum(r["amount"] for r in rows) == Decimal("10000.00")


def test_hidden_factor_one_sl_wins():
    rows = declining_schedule("5000", "500", 5, "1")
    # Y1 DB 1000 vs SL 900 ->1000; then SL 875 each remaining year wins/ties
    assert [r["amount"] for r in rows] == [Decimal("1000.00"), Decimal("875.00"), Decimal("875.00"), Decimal("875.00"), Decimal("875.00")]
    assert rows[-1]["book_value"] == Decimal("500.00")


def test_hidden_factor_one_point_five_switch():
    rows = declining_schedule("8000", "0", 4, "1.5")
    # Y1 3000, Y2 1875, Y3 SL 1562.50 beats DB 1171.88, Y4 final 1562.50
    assert [r["amount"] for r in rows] == [Decimal("3000.00"), Decimal("1875.00"), Decimal("1562.50"), Decimal("1562.50")]


def test_hidden_rounding_half_up():
    rows = declining_schedule("10000", "0", 3, "2")
    assert [r["amount"] for r in rows] == [Decimal("6666.67"), Decimal("2222.22"), Decimal("1111.11")]
    assert sum(r["amount"] for r in rows) == Decimal("10000.00")


def test_hidden_life_one_final_only():
    rows = declining_schedule("5000", "1000", 1, "2")
    assert rows == [{"year": 1, "amount": Decimal("4000.00"), "accumulated": Decimal("4000.00"), "book_value": Decimal("1000.00")}]


def test_hidden_factor_three_never_below_salvage():
    rows = declining_schedule("9000", "1000", 3, "3")
    # rate 1: Y1 DB 9000 capped to 8000? opening-salvage=8000, DB 9000 > cap -> 8000, then remaining years 0
    assert rows[0]["amount"] == Decimal("8000.00")
    assert rows[-1]["book_value"] == Decimal("1000.00")
    assert sum(r["amount"] for r in rows) == Decimal("8000.00")
    assert all(r["book_value"] >= Decimal("1000.00") for r in rows)


def test_hidden_total_and_exponent():
    rows = declining_schedule("12345.67", "2345.67", 6, "2")
    assert sum(r["amount"] for r in rows) == Decimal("10000.00")
    assert rows[-1]["book_value"] == Decimal("2345.67")
    for r in rows:
        assert r["amount"].as_tuple().exponent == -2
        assert r["book_value"].as_tuple().exponent == -2


def test_hidden_accumulated_consistency():
    rows = declining_schedule("10000", "1000", 4, "2")
    acc = Decimal("0.00")
    for r in rows:
        acc += r["amount"]
        assert r["accumulated"] == acc
        assert r["book_value"] == Decimal("10000.00") - acc


def test_hidden_salvage_equal_cost_raises():
    with pytest.raises(ValueError):
        declining_schedule("1000", "1000", 4, "2")


def test_hidden_negative_salvage_raises():
    with pytest.raises(ValueError):
        declining_schedule("1000", "-1", 4, "2")


def test_hidden_factor_below_one_raises():
    with pytest.raises(ValueError):
        declining_schedule("1000", "0", 4, "0.5")


def test_hidden_factor_above_three_raises():
    with pytest.raises(ValueError):
        declining_schedule("1000", "0", 4, "3.01")


def test_hidden_factor_non_numeric_raises():
    with pytest.raises(ValueError):
        declining_schedule("1000", "0", 4, "abc")


def test_hidden_factor_boundary_three_ok():
    rows = declining_schedule("1000", "0", 2, "3")
    assert sum(r["amount"] for r in rows) == Decimal("1000.00")


def test_hidden_factor_boundary_one_ok():
    rows = declining_schedule("1000", "0", 2, "1")
    # Y1 DB 500 vs SL 500 -> 500, Y2 final 500
    assert [r["amount"] for r in rows] == [Decimal("500.00"), Decimal("500.00")]


def test_hidden_life_zero_raises():
    with pytest.raises(ValueError):
        declining_schedule("1000", "0", 0, "2")


def test_hidden_life_bool_raises():
    with pytest.raises(ValueError):
        declining_schedule("1000", "0", True, "2")


def test_hidden_cost_three_decimals_raises():
    with pytest.raises(ValueError):
        declining_schedule("1000.005", "0", 4, "2")
