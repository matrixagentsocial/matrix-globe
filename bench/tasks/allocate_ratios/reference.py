from decimal import Decimal, InvalidOperation

_CENT = Decimal("0.01")


def allocate_by_ratios(total: str, ratios: list) -> list[Decimal]:
    if not isinstance(total, str):
        raise ValueError("total must be a string")
    try:
        amount = Decimal(total)
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid total: {total!r}") from None
    if not amount.is_finite():
        raise ValueError("total must be finite")
    if amount != amount.quantize(_CENT):
        raise ValueError("total must have at most 2 decimal places")
    if not isinstance(ratios, list) or len(ratios) == 0:
        raise ValueError("ratios must be a non-empty list")
    weights = []
    for entry in ratios:
        if isinstance(entry, bool):
            raise ValueError("bool weights are not accepted")
        if isinstance(entry, int):
            weight = Decimal(entry)
        elif isinstance(entry, Decimal):
            weight = entry
        elif isinstance(entry, str):
            try:
                weight = Decimal(entry)
            except (InvalidOperation, ValueError):
                raise ValueError(f"invalid weight: {entry!r}") from None
        else:
            raise ValueError(f"invalid weight: {entry!r}")
        if not weight.is_finite():
            raise ValueError("weights must be finite")
        if weight < 0:
            raise ValueError("weights must be >= 0")
        weights.append(weight)
    total_weight = sum(weights, Decimal("0"))
    if total_weight <= 0:
        raise ValueError("at least one weight must be > 0")
    negative = amount < 0
    cents = int(abs(amount) * 100)
    floors, remainders = [], []
    for weight in weights:
        exact = Decimal(cents) * weight / total_weight
        floor_cents = int(exact)  # non-negative, truncation is floor
        floors.append(floor_cents)
        remainders.append(exact - floor_cents)
    remaining = cents - sum(floors)
    order = sorted((i for i, w in enumerate(weights) if w > 0), key=lambda i: (-remainders[i], -weights[i], i))
    for i in order[:remaining]:
        floors[i] += 1
    parts = []
    for floor_cents in floors:
        part = (Decimal(floor_cents) / Decimal(100)).quantize(_CENT)
        if negative and part != 0:
            part = -part
        parts.append(part)
    return parts
