from decimal import Decimal, InvalidOperation


def split_installments(total: str, n: int) -> list[Decimal]:
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError("n must be an integer")
    if n < 1:
        raise ValueError("n must be >= 1")
    if not isinstance(total, str):
        raise ValueError("total must be a string")
    try:
        amount = Decimal(total)
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid total: {total!r}") from None
    if not amount.is_finite():
        raise ValueError("total must be finite")
    if amount < 0:
        raise ValueError("total must be >= 0")
    if amount != amount.quantize(Decimal("0.01")):
        raise ValueError("total must have at most 2 decimal places")
    cents = int(amount * 100)
    base, remainder = divmod(cents, n)
    parts = []
    for i in range(n):
        part_cents = base + (1 if i < remainder else 0)
        parts.append((Decimal(part_cents) / Decimal(100)).quantize(Decimal("0.01")))
    return parts
