from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENT = Decimal("0.01")
BRACKETS = [
    (Decimal("0"), Decimal("12450"), 19),
    (Decimal("12450"), Decimal("20200"), 24),
    (Decimal("20200"), Decimal("35200"), 30),
    (Decimal("35200"), Decimal("60000"), 37),
    (Decimal("60000"), Decimal("300000"), 45),
    (Decimal("300000"), None, 47),
]


def _parse_income(income):
    if not isinstance(income, str):
        raise ValueError("income must be a string")
    try:
        amount = Decimal(income)
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid income: {income!r}") from None
    if not amount.is_finite():
        raise ValueError("income must be finite")
    if amount < 0:
        raise ValueError("income must be >= 0")
    try:
        rounded = amount.quantize(CENT)
    except InvalidOperation:
        raise ValueError("income must have at most 2 decimal places") from None
    if amount != rounded:
        raise ValueError("income must have at most 2 decimal places")
    return amount.quantize(CENT)


def tax_breakdown(income):
    amount = _parse_income(income)
    rows = []
    for lower, upper, rate in BRACKETS:
        if amount <= lower:
            continue
        top = amount if upper is None else min(amount, upper)
        taxable = (top - lower).quantize(CENT)
        if taxable <= 0:
            continue
        tax = taxable * Decimal(rate) / Decimal(100)
        rows.append(
            {
                "from": lower.quantize(CENT),
                "to": None if upper is None else upper.quantize(CENT),
                "rate_percent": rate,
                "taxable": taxable,
                "tax": tax,
            }
        )
    return rows


def income_tax(income):
    total = sum((row["tax"] for row in tax_breakdown(income)), Decimal("0.00"))
    return total.quantize(CENT)


def effective_rate_percent(income):
    amount = _parse_income(income)
    if amount == 0:
        return Decimal("0.0000")
    rate = (income_tax(income) / amount * Decimal(100)).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP
    )
    return rate
