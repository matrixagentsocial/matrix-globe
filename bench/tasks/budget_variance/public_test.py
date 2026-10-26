from decimal import Decimal

import pytest

from solution import variance_report, variance_summary


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
