from decimal import Decimal

import pytest

from solution import round_money


def test_hidden_half_even_up_to_even():
    assert round_money("3.5", "JPY", "HALF_EVEN") == Decimal("4")


def test_hidden_half_even_eur_tie():
    assert round_money("1.015", "EUR", "HALF_EVEN") == Decimal("1.02")
    assert round_money("1.005", "EUR", "HALF_EVEN") == Decimal("1.00")


def test_hidden_half_up_negative_tie():
    assert round_money("-2.5", "JPY", "HALF_UP") == Decimal("-3")


def test_hidden_half_even_negative_tie():
    assert round_money("-2.5", "JPY", "HALF_EVEN") == Decimal("-2")


def test_hidden_down_truncates_positive():
    assert round_money("1.239", "EUR", "DOWN") == Decimal("1.23")


def test_hidden_down_truncates_negative_toward_zero():
    assert round_money("-1.239", "EUR", "DOWN") == Decimal("-1.23")


def test_hidden_up_away_from_zero_positive():
    assert round_money("1.231", "EUR", "UP") == Decimal("1.24")


def test_hidden_up_away_from_zero_negative():
    assert round_money("-1.231", "EUR", "UP") == Decimal("-1.24")


def test_hidden_kwd_three_places_half_up():
    assert round_money("0.0005", "KWD") == Decimal("0.001")


def test_hidden_krw_zero_places():
    result = round_money("999.4", "KRW")
    assert result == Decimal("999")
    assert result.as_tuple().exponent == 0


def test_hidden_eur_exponent_two():
    assert round_money("1.2", "EUR").as_tuple().exponent == -2


def test_hidden_lowercase_currency_and_mode():
    assert round_money("1.005", "eur", "half_up") == Decimal("1.01")


def test_hidden_no_cash_rounding_chf():
    assert round_money("1.03", "CHF") == Decimal("1.03")
    assert round_money("1.025", "CHF", "HALF_UP") == Decimal("1.03")


def test_hidden_zero_amount():
    assert round_money("0", "JPY") == Decimal("0")
    assert round_money("0.000", "BHD") == Decimal("0.000")


def test_hidden_unknown_mode_raises():
    with pytest.raises(ValueError):
        round_money("1.00", "EUR", "CEILING")


def test_hidden_unknown_currency_raises():
    with pytest.raises(ValueError):
        round_money("1.00", "BTC")


def test_hidden_invalid_amount_raises():
    with pytest.raises(ValueError):
        round_money("abc", "EUR")


def test_hidden_nan_raises():
    with pytest.raises(ValueError):
        round_money("NaN", "EUR")


def test_hidden_exact_tie_bhd_half_even():
    # 1.0025 at 3 places: tie, even neighbour is 1.002.
    assert round_money("1.0025", "BHD", "HALF_EVEN") == Decimal("1.002")
    assert round_money("1.0035", "BHD", "HALF_EVEN") == Decimal("1.004")
