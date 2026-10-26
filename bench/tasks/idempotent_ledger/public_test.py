from decimal import Decimal

from solution import process_payments


def _req(key, account="A", currency="EUR", amount="10.00", reference="r"):
    return {"key": key, "account": account, "currency": currency, "amount": amount, "reference": reference}


def test_public_single_payment_applied():
    result = process_payments([_req("k1")])
    assert result["applied"] == [
        {"key": "k1", "account": "A", "currency": "EUR", "amount": Decimal("10.00"), "balance_after": Decimal("10.00")}
    ]
    assert result["balances"] == {"A:EUR": Decimal("10.00")}


def test_public_worked_example_duplicate():
    result = process_payments(
        [
            _req("k1", currency="eur", amount="10.00", reference="r1"),
            _req("k2", amount="5.50", reference=""),
            _req("k1", amount="10.0", reference="r1"),
        ]
    )
    assert [a["balance_after"] for a in result["applied"]] == [Decimal("10.00"), Decimal("15.50")]
    assert result["duplicates"] == ["k1"]
    assert result["conflicts"] == []
    assert result["balances"] == {"A:EUR": Decimal("15.50")}


def test_public_conflict_not_applied():
    result = process_payments([_req("k1"), _req("k1", amount="11.00")])
    assert len(result["applied"]) == 1
    assert result["conflicts"] == [{"key": "k1", "reason": "payload differs from first occurrence"}]
    assert result["balances"] == {"A:EUR": Decimal("10.00")}


def test_public_empty_list():
    assert process_payments([]) == {"applied": [], "duplicates": [], "conflicts": [], "balances": {}}
