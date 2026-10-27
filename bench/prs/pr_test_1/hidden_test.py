# --- hidden tests for allocate_ratios (module task_a.py) ---
from decimal import Decimal

import pytest

from task_a import allocate_by_ratios


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

# --- hidden tests for apr_apy (module task_b.py) ---
from decimal import Decimal

import pytest

from task_b import apr_to_apy, apy_to_apr


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

# --- hidden tests for bank_reconciliation (module task_c.py) ---
import pytest

from task_c import reconcile


def e(i, d, a):
    return {"id": i, "date": d, "amount": a}


def test_hidden_outside_tolerance_no_match():
    r = reconcile([e("b1", "2024-01-01", "10.00")], [e("k1", "2024-01-10", "10.00")], tolerance_days=3)
    assert r["matches"] == []
    assert r["unmatched_book"] == ["b1"]
    assert r["unmatched_bank"] == ["k1"]


def test_hidden_tolerance_boundary_inclusive():
    r = reconcile([e("b1", "2024-01-01", "10.00")], [e("k1", "2024-01-04", "10.00")], tolerance_days=3)
    assert r["matches"] == [{"bank_id": "k1", "book_ids": ["b1"]}]


def test_hidden_zero_tolerance_same_day_only():
    r = reconcile([e("b1", "2024-01-01", "10.00")], [e("k1", "2024-01-02", "10.00")], tolerance_days=0)
    assert r["matches"] == []


def test_hidden_sign_matters():
    r = reconcile([e("b1", "2024-01-01", "-10.00")], [e("k1", "2024-01-01", "10.00")])
    assert r["matches"] == []


def test_hidden_negative_match():
    r = reconcile([e("b1", "2024-01-01", "-10.00")], [e("k1", "2024-01-01", "-10.00")])
    assert r["matches"] == [{"bank_id": "k1", "book_ids": ["b1"]}]


def test_hidden_greedy_smallest_diff_wins():
    # b1 can match k_far (diff2) or k_near (diff1); greedy picks k_near, k_far unmatched (no phase2 subset)
    r = reconcile(
        [e("b1", "2024-01-05", "10.00")],
        [e("k_far", "2024-01-07", "10.00"), e("k_near", "2024-01-06", "10.00")],
    )
    assert r["matches"] == [{"bank_id": "k_near", "book_ids": ["b1"]}]
    assert r["unmatched_bank"] == ["k_far"]


def test_hidden_greedy_tie_bank_id():
    # same diff, same bank date -> bank id decides; b1 goes to k_a
    r = reconcile(
        [e("b1", "2024-01-05", "10.00")],
        [e("k_b", "2024-01-06", "10.00"), e("k_a", "2024-01-06", "10.00")],
    )
    assert r["matches"] == [{"bank_id": "k_a", "book_ids": ["b1"]}]
    assert r["unmatched_bank"] == ["k_b"]


def test_hidden_greedy_tie_book_id():
    # one bank, two identical book entries: smallest book id wins
    r = reconcile(
        [e("b_b", "2024-01-05", "10.00"), e("b_a", "2024-01-05", "10.00")],
        [e("k1", "2024-01-05", "10.00")],
    )
    assert r["matches"] == [{"bank_id": "k1", "book_ids": ["b_a"]}]
    assert r["unmatched_book"] == ["b_b"]


def test_hidden_phase1_before_phase2():
    # b1+b2 sum to k2, but b1 first phase1-matches k1, so k2 cannot use b1
    r = reconcile(
        [e("b1", "2024-01-05", "60.00"), e("b2", "2024-01-05", "40.00")],
        [e("k1", "2024-01-05", "60.00"), e("k2", "2024-01-05", "100.00")],
    )
    assert r["matches"] == [{"bank_id": "k1", "book_ids": ["b1"]}]
    assert r["unmatched_book"] == ["b2"]
    assert r["unmatched_bank"] == ["k2"]


def test_hidden_phase2_prefers_size2_over_size3():
    r = reconcile(
        [e("b1", "2024-01-05", "50.00"), e("b2", "2024-01-05", "50.00"),
         e("b3", "2024-01-05", "30.00"), e("b4", "2024-01-05", "30.00"), e("b5", "2024-01-05", "40.00")],
        [e("k1", "2024-01-05", "100.00")],
    )
    # size2 subsets: (b1,b2) ids tuple smallest among maxdiff ties -> b1,b2
    assert r["matches"] == [{"bank_id": "k1", "book_ids": ["b1", "b2"]}]


def test_hidden_phase2_size3_when_no_size2():
    r = reconcile(
        [e("b1", "2024-01-05", "30.00"), e("b2", "2024-01-05", "30.00"), e("b3", "2024-01-05", "40.00")],
        [e("k1", "2024-01-05", "100.00")],
    )
    assert r["matches"] == [{"bank_id": "k1", "book_ids": ["b1", "b2", "b3"]}]


def test_hidden_phase2_lexicographic_tiebreak():
    # two size-2 subsets same maxdiff: (b1,b4)=60+40 and (b2,b3)=50+50 ; lexicographically (b1,b4) < (b2,b3)
    r = reconcile(
        [e("b1", "2024-01-05", "60.00"), e("b4", "2024-01-05", "40.00"),
         e("b2", "2024-01-05", "50.00"), e("b3", "2024-01-05", "50.00")],
        [e("k1", "2024-01-05", "100.00")],
    )
    assert r["matches"] == [{"bank_id": "k1", "book_ids": ["b1", "b4"]}]


def test_hidden_phase2_maxdiff_tiebreak():
    # (b1,b2) maxdiff 3, (b3,b4) maxdiff 0 -> prefers maxdiff 0 even though ids larger
    r = reconcile(
        [e("b1", "2024-01-02", "60.00"), e("b2", "2024-01-05", "40.00"),
         e("b3", "2024-01-05", "50.00"), e("b4", "2024-01-05", "50.00")],
        [e("k1", "2024-01-05", "100.00")],
    )
    assert r["matches"] == [{"bank_id": "k1", "book_ids": ["b3", "b4"]}]


def test_hidden_phase2_signed_sum():
    r = reconcile(
        [e("b1", "2024-01-05", "120.00"), e("b2", "2024-01-05", "-20.00")],
        [e("k1", "2024-01-05", "100.00")],
    )
    assert r["matches"] == [{"bank_id": "k1", "book_ids": ["b1", "b2"]}]


def test_hidden_matches_merged_bank_order():
    # phase2 match for earlier bank, phase1 for later bank -> output in bank date order
    r = reconcile(
        [e("b1", "2024-01-01", "60.00"), e("b2", "2024-01-01", "40.00"), e("b3", "2024-01-10", "10.00")],
        [e("k_late", "2024-01-10", "10.00"), e("k_early", "2024-01-01", "100.00")],
    )
    assert r["matches"] == [
        {"bank_id": "k_early", "book_ids": ["b1", "b2"]},
        {"bank_id": "k_late", "book_ids": ["b3"]},
    ]


def test_hidden_unmatched_sorted_by_date_id():
    r = reconcile(
        [e("b2", "2024-01-02", "10.00"), e("b1", "2024-01-01", "20.00")],
        [e("k2", "2024-01-03", "35.00"), e("k1", "2024-01-01", "45.00")],
    )
    assert r["unmatched_book"] == ["b1", "b2"]
    assert r["unmatched_bank"] == ["k1", "k2"]


def test_hidden_duplicate_book_id_raises():
    with pytest.raises(ValueError):
        reconcile([e("b1", "2024-01-01", "10.00"), e("b1", "2024-01-02", "10.00")], [])


def test_hidden_duplicate_bank_id_raises():
    with pytest.raises(ValueError):
        reconcile([], [e("k1", "2024-01-01", "10.00"), e("k1", "2024-01-01", "20.00")])


def test_hidden_bad_date_raises():
    with pytest.raises(ValueError):
        reconcile([e("b1", "2024-02-30", "10.00")], [])


def test_hidden_bad_amount_raises():
    with pytest.raises(ValueError):
        reconcile([e("b1", "2024-01-01", "10.005")], [])
