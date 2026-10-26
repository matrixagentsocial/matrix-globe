from decimal import Decimal

import pytest

from solution import allocate_by_ratios


def test_hidden_sum_exact_and_length():
    parts = allocate_by_ratios("99.99", [1, 2, 3, 4])
    assert len(parts) == 4 and sum(parts) == Decimal("99.99")


def test_hidden_remainder_to_largest_fraction():
    # 5 cents by [1,2]: floors 1 and 3, remainder to index 0 (frac .666 > .333).
    assert allocate_by_ratios("0.05", [1, 2]) == [Decimal("0.02"), Decimal("0.03")]


def test_hidden_exact_shares_no_remainder():
    assert allocate_by_ratios("0.03", [1, 2]) == [Decimal("0.01"), Decimal("0.02")]


def test_hidden_zero_weight_never_gets_remainder():
    # 1 cent by [0,1,1]: remainder cent must go to index 1 (lower positive index), never index 0.
    assert allocate_by_ratios("0.01", [0, 1, 1]) == [Decimal("0.00"), Decimal("0.01"), Decimal("0.00")]


def test_hidden_negative_total():
    assert allocate_by_ratios("-100.00", [1, 1, 1]) == [Decimal("-33.34"), Decimal("-33.33"), Decimal("-33.33")]


def test_hidden_negative_one_cent():
    parts = allocate_by_ratios("-0.01", [1, 1])
    assert parts == [Decimal("-0.01"), Decimal("0.00")] and sum(parts) == Decimal("-0.01")


def test_hidden_zero_total():
    assert allocate_by_ratios("0.00", [1, 2]) == [Decimal("0.00"), Decimal("0.00")]


def test_hidden_string_weights():
    assert allocate_by_ratios("10.00", ["2", "1", "1"]) == [Decimal("5.00"), Decimal("2.50"), Decimal("2.50")]


def test_hidden_fractional_string_weights():
    assert allocate_by_ratios("10.00", ["1.5", "1.5"]) == [Decimal("5.00"), Decimal("5.00")]


def test_hidden_weight_tiebreak_larger_weight_first():
    # 2 cents by [1,3]: exact 0.5 and 1.5, floors 0 and 1, one remainder cent;
    # fractional remainders tie (0.5 each), larger weight (index 1) wins.
    assert allocate_by_ratios("0.02", [1, 3]) == [Decimal("0.00"), Decimal("0.02")]


def test_hidden_two_dp_exponent():
    for part in allocate_by_ratios("10.00", [1, 1, 1]):
        assert part.as_tuple().exponent == -2


def test_hidden_all_zero_weights_raise():
    with pytest.raises(ValueError):
        allocate_by_ratios("10.00", [0, 0])


def test_hidden_negative_weight_raises():
    with pytest.raises(ValueError):
        allocate_by_ratios("10.00", [1, -1])


def test_hidden_bool_weight_raises():
    with pytest.raises(ValueError):
        allocate_by_ratios("10.00", [True, 1])


def test_hidden_float_weight_raises():
    with pytest.raises(ValueError):
        allocate_by_ratios("10.00", [1.0, 1])


def test_hidden_three_dp_total_raises():
    with pytest.raises(ValueError):
        allocate_by_ratios("10.005", [1, 1])


def test_hidden_bad_total_raises():
    with pytest.raises(ValueError):
        allocate_by_ratios("abc", [1])


def test_hidden_single_ratio_gets_all():
    assert allocate_by_ratios("42.50", [7]) == [Decimal("42.50")]
