from decimal import Decimal

import pytest

from solution import amortize, total_interest


def test_hidden_worked_example_full_rows():
    assert amortize("100.00", "12", 3, "2024-01-15") == [
        {"n": 1, "date": "2024-02-15", "payment": Decimal("34.00"), "interest": Decimal("1.00"), "principal": Decimal("33.00"), "balance": Decimal("67.00")},
        {"n": 2, "date": "2024-03-15", "payment": Decimal("34.00"), "interest": Decimal("0.67"), "principal": Decimal("33.33"), "balance": Decimal("33.67")},
        {"n": 3, "date": "2024-04-15", "payment": Decimal("34.01"), "interest": Decimal("0.34"), "principal": Decimal("33.67"), "balance": Decimal("0.00")},
    ]


def test_hidden_zero_rate_final_cent():
    schedule = amortize("100.00", "0", 3, "2024-01-15")
    assert [row["principal"] for row in schedule] == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
    assert [row["balance"] for row in schedule] == [Decimal("66.67"), Decimal("33.34"), Decimal("0.00")]
    assert all(row["interest"] == Decimal("0.00") for row in schedule)


def test_hidden_single_month():
    assert amortize("100.00", "12", 1, "2024-01-15") == [
        {"n": 1, "date": "2024-02-15", "payment": Decimal("101.00"), "interest": Decimal("1.00"), "principal": Decimal("100.00"), "balance": Decimal("0.00")}
    ]


def test_hidden_anchor_31_dates_full_year():
    schedule = amortize("1200.00", "0", 12, "2024-01-31")
    assert [row["date"] for row in schedule] == [
        "2024-02-29", "2024-03-31", "2024-04-30", "2024-05-31",
        "2024-06-30", "2024-07-31", "2024-08-31", "2024-09-30",
        "2024-10-31", "2024-11-30", "2024-12-31", "2025-01-31",
    ]
    assert [row["payment"] for row in schedule] == [Decimal("100.00")] * 12


def test_hidden_anchor_restored_after_feb_clamp():
    schedule = amortize("100.00", "12", 2, "2024-01-31")
    assert [row["date"] for row in schedule] == ["2024-02-29", "2024-03-31"]
    assert [row["payment"] for row in schedule] == [Decimal("50.75"), Decimal("50.75")]
    assert [row["interest"] for row in schedule] == [Decimal("1.00"), Decimal("0.50")]
    assert schedule[-1]["balance"] == Decimal("0.00")


def test_hidden_year_rollover_with_interest():
    schedule = amortize("500.00", "6", 6, "2023-12-31")
    assert [row["date"] for row in schedule] == [
        "2024-01-31", "2024-02-29", "2024-03-31",
        "2024-04-30", "2024-05-31", "2024-06-30",
    ]
    assert [row["payment"] for row in schedule] == [Decimal("84.80")] * 5 + [Decimal("84.78")]
    assert [row["interest"] for row in schedule] == [
        Decimal("2.50"), Decimal("2.09"), Decimal("1.67"),
        Decimal("1.26"), Decimal("0.84"), Decimal("0.42"),
    ]
    assert total_interest(schedule) == Decimal("8.78")


def test_hidden_twelve_month_known_schedule():
    schedule = amortize("1000.00", "12", 12, "2024-01-01")
    assert schedule[0]["payment"] == Decimal("88.85")
    assert schedule[0]["interest"] == Decimal("10.00")
    assert schedule[0]["balance"] == Decimal("921.15")
    assert schedule[-1]["payment"] == Decimal("88.84")
    assert schedule[-1]["interest"] == Decimal("0.88")
    assert schedule[-1]["balance"] == Decimal("0.00")
    assert sum(row["principal"] for row in schedule) == Decimal("1000.00")
    assert total_interest(schedule) == Decimal("66.19")


def test_hidden_money_exponents_and_keys():
    schedule = amortize("250.00", "9", 5, "2024-03-10")
    assert len(schedule) == 5
    for index, row in enumerate(schedule, start=1):
        assert set(row.keys()) == {"n", "date", "payment", "interest", "principal", "balance"}
        assert row["n"] == index
        for key in ("payment", "interest", "principal", "balance"):
            assert row[key].as_tuple().exponent == -2
    assert schedule[-1]["balance"] == Decimal("0.00")


def test_hidden_total_interest_empty():
    assert total_interest([]) == Decimal("0.00")
    assert total_interest([]).as_tuple().exponent == -2


def test_hidden_principal_three_decimals_raises():
    with pytest.raises(ValueError):
        amortize("10.005", "12", 3, "2024-01-15")


def test_hidden_principal_zero_and_negative_raise():
    with pytest.raises(ValueError):
        amortize("0.00", "12", 3, "2024-01-15")
    with pytest.raises(ValueError):
        amortize("-100.00", "12", 3, "2024-01-15")


def test_hidden_principal_nonstring_and_nan_raise():
    with pytest.raises(ValueError):
        amortize(100, "12", 3, "2024-01-15")
    with pytest.raises(ValueError):
        amortize("NaN", "12", 3, "2024-01-15")
    with pytest.raises(ValueError):
        amortize("abc", "12", 3, "2024-01-15")


def test_hidden_rate_out_of_range_raises():
    with pytest.raises(ValueError):
        amortize("100.00", "100.01", 3, "2024-01-15")
    with pytest.raises(ValueError):
        amortize("100.00", "-0.01", 3, "2024-01-15")


def test_hidden_rate_invalid_raises():
    with pytest.raises(ValueError):
        amortize("100.00", "abc", 3, "2024-01-15")
    with pytest.raises(ValueError):
        amortize("100.00", 12, 3, "2024-01-15")


def test_hidden_months_bool_raises():
    with pytest.raises(ValueError):
        amortize("100.00", "12", True, "2024-01-15")


def test_hidden_months_bounds_raise():
    with pytest.raises(ValueError):
        amortize("100.00", "12", 361, "2024-01-15")
    with pytest.raises(ValueError):
        amortize("100.00", "12", -1, "2024-01-15")


def test_hidden_months_nonint_raises():
    with pytest.raises(ValueError):
        amortize("100.00", "12", 2.5, "2024-01-15")
    with pytest.raises(ValueError):
        amortize("100.00", "12", "3", "2024-01-15")


def test_hidden_bad_start_date_raises():
    with pytest.raises(ValueError):
        amortize("100.00", "12", 3, "2024-02-30")
    with pytest.raises(ValueError):
        amortize("100.00", "12", 3, "15/01/2024")
    with pytest.raises(ValueError):
        amortize("100.00", "12", 3, "2024-13-01")
