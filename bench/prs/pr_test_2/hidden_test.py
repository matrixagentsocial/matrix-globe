# --- hidden tests for budget_variance (module task_a.py) ---
from decimal import Decimal

import pytest

from task_a import variance_report, variance_summary


def _line(name="X", kind="revenue", budget="100.00", actual="100.00"):
    return {"name": name, "kind": kind, "budget": budget, "actual": actual}


def test_hidden_revenue_unfavourable():
    row = variance_report([_line(actual="90.00")])[0]
    assert row["variance"] == Decimal("-10.00") and row["favourable"] is False and row["status"] == "unfavourable"
    assert row["variance_percent"] == Decimal("-10.00")


def test_hidden_cost_overspend_unfavourable_signed_percent():
    row = variance_report([_line(kind="cost", actual="110.00")])[0]
    assert row["variance"] == Decimal("10.00") and row["favourable"] is False and row["status"] == "unfavourable"
    assert row["variance_percent"] == Decimal("10.00")


def test_hidden_cost_underspend_percent_negative():
    row = variance_report([_line(kind="cost", budget="50.00", actual="40.00")])[0]
    assert row["variance_percent"] == Decimal("-20.00") and row["favourable"] is True


def test_hidden_zero_budget_percent_none():
    row = variance_report([_line(budget="0.00", actual="5.00")])[0]
    assert row["variance_percent"] is None and row["variance"] == Decimal("5.00")


def test_hidden_zero_budget_zero_actual_on_budget():
    row = variance_report([_line(budget="0.00", actual="0.00")])[0]
    assert row["variance_percent"] is None and row["status"] == "on_budget" and row["favourable"] is False


def test_hidden_input_order_preserved():
    rows = variance_report([_line(name="B", budget="1.00", actual="1.00"), _line(name="A", budget="2.00", actual="3.00")])
    assert [r["name"] for r in rows] == ["B", "A"]


def test_hidden_summary_totals_and_net():
    lines = [_line("Sales", "revenue", "100.00", "110.00"), _line("Rent", "cost", "50.00", "40.00")]
    s = variance_summary(lines)
    assert s["total_budget_revenue"] == Decimal("100.00") and s["total_actual_revenue"] == Decimal("110.00")
    assert s["total_budget_cost"] == Decimal("50.00") and s["total_actual_cost"] == Decimal("40.00")
    assert s["net_budget"] == Decimal("50.00") and s["net_actual"] == Decimal("70.00") and s["net_variance"] == Decimal("20.00")
    assert s["favourable_count"] == 2 and s["unfavourable_count"] == 0 and s["on_budget_count"] == 0


def test_hidden_summary_counts_mixed():
    lines = [_line("A", "revenue", "100.00", "110.00"), _line("B", "revenue", "100.00", "90.00"), _line("C", "cost", "10.00", "10.00")]
    s = variance_summary(lines)
    assert (s["favourable_count"], s["unfavourable_count"], s["on_budget_count"]) == (1, 1, 1)


def test_hidden_percent_rounding_half_up():
    # variance 1.00 on budget 800.00 -> 0.125% -> 0.13 with HALF_UP.
    row = variance_report([_line(budget="800.00", actual="801.00")])[0]
    assert row["variance_percent"] == Decimal("0.13")


def test_hidden_negative_revenue_amounts():
    row = variance_report([_line(budget="-100.00", actual="-90.00")])[0]
    assert row["variance"] == Decimal("10.00") and row["favourable"] is True
    assert row["variance_percent"] == Decimal("-10.00")


def test_hidden_output_two_dp_exponent():
    row = variance_report([_line(budget="100", actual="110")])[0]
    assert row["budget"] == Decimal("100.00") and row["budget"].as_tuple().exponent == -2
    assert row["variance"].as_tuple().exponent == -2


def test_hidden_missing_key_raises():
    with pytest.raises(ValueError):
        variance_report([{"name": "X", "kind": "revenue", "budget": "1.00"}])


def test_hidden_bad_money_raises():
    with pytest.raises(ValueError):
        variance_report([_line(budget="abc")])


def test_hidden_three_dp_raises():
    with pytest.raises(ValueError):
        variance_summary([_line(actual="1.005")])


def test_hidden_summary_bad_kind_raises():
    with pytest.raises(ValueError):
        variance_summary([_line(kind="income")])

# --- hidden tests for depreciation_declining (module task_b.py) ---
from decimal import Decimal

import pytest

from task_b import declining_schedule


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

# --- hidden tests for depreciation_straight_line (module task_c.py) ---
from decimal import Decimal

import pytest

from task_c import straight_line_schedule


def test_hidden_worked_example_full_rows():
    rows = straight_line_schedule("12000", "0", 5, 2024, 7)
    assert rows == [
        {"year": 2024, "amount": Decimal("1100.00"), "accumulated": Decimal("1100.00"), "book_value": Decimal("10900.00")},
        {"year": 2025, "amount": Decimal("2400.00"), "accumulated": Decimal("3500.00"), "book_value": Decimal("8500.00")},
        {"year": 2026, "amount": Decimal("2400.00"), "accumulated": Decimal("5900.00"), "book_value": Decimal("6100.00")},
        {"year": 2027, "amount": Decimal("2400.00"), "accumulated": Decimal("8300.00"), "book_value": Decimal("3700.00")},
        {"year": 2028, "amount": Decimal("2400.00"), "accumulated": Decimal("10700.00"), "book_value": Decimal("1300.00")},
        {"year": 2029, "amount": Decimal("1300.00"), "accumulated": Decimal("12000.00"), "book_value": Decimal("0.00")},
    ]


def test_hidden_january_fraction():
    rows = straight_line_schedule("12000", "0", 4, 2023, 1)
    assert [r["amount"] for r in rows] == [Decimal("2875.00"), Decimal("3000.00"), Decimal("3000.00"), Decimal("3000.00"), Decimal("125.00")]
    assert [r["year"] for r in rows] == [2023, 2024, 2025, 2026, 2027]
    assert rows[-1]["book_value"] == Decimal("0.00")


def test_hidden_december_fraction():
    rows = straight_line_schedule("6000", "600", 3, 2021, 12)
    assert [r["amount"] for r in rows] == [Decimal("75.00"), Decimal("1800.00"), Decimal("1800.00"), Decimal("1725.00")]
    assert rows[-1] == {"year": 2024, "amount": Decimal("1725.00"), "accumulated": Decimal("5400.00"), "book_value": Decimal("600.00")}


def test_hidden_salvage_base_and_final_book():
    rows = straight_line_schedule("10000", "1000", 4, 2020, 1)
    # base 9000, full 2250, first 2250*11.5/12 = 2156.25
    assert [r["amount"] for r in rows] == [Decimal("2156.25"), Decimal("2250.00"), Decimal("2250.00"), Decimal("2250.00"), Decimal("93.75")]
    assert sum(r["amount"] for r in rows) == Decimal("9000.00")
    assert rows[-1]["book_value"] == Decimal("1000.00")


def test_hidden_rounding_final_absorbs():
    rows = straight_line_schedule("10000", "0", 3, 2022, 6)
    # full 3333.333..., first fraction 6.5/12 -> 1805.56, then 3333.33 x2, final remainder
    assert [r["amount"] for r in rows] == [Decimal("1805.56"), Decimal("3333.33"), Decimal("3333.33"), Decimal("1527.78")]
    assert sum(r["amount"] for r in rows) == Decimal("10000.00")
    assert rows[-1]["book_value"] == Decimal("0.00")


def test_hidden_life_one():
    rows = straight_line_schedule("1200", "200", 1, 2024, 7)
    # base 1000, first 1000*5.5/12=458.33, final 541.67
    assert [r["amount"] for r in rows] == [Decimal("458.33"), Decimal("541.67")]
    assert rows[-1]["book_value"] == Decimal("200.00")
    assert [r["year"] for r in rows] == [2024, 2025]


def test_hidden_accumulated_and_book_consistency():
    rows = straight_line_schedule("5000", "500", 2, 2020, 4)
    acc = Decimal("0.00")
    for r in rows:
        acc += r["amount"]
        assert r["accumulated"] == acc
        assert r["book_value"] == Decimal("5000.00") - acc
        assert r["amount"].as_tuple().exponent == -2
    assert rows[-1]["book_value"] == Decimal("500.00")


def test_hidden_row_count_life_plus_one():
    rows = straight_line_schedule("12000", "0", 5, 2024, 7)
    assert len(rows) == 6


def test_hidden_salvage_equal_cost_raises__depreciation_straight_line():
    with pytest.raises(ValueError):
        straight_line_schedule("1000", "1000", 5, 2024, 1)


def test_hidden_salvage_greater_than_cost_raises():
    with pytest.raises(ValueError):
        straight_line_schedule("1000", "1000.01", 5, 2024, 1)


def test_hidden_negative_salvage_raises__depreciation_straight_line():
    with pytest.raises(ValueError):
        straight_line_schedule("1000", "-1", 5, 2024, 1)


def test_hidden_zero_cost_raises():
    with pytest.raises(ValueError):
        straight_line_schedule("0", "0", 5, 2024, 1)


def test_hidden_cost_three_decimals_raises__depreciation_straight_line():
    with pytest.raises(ValueError):
        straight_line_schedule("1000.005", "0", 5, 2024, 1)


def test_hidden_non_numeric_cost_raises():
    with pytest.raises(ValueError):
        straight_line_schedule("abc", "0", 5, 2024, 1)


def test_hidden_life_too_large_raises():
    with pytest.raises(ValueError):
        straight_line_schedule("1000", "0", 51, 2024, 1)


def test_hidden_life_bool_raises__depreciation_straight_line():
    with pytest.raises(ValueError):
        straight_line_schedule("1000", "0", True, 2024, 1)


def test_hidden_month_zero_raises():
    with pytest.raises(ValueError):
        straight_line_schedule("1000", "0", 5, 2024, 0)


def test_hidden_year_out_of_range_raises():
    with pytest.raises(ValueError):
        straight_line_schedule("1000", "0", 5, 1899, 1)


def test_hidden_amount_never_exceeds_remaining():
    rows = straight_line_schedule("100.00", "0.00", 7, 2024, 11)
    assert sum(r["amount"] for r in rows) == Decimal("100.00")
    assert all(r["amount"] > Decimal("0.00") for r in rows)
    assert rows[-1]["book_value"] == Decimal("0.00")
