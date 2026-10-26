from decimal import Decimal

import pytest

from solution import variance_report, variance_summary


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
