from decimal import Decimal

import pytest

from solution import find_duplicate_payments


def _p(pid, d, vendor, amount="100.00", currency="EUR"):
    return {"id": pid, "date": d, "vendor": vendor, "amount": amount, "currency": currency}


def test_hidden_legal_suffix_punct_case_variants():
    result = find_duplicate_payments([_p("p1", "2024-01-01", "ACME, S.L."), _p("p2", "2024-01-03", "acme sl"), _p("p3", "2024-01-04", "Acme S.L.U.")])
    assert result == [{"payment_ids": ["p1", "p2", "p3"], "vendor": "ACME", "amount": Decimal("100.00"), "currency": "EUR"}]


def test_hidden_chain_transitive_group():
    result = find_duplicate_payments([_p("a", "2024-01-01", "Acme"), _p("b", "2024-01-07", "Acme"), _p("c", "2024-01-13", "Acme")], window_days=7)
    assert len(result) == 1
    assert result[0]["payment_ids"] == ["a", "b", "c"]


def test_hidden_same_amount_different_vendor_no():
    assert find_duplicate_payments([_p("p1", "2024-01-01", "Acme"), _p("p2", "2024-01-01", "Other")]) == []


def test_hidden_refund_sign_not_duplicate():
    assert find_duplicate_payments([_p("p1", "2024-01-01", "Acme", "50.00"), _p("p2", "2024-01-01", "Acme", "-50.00")]) == []


def test_hidden_window_exactly_n_yes():
    result = find_duplicate_payments([_p("p1", "2024-01-01", "Acme"), _p("p2", "2024-01-11", "Acme")], window_days=10)
    assert len(result) == 1


def test_hidden_window_n_plus_one_no():
    assert find_duplicate_payments([_p("p1", "2024-01-01", "Acme"), _p("p2", "2024-01-12", "Acme")], window_days=10) == []


def test_hidden_different_currency_no():
    assert find_duplicate_payments([_p("p1", "2024-01-01", "Acme", currency="EUR"), _p("p2", "2024-01-01", "Acme", currency="USD")]) == []


def test_hidden_currency_case_normalized():
    result = find_duplicate_payments([_p("p1", "2024-01-01", "Acme", currency="eur"), _p("p2", "2024-01-01", "Acme", currency=" EUR ")])
    assert len(result) == 1 and result[0]["currency"] == "EUR"


def test_hidden_ids_sorted_by_date_then_id():
    result = find_duplicate_payments([_p("z", "2024-01-02", "Acme"), _p("a", "2024-01-02", "Acme"), _p("m", "2024-01-01", "Acme")])
    assert result[0]["payment_ids"] == ["m", "a", "z"]


def test_hidden_groups_sorted_by_earliest_date():
    payments = [_p("b1", "2024-02-01", "Beta", "20.00"), _p("b2", "2024-02-02", "Beta", "20.00"), _p("a1", "2024-01-01", "Acme"), _p("a2", "2024-01-02", "Acme")]
    result = find_duplicate_payments(payments)
    assert [g["vendor"] for g in result] == ["ACME", "BETA"]


def test_hidden_bad_date_raises():
    with pytest.raises(ValueError):
        find_duplicate_payments([_p("p1", "2024-02-30", "Acme")])


def test_hidden_bad_amount_raises():
    with pytest.raises(ValueError):
        find_duplicate_payments([_p("p1", "2024-01-01", "Acme", "abc")])


def test_hidden_window_too_large_raises():
    with pytest.raises(ValueError):
        find_duplicate_payments([], window_days=366)


def test_hidden_negative_window_raises():
    with pytest.raises(ValueError):
        find_duplicate_payments([], window_days=-1)


def test_hidden_empty_normalized_vendor_raises():
    with pytest.raises(ValueError):
        find_duplicate_payments([_p("p1", "2024-01-01", "LTD")])


def test_hidden_repeated_legal_suffix_dropped():
    result = find_duplicate_payments([_p("p1", "2024-01-01", "Acme Limited Ltd"), _p("p2", "2024-01-01", "ACME")])
    assert len(result) == 1 and result[0]["vendor"] == "ACME"


def test_hidden_leading_legal_token_kept():
    # "SA Holdings" -> "SA HOLDINGS" (leading SA not dropped), so not a duplicate of "Holdings".
    assert find_duplicate_payments([_p("p1", "2024-01-01", "SA Holdings"), _p("p2", "2024-01-01", "Holdings")]) == []


def test_hidden_amount_three_dp_raises():
    with pytest.raises(ValueError):
        find_duplicate_payments([_p("p1", "2024-01-01", "Acme", "10.005")])
