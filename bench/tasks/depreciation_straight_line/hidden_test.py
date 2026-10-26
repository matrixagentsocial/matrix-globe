from decimal import Decimal

import pytest

from solution import straight_line_schedule


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


def test_hidden_salvage_equal_cost_raises():
    with pytest.raises(ValueError):
        straight_line_schedule("1000", "1000", 5, 2024, 1)


def test_hidden_salvage_greater_than_cost_raises():
    with pytest.raises(ValueError):
        straight_line_schedule("1000", "1000.01", 5, 2024, 1)


def test_hidden_negative_salvage_raises():
    with pytest.raises(ValueError):
        straight_line_schedule("1000", "-1", 5, 2024, 1)


def test_hidden_zero_cost_raises():
    with pytest.raises(ValueError):
        straight_line_schedule("0", "0", 5, 2024, 1)


def test_hidden_cost_three_decimals_raises():
    with pytest.raises(ValueError):
        straight_line_schedule("1000.005", "0", 5, 2024, 1)


def test_hidden_non_numeric_cost_raises():
    with pytest.raises(ValueError):
        straight_line_schedule("abc", "0", 5, 2024, 1)


def test_hidden_life_too_large_raises():
    with pytest.raises(ValueError):
        straight_line_schedule("1000", "0", 51, 2024, 1)


def test_hidden_life_bool_raises():
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
