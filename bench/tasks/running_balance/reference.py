import re
from datetime import date
from decimal import Decimal, InvalidOperation

CENT = Decimal("0.01")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _money(value, name, allow_zero_amount=True):
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid {name}: {value!r}") from None
    if not amount.is_finite():
        raise ValueError(f"{name} must be finite")
    if amount != amount.quantize(CENT):
        raise ValueError(f"{name} must have at most 2 decimal places")
    quantized = amount.quantize(CENT)
    # Normalize -0.00 to 0.00
    if quantized == 0:
        quantized = Decimal("0.00")
    return quantized


def _date(value, name):
    if not isinstance(value, str) or not _DATE_RE.match(value):
        raise ValueError(f"{name} must be YYYY-MM-DD")
    try:
        date(int(value[0:4]), int(value[5:7]), int(value[8:10]))
    except ValueError:
        raise ValueError(f"invalid {name}: {value!r}") from None
    return value


def running_balance(transactions: list[dict], opening_balance: str) -> list[dict]:
    opening = _money(opening_balance, "opening_balance")
    if not isinstance(transactions, list):
        raise ValueError("transactions must be a list")
    seen = set()
    normalized = []
    for tx in transactions:
        if not isinstance(tx, dict):
            raise ValueError("each transaction must be a dict")
        for key in ("id", "value_date", "booking_date", "amount"):
            if key not in tx:
                raise ValueError(f"missing key: {key}")
        tx_id = tx["id"]
        if not isinstance(tx_id, str) or tx_id == "":
            raise ValueError("id must be a non-empty string")
        if tx_id in seen:
            raise ValueError(f"duplicate id: {tx_id!r}")
        seen.add(tx_id)
        value_date = _date(tx["value_date"], "value_date")
        booking_date = _date(tx["booking_date"], "booking_date")
        amount = _money(tx["amount"], "amount")
        normalized.append({"id": tx_id, "value_date": value_date, "booking_date": booking_date, "amount": amount})
    normalized.sort(key=lambda r: (r["value_date"], r["booking_date"], r["id"]))
    rows = []
    balance = opening
    for r in normalized:
        balance = (balance + r["amount"]).quantize(CENT)
        if balance == 0:
            balance = Decimal("0.00")
        rows.append({"id": r["id"], "value_date": r["value_date"], "booking_date": r["booking_date"], "amount": r["amount"], "balance": balance})
    return rows


def closing_balance(transactions: list[dict], opening_balance: str) -> Decimal:
    rows = running_balance(transactions, opening_balance)
    if not rows:
        return _money(opening_balance, "opening_balance")
    return rows[-1]["balance"]
