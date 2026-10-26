from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext

CENT = Decimal("0.01")


def _money(value, name):
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
    return amount.quantize(CENT)


def _int_range(value, name, lo, hi):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if not lo <= value <= hi:
        raise ValueError(f"{name} out of range")
    return value


def straight_line_schedule(cost: str, salvage: str, life_years: int, placed_year: int, placed_month: int) -> list[dict]:
    cost_d = _money(cost, "cost")
    salvage_d = _money(salvage, "salvage")
    if cost_d <= 0:
        raise ValueError("cost must be > 0")
    if salvage_d < 0 or salvage_d >= cost_d:
        raise ValueError("salvage must satisfy 0 <= salvage < cost")
    life = _int_range(life_years, "life_years", 1, 100)
    year = _int_range(placed_year, "placed_year", 1900, 2200)
    month = _int_range(placed_month, "placed_month", 1, 12)
    with localcontext() as ctx:
        ctx.prec = 50
        base = cost_d - salvage_d
        full = base / Decimal(life)
        fraction = (Decimal(12 - month) + Decimal("0.5")) / Decimal(12)
        rows = []
        accumulated = Decimal("0.00")
        remaining = base
        current_year = year
        first = True
        while remaining > 0:
            raw = full * fraction if first else full
            quantized = raw.quantize(CENT, rounding=ROUND_HALF_UP)
            if quantized >= remaining or quantized == 0:
                amount = remaining.quantize(CENT)
            else:
                amount = quantized
            accumulated = (accumulated + amount).quantize(CENT)
            remaining = base - accumulated
            book = (cost_d - accumulated).quantize(CENT)
            rows.append({"year": current_year, "amount": amount.quantize(CENT), "accumulated": accumulated, "book_value": book})
            current_year += 1
            first = False
        return rows
