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


def declining_schedule(cost: str, salvage: str, life_years: int, factor: str = "2") -> list[dict]:
    cost_d = _money(cost, "cost")
    salvage_d = _money(salvage, "salvage")
    if not (cost_d > salvage_d >= 0):
        raise ValueError("must satisfy cost > salvage >= 0")
    if isinstance(life_years, bool) or not isinstance(life_years, int):
        raise ValueError("life_years must be an integer")
    if not 1 <= life_years <= 50:
        raise ValueError("life_years out of range")
    if not isinstance(factor, str):
        raise ValueError("factor must be a string")
    try:
        factor_d = Decimal(factor)
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid factor: {factor!r}") from None
    if not factor_d.is_finite():
        raise ValueError("factor must be finite")
    if not (Decimal("1") <= factor_d < Decimal("3")):
        raise ValueError("factor must satisfy 1 <= factor <= 3")
    with localcontext() as ctx:
        ctx.prec = 50
        rows = []
        opening = cost_d
        accumulated = Decimal("0.00")
        for year in range(1, life_years + 1):
            remaining_years = life_years - year + 1
            if year == life_years:
                amount = (opening - salvage_d).quantize(CENT)
            else:
                db = opening * (factor_d / Decimal(life_years))
                sl = (opening - salvage_d) / Decimal(remaining_years)
                raw = db if db >= sl else sl
                amount = raw.quantize(CENT, rounding=ROUND_HALF_UP)
                cap = opening - salvage_d
                if amount > cap:
                    amount = cap.quantize(CENT)
            accumulated = (accumulated + amount).quantize(CENT)
            book = (cost_d - accumulated).quantize(CENT)
            rows.append({"year": year, "amount": amount.quantize(CENT), "accumulated": accumulated, "book_value": book})
            opening = book
        return rows
