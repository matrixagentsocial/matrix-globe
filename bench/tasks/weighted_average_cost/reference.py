from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext

_CENT = Decimal("0.01")
_TYPES = {"PURCHASE", "SALE", "CUSTOMER_RETURN", "PURCHASE_RETURN"}


def _d2(value):
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


def process_inventory(movements: list[dict]) -> dict:
    if not isinstance(movements, list):
        raise ValueError("movements must be a list")
    qty = 0
    value = Decimal("0.00")
    total_cogs = Decimal("0.00")
    total_pr = Decimal("0.00")
    with localcontext() as ctx:
        ctx.prec = 50
        for mv in movements:
            if not isinstance(mv, dict):
                raise ValueError("movement must be a dict")
            mtype = mv.get("type")
            if mtype not in _TYPES:
                raise ValueError(f"invalid movement type: {mtype!r}")
            quantity = mv.get("quantity")
            if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
                raise ValueError("quantity must be a positive int")
            if mtype == "PURCHASE":
                if "unit_cost" not in mv:
                    raise ValueError("unit_cost required for PURCHASE")
                raw = mv["unit_cost"]
                if not isinstance(raw, str):
                    raise ValueError("unit_cost must be a string")
                try:
                    cost = Decimal(raw)
                except (InvalidOperation, ValueError):
                    raise ValueError(f"invalid unit_cost: {raw!r}") from None
                if not cost.is_finite() or cost < 0:
                    raise ValueError("unit_cost must be finite and >= 0")
                value = _d2(value + _d2(cost * quantity))
                qty += quantity
            elif mtype == "SALE":
                if quantity > qty:
                    raise ValueError("sale exceeds quantity on hand")
                avg = value / qty
                cogs = _d2(avg * quantity)
                value = _d2(value - cogs)
                qty -= quantity
                total_cogs = _d2(total_cogs + cogs)
            elif mtype == "CUSTOMER_RETURN":
                if qty == 0:
                    raise ValueError("no current average cost for customer return")
                avg = value / qty
                value = _d2(value + _d2(avg * quantity))
                qty += quantity
            else:  # PURCHASE_RETURN
                if quantity > qty:
                    raise ValueError("purchase return exceeds quantity on hand")
                avg = value / qty
                removed = _d2(avg * quantity)
                value = _d2(value - removed)
                qty -= quantity
                total_pr = _d2(total_pr + removed)
        avg_out = Decimal("0.0000") if qty == 0 else (value / qty).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return {
        "quantity_on_hand": qty,
        "inventory_value": _d2(value),
        "average_cost": avg_out,
        "total_cogs": _d2(total_cogs),
        "total_purchase_returns": _d2(total_pr),
    }
