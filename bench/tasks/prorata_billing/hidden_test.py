from decimal import Decimal

import pytest

from solution import prorate_period


def test_hidden_leap_feb_with_change():
    result = prorate_period(
        "2024-02-01", "2024-03-01",
        [{"date": "2024-02-01", "monthly_price": "29.00"}, {"date": "2024-02-15", "monthly_price": "58.00"}],
    )
    assert result["period_days"] == 29
    assert [(s["from"], s["to"], s["days"], str(s["amount"])) for s in result["segments"]] == [
        ("2024-02-01", "2024-02-15", 14, "14.00"),
        ("2024-02-15", "2024-03-01", 15, "30.00"),
    ]
    assert result["total"] == Decimal("44.00")


def test_hidden_same_price_mid_cycle_merges():
    result = prorate_period(
        "2024-03-01", "2024-04-01",
        [{"date": "2024-03-01", "monthly_price": "31.00"}, {"date": "2024-03-16", "monthly_price": "31.00"}],
    )
    assert len(result["segments"]) == 1
    assert result["segments"][0]["days"] == 31
    assert result["total"] == Decimal("31.00")


def test_hidden_per_segment_rounding():
    # 30-day period: 10*10/30=3.33, 20*20/30=13.33
    result = prorate_period(
        "2024-04-01", "2024-05-01",
        [{"date": "2024-04-01", "monthly_price": "10.00"}, {"date": "2024-04-11", "monthly_price": "20.00"}],
    )
    assert [s["amount"] for s in result["segments"]] == [Decimal("3.33"), Decimal("13.33")]
    assert result["total"] == Decimal("16.66")


def test_hidden_entry_after_end_ignored():
    result = prorate_period(
        "2024-03-01", "2024-04-01",
        [{"date": "2024-03-01", "monthly_price": "31.00"}, {"date": "2024-05-01", "monthly_price": "999.00"}],
    )
    assert len(result["segments"]) == 1
    assert result["total"] == Decimal("31.00")


def test_hidden_entry_exactly_at_end_ignored():
    result = prorate_period(
        "2024-03-01", "2024-04-01",
        [{"date": "2024-03-01", "monthly_price": "31.00"}, {"date": "2024-04-01", "monthly_price": "62.00"}],
    )
    assert len(result["segments"]) == 1
    assert result["segments"][0]["to"] == "2024-04-01"


def test_hidden_entry_after_end_still_validated():
    with pytest.raises(ValueError):
        prorate_period(
            "2024-03-01", "2024-04-01",
            [{"date": "2024-03-01", "monthly_price": "31.00"}, {"date": "2024-05-01", "monthly_price": "-5.00"}],
        )


def test_hidden_plan_before_start_applies():
    result = prorate_period(
        "2024-03-01", "2024-04-01",
        [{"date": "2024-02-15", "monthly_price": "31.00"}],
    )
    assert len(result["segments"]) == 1
    assert result["segments"][0]["from"] == "2024-03-01"
    assert result["total"] == Decimal("31.00")


def test_hidden_latest_before_start_wins():
    result = prorate_period(
        "2024-03-01", "2024-04-01",
        [{"date": "2024-01-01", "monthly_price": "10.00"}, {"date": "2024-02-01", "monthly_price": "31.00"}],
    )
    assert len(result["segments"]) == 1
    assert result["segments"][0]["monthly_price"] == Decimal("31.00")


def test_hidden_zero_price():
    result = prorate_period("2024-01-01", "2024-02-01", [{"date": "2024-01-01", "monthly_price": "0.00"}])
    assert result["total"] == Decimal("0.00")
    assert result["segments"][0]["amount"] == Decimal("0.00")


def test_hidden_segment_days_sum_and_coverage():
    result = prorate_period(
        "2024-01-15", "2024-03-15",
        [
            {"date": "2024-01-01", "monthly_price": "60.00"},
            {"date": "2024-02-01", "monthly_price": "30.00"},
            {"date": "2024-03-01", "monthly_price": "90.00"},
        ],
    )
    assert sum(s["days"] for s in result["segments"]) == result["period_days"]
    assert result["segments"][0]["from"] == "2024-01-15"
    assert result["segments"][-1]["to"] == "2024-03-15"
    for a, b in zip(result["segments"], result["segments"][1:]):
        assert a["to"] == b["from"]
    assert result["total"] == sum((s["amount"] for s in result["segments"]), Decimal("0.00"))


def test_hidden_end_not_after_start_raises():
    with pytest.raises(ValueError):
        prorate_period("2024-04-01", "2024-04-01", [{"date": "2024-03-01", "monthly_price": "1.00"}])
    with pytest.raises(ValueError):
        prorate_period("2024-04-01", "2024-03-01", [{"date": "2024-03-01", "monthly_price": "1.00"}])


def test_hidden_no_plan_at_start_raises():
    with pytest.raises(ValueError):
        prorate_period("2024-03-01", "2024-04-01", [{"date": "2024-03-05", "monthly_price": "31.00"}])


def test_hidden_duplicate_date_raises():
    with pytest.raises(ValueError):
        prorate_period(
            "2024-03-01", "2024-04-01",
            [{"date": "2024-03-01", "monthly_price": "31.00"}, {"date": "2024-03-01", "monthly_price": "32.00"}],
        )


def test_hidden_empty_changes_raises():
    with pytest.raises(ValueError):
        prorate_period("2024-03-01", "2024-04-01", [])


def test_hidden_invalid_dates_raise():
    with pytest.raises(ValueError):
        prorate_period("2024-02-30", "2024-04-01", [{"date": "2024-02-01", "monthly_price": "1.00"}])
    with pytest.raises(ValueError):
        prorate_period("2024-03-01", "2024-04-01", [{"date": "not-a-date", "monthly_price": "1.00"}])


def test_hidden_invalid_price_raises():
    with pytest.raises(ValueError):
        prorate_period("2024-03-01", "2024-04-01", [{"date": "2024-03-01", "monthly_price": "10.005"}])
    with pytest.raises(ValueError):
        prorate_period("2024-03-01", "2024-04-01", [{"date": "2024-03-01", "monthly_price": "-1.00"}])
    with pytest.raises(ValueError):
        prorate_period("2024-03-01", "2024-04-01", [{"date": "2024-03-01", "monthly_price": "abc"}])


def test_hidden_missing_key_raises():
    with pytest.raises(ValueError):
        prorate_period("2024-03-01", "2024-04-01", [{"date": "2024-03-01"}])


def test_hidden_non_leap_feb_days():
    result = prorate_period("2023-02-01", "2023-03-01", [{"date": "2023-02-01", "monthly_price": "28.00"}])
    assert result["period_days"] == 28
    assert result["total"] == Decimal("28.00")
