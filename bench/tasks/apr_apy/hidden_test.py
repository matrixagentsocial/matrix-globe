from decimal import Decimal

import pytest

from solution import apr_to_apy, apy_to_apr


def test_hidden_apr_annually():
    assert apr_to_apy("12", "annually") == Decimal("12.000000")


def test_hidden_apr_semiannually():
    assert apr_to_apy("12", "semiannually") == Decimal("12.360000")


def test_hidden_apr_quarterly():
    assert apr_to_apy("12", "quarterly") == Decimal("12.550881")


def test_hidden_apr_daily():
    assert apr_to_apy("12", "daily") == Decimal("12.747462")


def test_hidden_apr_daily_six():
    assert apr_to_apy("6", "daily") == Decimal("6.183131")


def test_hidden_apr_monthly_five_point_five():
    assert apr_to_apy("5.5", "monthly") == Decimal("5.640786")


def test_hidden_apr_negative_monthly():
    assert apr_to_apy("-6", "monthly") == Decimal("-5.837719")


def test_hidden_apy_continuous_inverse():
    assert apy_to_apr("12.749685", "continuous") == Decimal("12.000000")


def test_hidden_apy_quarterly_ten():
    assert apy_to_apr("10", "quarterly") == Decimal("9.645476")


def test_hidden_apy_continuous_ten():
    assert apy_to_apr("10", "continuous") == Decimal("9.531018")


def test_hidden_round_trip_monthly():
    assert apy_to_apr(str(apr_to_apy("12", "monthly")), "monthly") == Decimal("12.000000")


def test_hidden_round_trip_continuous():
    assert apy_to_apr(str(apr_to_apy("12", "continuous")), "continuous") == Decimal("12.000000")


def test_hidden_case_insensitive_frequency():
    assert apr_to_apy("12", "MONTHLY") == Decimal("12.682503")
    assert apr_to_apy("12", "Monthly") == Decimal("12.682503")
    assert apy_to_apr("12.682503", "MONTHLY") == Decimal("12.000000")


def test_hidden_output_exponent_six():
    assert apr_to_apy("12", "monthly").as_tuple().exponent == -6
    assert apy_to_apr("10", "quarterly").as_tuple().exponent == -6
    assert apr_to_apy("0", "annually") == Decimal("0.000000")


def test_hidden_large_apr_monthly():
    assert apr_to_apy("100", "monthly") == Decimal("161.303529")


def test_hidden_minus_100_apr_raises():
    with pytest.raises(ValueError):
        apr_to_apy("-100", "monthly")


def test_hidden_below_minus_100_apy_raises():
    with pytest.raises(ValueError):
        apy_to_apr("-100.01", "daily")


def test_hidden_unknown_frequency_raises():
    with pytest.raises(ValueError):
        apr_to_apy("12", "biweekly")


def test_hidden_non_numeric_apr_raises():
    with pytest.raises(ValueError):
        apr_to_apy("abc", "monthly")


def test_hidden_nan_raises():
    with pytest.raises(ValueError):
        apy_to_apr("NaN", "monthly")
