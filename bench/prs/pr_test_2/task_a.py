from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

_CENT = Decimal("0.01")


def _money(value):
    if not isinstance(value, str):
        raise ValueError("money must be a string")
    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid money: {value!r}") from None
    if not amount.is_finite():
        raise ValueError("money must be finite")
    if amount != amount.quantize(_CENT):
        raise ValueError("money must have at most 2 decimal places")
    return amount.quantize(_CENT)


def _validated(lines):
    if not isinstance(lines, list):
        raise ValueError("lines must be a list")
    parsed = []
    for entry in lines:
        if not isinstance(entry, dict):
            raise ValueError("each line must be a dict")
        for key in ("name", "kind", "budget", "actual"):
            if key not in entry:
                raise ValueError(f"missing key: {key}")
        if not isinstance(entry["name"], str):
            raise ValueError("name must be a string")
        if entry["kind"] not in ("revenue", "cost"):
            raise ValueError("kind must be revenue or cost")
        parsed.append((entry["name"], entry["kind"], _money(entry["budget"]), _money(entry["actual"])))
    return parsed


def variance_report(lines: list[dict]) -> list[dict]:
    report = []
    for name, kind, budget, actual in _validated(lines):
        variance = (actual - budget).quantize(_CENT)
        if variance == 0:
            favourable, status = False, "on_budget"
        elif (kind == "revenue" and variance > 0) or (kind == "cost" and variance < 0):
            favourable, status = True, "favourable"
        else:
            favourable, status = False, "unfavourable"
        if budget == 0:
            percent = None
        else:
            percent = (variance / budget * 100).quantize(_CENT, rounding=ROUND_HALF_UP)
        report.append({"name": name, "kind": kind, "budget": budget, "actual": actual, "variance": variance, "variance_percent": percent, "favourable": favourable, "status": status})
    return report


def variance_summary(lines: list[dict]) -> dict:
    report = variance_report(lines)
    def total(kind, field):
        return sum((row[field] for row in report if row["kind"] == kind), Decimal("0.00")).quantize(_CENT)
    total_budget_revenue, total_actual_revenue = total("revenue", "budget"), total("revenue", "actual")
    total_budget_cost, total_actual_cost = total("cost", "budget"), total("cost", "actual")
    net_budget = (total_budget_revenue - total_budget_cost).quantize(_CENT)
    net_actual = (total_actual_revenue - total_actual_cost).quantize(_CENT)
    return {
        "total_budget_revenue": total_budget_revenue,
        "total_actual_revenue": total_actual_revenue,
        "total_budget_cost": total_budget_cost,
        "total_actual_cost": total_actual_cost,
        "net_budget": net_budget,
        "net_actual": net_actual,
        "net_variance": (net_actual - net_budget).quantize(_CENT),
        "favourable_count": sum(1 for r in report if r["status"] == "favourable"),
        "unfavourable_count": sum(1 for r in report if r["status"] == "unfavourable"),
        "on_budget_count": sum(1 for r in report if r["status"] == "on_budget"),
    }
