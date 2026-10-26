import pytest

from solution import reconcile


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
