# --- public tests for budget_variance (module task_a.py) ---
from decimal import Decimal

import pytest

from task_a import variance_report, variance_summary


def test_public_revenue_favourable():
    row = variance_report([{"name": "Sales", "kind": "revenue", "budget": "100.00", "actual": "110.00"}])[0]
    assert row["variance"] == Decimal("10.00") and row["favourable"] is True and row["status"] == "favourable"
    assert row["variance_percent"] == Decimal("10.00")


def test_public_cost_underspend_favourable():
    row = variance_report([{"name": "Rent", "kind": "cost", "budget": "50.00", "actual": "40.00"}])[0]
    assert row["variance"] == Decimal("-10.00") and row["favourable"] is True


def test_public_on_budget():
    row = variance_report([{"name": "X", "kind": "cost", "budget": "50.00", "actual": "50.00"}])[0]
    assert row["favourable"] is False and row["status"] == "on_budget"


def test_public_empty_summary():
    summary = variance_summary([])
    assert summary["net_budget"] == Decimal("0.00") and summary["favourable_count"] == 0
    assert variance_report([]) == []


def test_public_bad_kind_raises():
    with pytest.raises(ValueError):
        variance_report([{"name": "X", "kind": "other", "budget": "1.00", "actual": "1.00"}])

# --- public tests for depreciation_declining (module task_b.py) ---
from decimal import Decimal

import pytest

from task_b import declining_schedule


def test_public_worked_example_a():
    rows = declining_schedule("10000", "1000", 4, "2")
    assert [r["amount"] for r in rows] == [Decimal("5000.00"), Decimal("2500.00"), Decimal("1250.00"), Decimal("250.00")]
    assert rows[-1]["book_value"] == Decimal("1000.00")


def test_public_worked_example_b_sl_switch():
    rows = declining_schedule("10000", "0", 5, "2")
    assert [r["amount"] for r in rows] == [Decimal("4000.00"), Decimal("2400.00"), Decimal("1440.00"), Decimal("1080.00"), Decimal("1080.00")]


def test_public_default_factor():
    assert declining_schedule("10000", "1000", 4) == declining_schedule("10000", "1000", 4, "2")


def test_public_years_are_one_based():
    rows = declining_schedule("5000", "0", 3, "2")
    assert [r["year"] for r in rows] == [1, 2, 3]


def test_public_invalid_factor():
    with pytest.raises(ValueError):
        declining_schedule("10000", "0", 5, "4")

# --- public tests for depreciation_straight_line (module task_c.py) ---
from decimal import Decimal

import pytest

from task_c import straight_line_schedule


def test_public_worked_example():
    rows = straight_line_schedule("12000", "0", 5, 2024, 7)
    assert [r["year"] for r in rows] == [2024, 2025, 2026, 2027, 2028, 2029]
    assert [r["amount"] for r in rows] == [Decimal("1100.00"), Decimal("2400.00"), Decimal("2400.00"), Decimal("2400.00"), Decimal("2400.00"), Decimal("1300.00")]
    assert rows[-1]["book_value"] == Decimal("0.00")
    assert sum(r["amount"] for r in rows) == Decimal("12000.00")


def test_public_salvage_book_value():
    rows = straight_line_schedule("6000", "600", 3, 2021, 12)
    assert rows[-1]["book_value"] == Decimal("600.00")
    assert sum(r["amount"] for r in rows) == Decimal("5400.00")


def test_public_first_year_january():
    rows = straight_line_schedule("12000", "0", 4, 2023, 1)
    assert rows[0]["amount"] == Decimal("2875.00")
    assert rows[0]["year"] == 2023


def test_public_invalid_life():
    with pytest.raises(ValueError):
        straight_line_schedule("1000", "0", 0, 2024, 1)


def test_public_invalid_month():
    with pytest.raises(ValueError):
        straight_line_schedule("1000", "0", 5, 2024, 13)
