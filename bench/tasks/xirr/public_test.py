from decimal import Decimal

import pytest

from solution import npv, xirr

CF_ONE_YEAR = [("2023-01-01", "-1000"), ("2024-01-01", "1100")]


def test_public_xirr_ten_percent_one_year():
    assert xirr(CF_ONE_YEAR) == Decimal("10.000000")


def test_public_xirr_ten_percent_two_years():
    flows = [("2021-01-01", "-1000"), ("2023-01-01", "1210")]
    assert xirr(flows) == Decimal("10.000000")


def test_public_npv_zero_at_true_rate():
    assert npv("10", CF_ONE_YEAR) == Decimal("0.00")


def test_public_npv_zero_rate_is_plain_sum():
    assert npv("0", CF_ONE_YEAR) == Decimal("100.00")


def test_public_xirr_all_positive_raises():
    with pytest.raises(ValueError):
        xirr([("2023-01-01", "100"), ("2024-01-01", "100")])
