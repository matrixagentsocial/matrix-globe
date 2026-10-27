from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENT = Decimal("0.01")


def _parse_date(value, field):
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"invalid {field}: {value!r}") from None
    if parsed.isoformat() != value:
        raise ValueError(f"invalid {field}: {value!r}")
    return parsed


def _parse_price(value):
    if not isinstance(value, str):
        raise ValueError("monthly_price must be a string")
    try:
        price = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid monthly_price: {value!r}") from None
    if not price.is_finite() or price < 0:
        raise ValueError("monthly_price must be finite and >= 0")
    try:
        rounded = price.quantize(CENT)
    except InvalidOperation:
        raise ValueError("monthly_price must have at most 2 decimal places") from None
    if price != rounded:
        raise ValueError("monthly_price must have at most 2 decimal places")
    return price.quantize(CENT)


def prorate_period(period_start, period_end, changes):
    start = _parse_date(period_start, "period_start")
    end = _parse_date(period_end, "period_end")
    if end <= start:
        raise ValueError("period_end must be after period_start")
    if not isinstance(changes, list) or not changes:
        raise ValueError("changes must be a non-empty list")
    parsed = []
    seen_dates = set()
    for entry in changes:
        if not isinstance(entry, dict) or "date" not in entry or "monthly_price" not in entry:
            raise ValueError("each change must have date and monthly_price")
        eff = _parse_date(entry["date"], "change date")
        price = _parse_price(entry["monthly_price"])
        if eff in seen_dates:
            raise ValueError("duplicate change date")
        seen_dates.add(eff)
        parsed.append((eff, price))
    parsed.sort(key=lambda item: item[0])
    if parsed[0][0] > start:
        raise ValueError("no change effective on or before period_start")
    current_price = None
    boundaries = []
    for eff, price in parsed:
        if eff <= start:
            current_price = price
        elif eff < end:
            boundaries.append((eff, price))
    period_days = (end - start).days
    points = [start] + [d for d, _ in boundaries] + [end]
    prices = [current_price] + [p for _, p in boundaries]
    raw = []
    for i in range(len(points) - 1):
        seg_start, seg_end = points[i], points[i + 1]
        days = (seg_end - seg_start).days
        if days <= 0:
            continue
        raw.append([seg_start, seg_end, days, prices[i]])
    merged = []
    for seg in raw:
        if merged and merged[-1][3] == seg[3]:
            merged[-1][1] = seg[1]
            merged[-1][2] += seg[2]
        else:
            merged.append(list(seg))
    segments = []
    total = Decimal("0.00")
    for seg_start, seg_end, days, price in merged:
        amount = (price * Decimal(days) / Decimal(period_days)).quantize(
            CENT, rounding=ROUND_HALF_UP
        )
        total += amount
        segments.append(
            {
                "from": seg_start.isoformat(),
                "to": seg_end.isoformat(),
                "days": days,
                "monthly_price": price.quantize(CENT),
                "amount": amount,
            }
        )
    return {"period_days": period_days, "segments": segments, "total": total.quantize(CENT)}
