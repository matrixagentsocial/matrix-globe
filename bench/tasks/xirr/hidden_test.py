from decimal import Decimal

import pytest

from solution import npv, xirr

CF1 = [("2023-01-01", "-1000"), ("2024-01-01", "1100")]


def test_hidden_xirr_two_year_ten_percent():
    flows = [("2021-01-01", "-1000"), ("2023-01-01", "1210")]
    assert xirr(flows) == Decimal("10.000000")


def test_hidden_xirr_zero_rate():
    flows = [("2023-01-01", "-1000"), ("2024-01-01", "1000")]
    assert xirr(flows) == Decimal("0.000000")


def test_hidden_xirr_negative_rate():
    flows = [("2023-01-01", "-1000"), ("2024-01-01", "900")]
    assert xirr(flows) == Decimal("-10.000000")
    assert npv("-10", flows) == Decimal("0.00")


def test_hidden_xirr_combines_same_date():
    flows = [
        ("2023-01-01", "-600"),
        ("2023-01-01", "-400"),
        ("2024-01-01", "1100"),
    ]
    assert xirr(flows) == Decimal("10.000000")


def test_hidden_xirr_unsorted_input():
    flows = [("2024-01-01", "1100"), ("2023-01-01", "-1000")]
    assert xirr(flows) == Decimal("10.000000")


def test_hidden_xirr_multi_flow_ten_percent():
    # -1000 + 550/1.1 + 605/1.21 = -1000 + 500 + 500 = 0.
    flows = [
        ("2021-01-01", "-1000"),
        ("2022-01-01", "550"),
        ("2023-01-01", "605"),
    ]
    assert xirr(flows) == Decimal("10.000000")
    assert npv("10", flows) == Decimal("0.00")
    assert npv("0", flows) == Decimal("155.00")


def test_hidden_xirr_twenty_one_percent():
    flows = [("2022-01-01", "-2000"), ("2023-01-01", "2420")]
    assert xirr(flows) == Decimal("21.000000")


def test_hidden_xirr_cents_amounts():
    # 500.25 * 1.1 = 550.275 exactly.
    flows = [("2022-01-01", "-500.25"), ("2023-01-01", "550.275")]
    assert xirr(flows) == Decimal("10.000000")


def test_hidden_xirr_result_exponent():
    result = xirr(CF1)
    assert result.as_tuple().exponent == -6
    assert str(result) == "10.000000"


def test_hidden_npv_twenty_percent():
    # -1000 + 1100/1.2 = -83.333... -> -83.33.
    assert npv("20", CF1) == Decimal("-83.33")


def test_hidden_npv_five_percent():
    # -1000 + 1100/1.05 = 47.619... -> 47.62.
    assert npv("5", CF1) == Decimal("47.62")


def test_hidden_npv_result_exponent():
    result = npv("7", CF1)
    assert result.as_tuple().exponent == -2


def test_hidden_npv_rate_minus_99():
    # 1 + r = 0.01, so 1100 / 0.01 = 110000; 110000 - 1000 = 109000.
    assert npv("-99", CF1) == Decimal("109000.00")


def test_hidden_npv_decimal_rate():
    # -1000 + 1100/1.105 = -4.5248... -> -4.52.
    assert npv("10.5", CF1) == Decimal("-4.52")


def test_hidden_single_distinct_date_raises():
    flows = [("2023-01-01", "-1000"), ("2023-01-01", "1100")]
    with pytest.raises(ValueError):
        xirr(flows)
    with pytest.raises(ValueError):
        npv("10", flows)


def test_hidden_all_positive_raises():
    flows = [("2023-01-01", "100"), ("2024-01-01", "100")]
    with pytest.raises(ValueError):
        xirr(flows)
    with pytest.raises(ValueError):
        npv("5", flows)


def test_hidden_empty_and_all_zero_raise():
    with pytest.raises(ValueError):
        xirr([])
    with pytest.raises(ValueError):
        xirr([("2023-01-01", "0"), ("2024-01-01", "0")])


def test_hidden_bad_date_and_amount_raise():
    with pytest.raises(ValueError):
        xirr([("2023-13-01", "-1000"), ("2024-01-01", "1100")])
    with pytest.raises(ValueError):
        npv("10", [("2023-01-01", "-1000"), ("2024-01-01", "abc")])
    with pytest.raises(ValueError):
        npv("10", [("2023-01-01", "NaN"), ("2024-01-01", "1100")])


def test_hidden_rate_at_or_below_minus_100_raises():
    with pytest.raises(ValueError):
        npv("-100", CF1)
    with pytest.raises(ValueError):
        npv("-150", CF1)
    with pytest.raises(ValueError):
        npv("abc", CF1)


def test_hidden_xirr_no_root_raises():
    # -1000 + 3000x - 2500x^2 (x = 1/(1+r)) has negative discriminant
    # (3000^2 - 4*2500*1000 < 0) and is always negative: no root exists.
    flows = [
        ("2021-01-01", "-1000"),
        ("2022-01-01", "3000"),
        ("2023-01-01", "-2500"),
    ]
    with pytest.raises(ValueError):
        xirr(flows)
