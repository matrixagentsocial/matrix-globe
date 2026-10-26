from decimal import Decimal

import pytest

from solution import effective_rate_percent, income_tax, tax_breakdown


def test_hidden_zero_income():
    assert income_tax("0") == Decimal("0.00")
    assert income_tax("0.00") == Decimal("0.00")
    assert tax_breakdown("0") == []


def test_hidden_one_cent_tax_rounds_to_zero_but_row_present():
    rows = tax_breakdown("0.01")
    assert rows == [
        {
            "from": Decimal("0.00"),
            "to": Decimal("12450.00"),
            "rate_percent": 19,
            "taxable": Decimal("0.01"),
            "tax": Decimal("0.00"),
        }
    ]
    assert income_tax("0.01") == Decimal("0.00")


def test_hidden_first_bracket_full_row():
    assert tax_breakdown("12450") == [
        {
            "from": Decimal("0.00"),
            "to": Decimal("12450.00"),
            "rate_percent": 19,
            "taxable": Decimal("12450.00"),
            "tax": Decimal("2365.50"),
        }
    ]


def test_hidden_one_euro_into_second_bracket():
    rows = tax_breakdown("12451")
    assert len(rows) == 2
    assert rows[1] == {
        "from": Decimal("12450.00"),
        "to": Decimal("20200.00"),
        "rate_percent": 24,
        "taxable": Decimal("1.00"),
        "tax": Decimal("0.24"),
    }
    assert income_tax("12451") == Decimal("2365.74")


def test_hidden_tax_at_35200():
    assert income_tax("35200") == Decimal("8725.50")


def test_hidden_tax_at_60000():
    assert income_tax("60000") == Decimal("17901.50")


def test_hidden_tax_at_300000():
    assert income_tax("300000") == Decimal("125901.50")


def test_hidden_tax_above_top_bracket():
    assert income_tax("400000") == Decimal("172901.50")
    top = tax_breakdown("400000")[-1]
    assert top["from"] == Decimal("300000.00")
    assert top["to"] is None
    assert top["rate_percent"] == 47
    assert top["taxable"] == Decimal("100000.00")
    assert top["tax"] == Decimal("47000.00")


def test_hidden_breakdown_50000_full():
    rows = tax_breakdown("50000")
    assert [(str(r["from"]), str(r["to"]), r["rate_percent"]) for r in rows] == [
        ("0.00", "12450.00", 19),
        ("12450.00", "20200.00", 24),
        ("20200.00", "35200.00", 30),
        ("35200.00", "60000.00", 37),
    ]
    assert [r["taxable"] for r in rows] == [
        Decimal("12450.00"),
        Decimal("7750.00"),
        Decimal("15000.00"),
        Decimal("14800.00"),
    ]


def test_hidden_tax_breakdown_sum_agrees():
    for value in ["1.00", "30000", "100000", "300001", "123456.78"]:
        rows = tax_breakdown(value)
        assert sum((r["tax"] for r in rows), Decimal("0.00")) == income_tax(value)


def test_hidden_effective_rate_first_bracket():
    assert effective_rate_percent("10000") == Decimal("19.0000")
    assert effective_rate_percent("12450") == Decimal("19.0000")


def test_hidden_effective_rate_second_bracket():
    # 4225.50 / 20200 * 100 = 20.918316... -> 20.9183
    assert effective_rate_percent("20200") == Decimal("20.9183")


def test_hidden_effective_rate_top():
    # 172901.50 / 400000 * 100 = 43.225375 -> 43.2254
    assert effective_rate_percent("400000") == Decimal("43.2254")


def test_hidden_negative_raises():
    with pytest.raises(ValueError):
        income_tax("-1.00")


def test_hidden_three_decimals_raises():
    with pytest.raises(ValueError):
        tax_breakdown("10.005")


def test_hidden_non_numeric_raises():
    with pytest.raises(ValueError):
        income_tax("abc")


def test_hidden_empty_and_nan_raise():
    with pytest.raises(ValueError):
        income_tax("")
    with pytest.raises(ValueError):
        effective_rate_percent("NaN")
    with pytest.raises(ValueError):
        income_tax("Infinity")


def test_hidden_non_string_raises():
    with pytest.raises(ValueError):
        income_tax(10000)
