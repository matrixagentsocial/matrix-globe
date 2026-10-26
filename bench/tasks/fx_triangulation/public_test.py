from decimal import Decimal

import pytest

from solution import convert_fx, cross_rate

RATES = {"USD": "1.10", "GBP": "0.88", "JPY": "160"}


def test_public_usd_to_gbp_example():
    assert convert_fx("110", "USD", "GBP", RATES) == Decimal("88.00")


def test_public_eur_to_jpy_zero_places():
    assert convert_fx("100", "EUR", "JPY", RATES) == Decimal("16000")


def test_public_cross_rate():
    assert cross_rate("USD", "GBP", RATES) == Decimal("0.8000000000")


def test_public_same_currency_rounds():
    assert convert_fx("10.005", "USD", "USD", RATES) == Decimal("10.01")


def test_public_unknown_currency_raises():
    with pytest.raises(ValueError):
        convert_fx("10", "USD", "XXX", RATES)
