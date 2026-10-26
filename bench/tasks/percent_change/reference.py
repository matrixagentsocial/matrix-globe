from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

_CENT = Decimal("0.01")


def _parse(value):
    if not isinstance(value, str):
        raise ValueError("input must be a string")
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid decimal: {value!r}") from None
    if not number.is_finite():
        raise ValueError("input must be finite")
    return number


def percent_change(old: str, new: str) -> Decimal | None:
    old_d, new_d = _parse(old), _parse(new)
    if old_d == 0:
        return Decimal("0.00") if new_d == 0 else None
    change = (new_d - old_d) / abs(old_d) * 100
    return change.quantize(_CENT, rounding=ROUND_HALF_UP)


def apply_percent_change(old: str, percent: str) -> Decimal:
    old_d, pct = _parse(old), _parse(percent)
    result = old_d * (1 + pct / 100)
    return result.quantize(_CENT, rounding=ROUND_HALF_UP)
