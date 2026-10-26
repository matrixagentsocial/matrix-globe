from decimal import Decimal

import pytest

from solution import apply_percent_change, percent_change


def test_hidden_decrease_rounding():
    assert percent_change("110", "100") == Decimal("-9.09")


def test_hidden_negative_base_rise():
    assert percent_change("-200", "-100") == Decimal("50.00")


def test_hidden_negative_base_fall():
    assert percent_change("-200", "-300") == Decimal("-50.00")


def test_hidden_negative_base_small():
    assert percent_change("-100", "-50") == Decimal("50.00")
    assert percent_change("-100", "-150") == Decimal("-50.00")


def test_hidden_small_values():
    assert percent_change("3", "2") == Decimal("-33.33")


def test_hidden_zero_variants():
    assert percent_change("0.00", "0.00") == Decimal("0.00")
    assert percent_change("-0", "0") == Decimal("0.00")
    assert percent_change("0", "-5") is None


def test_hidden_same_value_zero_change():
    assert percent_change("42.50", "42.50") == Decimal("0.00")


def test_hidden_half_up_rounding():
    # 1/800*100 = 0.125 -> 0.13 with HALF_UP.
    assert percent_change("800", "801") == Decimal("0.13")


def test_hidden_two_dp_exponent():
    assert percent_change("100", "110").as_tuple().exponent == -2
    assert apply_percent_change("100.00", "10").as_tuple().exponent == -2


def test_hidden_apply_negative_percent():
    assert apply_percent_change("100.00", "-10") == Decimal("90.00")


def test_hidden_apply_fractional_percent():
    assert apply_percent_change("50.00", "2.5") == Decimal("51.25")


def test_hidden_apply_zero_old():
    assert apply_percent_change("0.00", "10") == Decimal("0.00")


def test_hidden_apply_rounding():
    assert apply_percent_change("33.33", "10") == Decimal("36.66")


def test_hidden_apply_negative_old():
    assert apply_percent_change("-100.00", "10") == Decimal("-110.00")


def test_hidden_nan_raises():
    with pytest.raises(ValueError):
        percent_change("NaN", "5")


def test_hidden_infinity_percent_raises():
    with pytest.raises(ValueError):
        apply_percent_change("100.00", "Infinity")


def test_hidden_empty_raises():
    with pytest.raises(ValueError):
        apply_percent_change("", "10")


def test_hidden_many_dp_accepted():
    assert percent_change("10.005", "10.005") == Decimal("0.00")
