from decimal import Decimal

import pytest

from solution import accrued_interest, day_count_fraction


def test_public_us_example():
    assert day_count_fraction("2024-01-31", "2024-07-31", "30/360_US") == Decimal("0.5000000000")


def test_public_act_act_whole_year():
    assert day_count_fraction("2023-01-01", "2024-01-01", "ACT/ACT_ISDA") == Decimal("1.0000000000")


def test_public_act_act_split_years():
    assert day_count_fraction("2023-12-01", "2024-02-01", "ACT/ACT_ISDA") == Decimal("0.1696309604")


def test_public_act_365f():
    assert day_count_fraction("2024-01-01", "2024-04-01", "ACT/365F") == Decimal("0.2493150685")


def test_public_accrued_example():
    assert accrued_interest("10000.00", "5", "2024-01-31", "2024-07-31", "30/360_US") == Decimal("250.00")
