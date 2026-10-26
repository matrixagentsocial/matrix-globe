from decimal import Decimal

import pytest

from solution import process_payments


def _req(key, account="A", currency="EUR", amount="10.00", reference="r"):
    return {"key": key, "account": account, "currency": currency, "amount": amount, "reference": reference}


def test_hidden_currency_normalized_and_amount_quantized():
    result = process_payments([_req("k1", currency="usd", amount="10.5")])
    assert result["applied"][0]["currency"] == "USD"
    assert result["applied"][0]["amount"] == Decimal("10.50")
    assert result["balances"] == {"A:USD": Decimal("10.50")}


def test_hidden_separate_account_currency_balances():
    result = process_payments(
        [
            _req("k1", account="A", currency="EUR", amount="10.00"),
            _req("k2", account="A", currency="USD", amount="3.00"),
            _req("k3", account="B", currency="EUR", amount="1.25"),
            _req("k4", account="A", currency="EUR", amount="0.75"),
        ]
    )
    assert list(result["balances"].keys()) == ["A:EUR", "A:USD", "B:EUR"]
    assert result["balances"] == {"A:EUR": Decimal("10.75"), "A:USD": Decimal("3.00"), "B:EUR": Decimal("1.25")}
    assert result["applied"][-1]["balance_after"] == Decimal("10.75")


def test_hidden_duplicate_twice_counts_twice():
    result = process_payments([_req("k1"), _req("k1"), _req("k1")])
    assert result["duplicates"] == ["k1", "k1"]
    assert len(result["applied"]) == 1


def test_hidden_conflict_twice_and_compared_to_first():
    result = process_payments([_req("k1"), _req("k1", amount="11.00"), _req("k1", amount="11.00"), _req("k1")])
    assert len(result["conflicts"]) == 2
    # The last request matches the first again, so it is a duplicate, not a conflict.
    assert result["duplicates"] == ["k1"]
    assert result["balances"] == {"A:EUR": Decimal("10.00")}


def test_hidden_conflict_on_reference_only():
    result = process_payments([_req("k1", reference="a"), _req("k1", reference="b")])
    assert result["conflicts"] == [{"key": "k1", "reason": "payload differs from first occurrence"}]
    assert result["duplicates"] == []


def test_hidden_conflict_on_account_case():
    result = process_payments([_req("k1", account="A"), _req("k1", account="a")])
    assert len(result["conflicts"]) == 1


def test_hidden_conflict_account_creates_no_balance():
    result = process_payments([_req("k1", account="A"), _req("k1", account="B")])
    assert list(result["balances"].keys()) == ["A:EUR"]


def test_hidden_duplicate_order_multiple_keys():
    result = process_payments([_req("k1"), _req("k2", amount="2.00"), _req("k2", amount="2.00"), _req("k1")])
    assert result["duplicates"] == ["k2", "k1"]


def test_hidden_applied_order_and_running_balance():
    result = process_payments([_req("k2", amount="5.00"), _req("k1", amount="1.00"), _req("k3", currency="USD", amount="2.00")])
    assert [a["key"] for a in result["applied"]] == ["k2", "k1", "k3"]
    assert [a["balance_after"] for a in result["applied"]] == [Decimal("5.00"), Decimal("6.00"), Decimal("2.00")]


def test_hidden_invalid_amounts_raise():
    for bad in ["0.00", "-1.00", "10.005", "abc", "", "NaN", "Infinity"]:
        with pytest.raises(ValueError):
            process_payments([_req("k1", amount=bad)])


def test_hidden_invalid_repeat_still_raises():
    with pytest.raises(ValueError):
        process_payments([_req("k1"), _req("k1", amount="-5.00")])


def test_hidden_invalid_currency_raises():
    for bad in ["EU", "EURO", "E1R", "", 123]:
        with pytest.raises(ValueError):
            process_payments([_req("k1", currency=bad)])


def test_hidden_empty_key_or_account_raises():
    with pytest.raises(ValueError):
        process_payments([_req("")])
    with pytest.raises(ValueError):
        process_payments([_req("k1", account="")])


def test_hidden_missing_field_and_non_dict_raise():
    with pytest.raises(ValueError):
        process_payments([{"key": "k1", "account": "A", "currency": "EUR", "amount": "1.00"}])
    with pytest.raises(ValueError):
        process_payments(["not-a-dict"])


def test_hidden_non_string_reference_raises():
    with pytest.raises(ValueError):
        process_payments([_req("k1", reference=None)])


def test_hidden_empty_reference_allowed():
    result = process_payments([_req("k1", reference="")])
    assert len(result["applied"]) == 1


def test_hidden_non_list_raises():
    with pytest.raises(ValueError):
        process_payments("k1")


def test_hidden_same_key_different_keys_independent():
    # Same payload under a different key is a separate applied payment.
    result = process_payments([_req("k1"), _req("k2")])
    assert len(result["applied"]) == 2
    assert result["balances"] == {"A:EUR": Decimal("20.00")}
