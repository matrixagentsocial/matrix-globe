from decimal import Decimal

import pytest

from solution import convert_fx, cross_rate

RATES = {"USD": "1.10", "GBP": "0.88", "JPY": "160", "KRW": "1400", "CHF": "0.95"}


def test_hidden_lowercase_codes():
    assert convert_fx("110", "usd", "gbp", RATES) == Decimal("88.00")


def test_hidden_lowercase_rate_keys():
    assert convert_fx("110", "USD", "GBP", {"usd": "1.10", "gbp": "0.88"}) == Decimal("88.00")


def test_hidden_eur_omitted_and_to_eur():
    assert convert_fx("110", "USD", "EUR", {"USD": "1.10"}) == Decimal("100.00")


def test_hidden_eur_rate_not_one_raises():
    with pytest.raises(ValueError):
        convert_fx("10", "EUR", "USD", {"EUR": "1.01", "USD": "1.10"})


def test_hidden_no_intermediate_rounding():
    # 1 / 3 = 0.333... EUR; * 3 back would be 1 if rounded, exact chain: 1/3*2 -> 0.67 (via rate 2 currency XYZ known, 2dp)
    assert convert_fx("1", "AAA", "BBB", {"AAA": "3", "BBB": "2"}) == Decimal("0.67")


def test_hidden_unknown_currency_uses_two_minor_units():
    # XYZ is only known because it is in rates; outside table -> 2dp
    assert convert_fx("10", "EUR", "XYZ", {"XYZ": "2.005"}) == Decimal("20.05")


def test_hidden_jpy_half_up_zero_dp():
    # 1 EUR = 160.5 JPY -> 161 at 0dp HALF_UP (use exact rate)
    assert convert_fx("1", "EUR", "JPY", {"JPY": "160.5"}) == Decimal("161")


def test_hidden_negative_half_up_away_from_zero():
    assert convert_fx("-100.5", "JPY", "JPY", {"JPY": "160"}) == Decimal("-101")


def test_hidden_negative_conversion():
    assert convert_fx("-110", "USD", "GBP", RATES) == Decimal("-88.00")


def test_hidden_same_currency_unknown_no_lookup():
    assert convert_fx("10.004", "XYZ", "XYZ", {}) == Decimal("10.00")


def test_hidden_same_currency_bad_rates_ignored():
    assert convert_fx("10.00", "USD", "USD", {"USD": "0"}) == Decimal("10.00")


def test_hidden_krw_zero_dp_conversion():
    assert convert_fx("2", "EUR", "KRW", RATES) == Decimal("2800")


def test_hidden_cross_rate_same_known():
    result = cross_rate("USD", "USD", RATES)
    assert result == Decimal("1.0000000000")
    assert result.as_tuple().exponent == -10


def test_hidden_cross_rate_jpy_usd():
    # 1.10 / 160 = 0.006875 exactly
    assert cross_rate("JPY", "USD", RATES) == Decimal("0.0068750000")


def test_hidden_cross_rate_unknown_raises():
    with pytest.raises(ValueError):
        cross_rate("USD", "XXX", RATES)


def test_hidden_zero_rate_raises():
    with pytest.raises(ValueError):
        convert_fx("10", "USD", "GBP", {"USD": "0", "GBP": "0.88"})


def test_hidden_negative_unused_rate_raises():
    with pytest.raises(ValueError):
        convert_fx("10", "USD", "GBP", {"USD": "1.10", "GBP": "0.88", "CHF": "-1"})


def test_hidden_invalid_amount_raises():
    with pytest.raises(ValueError):
        convert_fx("NaN", "USD", "GBP", RATES)


def test_hidden_short_code_raises():
    with pytest.raises(ValueError):
        convert_fx("10", "US", "GBP", RATES)


def test_hidden_float_rate_raises():
    with pytest.raises(ValueError):
        convert_fx("10", "USD", "GBP", {"USD": 1.10, "GBP": "0.88"})
