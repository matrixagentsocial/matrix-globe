from datetime import date, datetime
from decimal import Decimal, InvalidOperation

BUCKETS = ["current", "1-30", "31-60", "61-90", "90+"]
CENT = Decimal("0.01")


def _to_date(value, field: str) -> date:
    if isinstance(value, datetime):
        raise ValueError(f"{field} must be a date or ISO string")
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise ValueError(f"invalid {field}: {value!r}") from None
    raise ValueError(f"{field} must be a date or ISO string")


def _to_amount(value) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError("amount must be a decimal string, Decimal or int")
    if isinstance(value, Decimal):
        amount = value
    elif isinstance(value, int):
        amount = Decimal(value)
    elif isinstance(value, str):
        try:
            amount = Decimal(value)
        except (InvalidOperation, ValueError):
            raise ValueError(f"invalid amount: {value!r}") from None
    else:
        raise ValueError("amount must be a decimal string, Decimal or int")
    if not amount.is_finite():
        raise ValueError("amount must be finite")
    return amount


def _bucket_for(days_overdue: int) -> str:
    if days_overdue <= 0:
        return "current"
    if days_overdue <= 30:
        return "1-30"
    if days_overdue <= 59:
        return "31-60"
    if days_overdue <= 90:
        return "61-90"
    return "90+"


def aging_buckets(invoices: list[dict], as_of) -> dict[str, Decimal]:
    as_of_date = _to_date(as_of, "as_of")
    totals = {name: Decimal("0") for name in BUCKETS}
    for invoice in invoices:
        if not isinstance(invoice, dict):
            raise ValueError("each invoice must be a dict")
        if "due_date" not in invoice or "amount" not in invoice:
            raise ValueError("invoice must have due_date and amount")
        due = _to_date(invoice["due_date"], "due_date")
        amount = _to_amount(invoice["amount"])
        days = (as_of_date - due).days
        totals[_bucket_for(days)] += amount
    return {name: totals[name].quantize(CENT) for name in BUCKETS}
