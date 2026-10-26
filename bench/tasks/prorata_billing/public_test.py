from decimal import Decimal

from solution import prorate_period


def test_public_worked_example():
    result = prorate_period(
        "2024-03-01",
        "2024-04-01",
        [
            {"date": "2024-03-01", "monthly_price": "31.00"},
            {"date": "2024-03-16", "monthly_price": "62.00"},
        ],
    )
    assert result["period_days"] == 31
    assert result["segments"] == [
        {"from": "2024-03-01", "to": "2024-03-16", "days": 15, "monthly_price": Decimal("31.00"), "amount": Decimal("15.00")},
        {"from": "2024-03-16", "to": "2024-04-01", "days": 16, "monthly_price": Decimal("62.00"), "amount": Decimal("32.00")},
    ]
    assert result["total"] == Decimal("47.00")


def test_public_single_plan_full_month():
    result = prorate_period("2024-01-01", "2024-02-01", [{"date": "2024-01-01", "monthly_price": "100.00"}])
    assert result["total"] == Decimal("100.00")
    assert len(result["segments"]) == 1


def test_public_leap_february():
    result = prorate_period("2024-02-01", "2024-03-01", [{"date": "2024-02-01", "monthly_price": "29.00"}])
    assert result["period_days"] == 29
    assert result["segments"][0]["days"] == 29
    assert result["total"] == Decimal("29.00")


def test_public_unsorted_changes():
    result = prorate_period(
        "2024-03-01",
        "2024-04-01",
        [
            {"date": "2024-03-16", "monthly_price": "62.00"},
            {"date": "2024-03-01", "monthly_price": "31.00"},
        ],
    )
    assert result["total"] == Decimal("47.00")
