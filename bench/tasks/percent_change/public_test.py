from decimal import Decimal

import pytest

from solution import apply_percent_change, percent_change


def test_public_increase():
    assert percent_change("100", "110") == Decimal("10.00")


def test_public_zero_to_nonzero_none():
    assert percent_change("0", "5") is None


def test_public_zero_to_zero():
    assert percent_change("0", "0") == Decimal("0.00")


def test_public_apply():
    assert apply_percent_change("100.00", "10") == Decimal("110.00")


def test_public_bad_input_raises():
    with pytest.raises(ValueError):
        percent_change("abc", "5")
