from decimal import Decimal, InvalidOperation

CENT = Decimal("0.01")
CONFLICT_REASON = "payload differs from first occurrence"


def _parse_amount(value):
    if not isinstance(value, str):
        raise ValueError("amount must be a string")
    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid amount: {value!r}") from None
    if not amount.is_finite() or amount <= 0:
        raise ValueError("amount must be finite and > 0")
    try:
        rounded = amount.quantize(CENT)
    except InvalidOperation:
        raise ValueError("amount must have at most 2 decimal places") from None
    if amount != rounded:
        raise ValueError("amount must have at most 2 decimal places")
    return amount.quantize(CENT)


def _validate(request):
    if not isinstance(request, dict):
        raise ValueError("each request must be a dict")
    for field in ("key", "account", "currency", "amount", "reference"):
        if field not in request:
            raise ValueError(f"missing field: {field}")
    key = request["key"]
    account = request["account"]
    currency = request["currency"]
    reference = request["reference"]
    if not isinstance(key, str) or not key.strip():
        raise ValueError("key must be a non-empty string")
    if not isinstance(account, str) or not account.strip():
        raise ValueError("account must be a non-empty string")
    if (
        not isinstance(currency, str)
        or len(currency) != 3
        or not currency.isalpha()
        or not currency.isascii()
    ):
        raise ValueError("currency must be exactly 3 letters")
    if not isinstance(reference, str):
        raise ValueError("reference must be a string")
    amount = _parse_amount(request["amount"])
    return key, account, currency.upper(), amount, reference


def process_payments(requests):
    if not isinstance(requests, list):
        raise ValueError("requests must be a list")
    seen = {}
    applied = []
    duplicates = []
    conflicts = []
    balances_map = {}
    for request in requests:
        key, account, currency, amount, reference = _validate(request)
        payload = (account, currency, amount)
        if key in seen:
            if seen[key] == payload:
                duplicates.append(key)
            else:
                conflicts.append({"key": key, "reason": CONFLICT_REASON})
            continue
        seen[key] = payload
        balance_key = (account, currency)
        new_balance = (balances_map.get(balance_key, Decimal("0.00")) + amount).quantize(CENT)
        balances_map[balance_key] = new_balance
        applied.append(
            {
                "key": key,
                "account": account,
                "currency": currency,
                "amount": amount,
                "balance_after": new_balance,
            }
        )
    balances = {
        f"{account}:{currency}": balances_map[(account, currency)]
        for account, currency in sorted(balances_map, key=lambda p: f"{p[0]}:{p[1]}")
    }
    return {
        "applied": applied,
        "duplicates": duplicates,
        "conflicts": conflicts,
        "balances": balances,
    }
