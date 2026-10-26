from decimal import Decimal

import pytest

from solution import round_money


def test_round_eur_half_up():
    assert round_money("1.005", "EUR") == Decimal("1.01")


def test_round_jpy_zero_places():
    assert round_money("123.5", "JPY") == Decimal("124")


def test_round_half_even():
    assert round_money("2.5", "JPY", "HALF_EVEN") == Decimal("2")


def test_round_unknown_currency():
    with pytest.raises(ValueError):
        round_money("1.00", "XXX")


def test_round_bhd_three_places():
    assert round_money("1.0005", "BHD") == Decimal("1.001")
