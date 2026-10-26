from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENT = Decimal("0.01")
FOUR = Decimal("0.0001")


def _q2(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _q4(value):
    return value.quantize(FOUR, rounding=ROUND_HALF_UP)


def _parse_decimal(value, max_places, name):
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid {name}: {value!r}") from None
    if not amount.is_finite():
        raise ValueError(f"{name} must be finite")
    quantum = Decimal(1).scaleb(-max_places)
    try:
        quantized = amount.quantize(quantum)
    except InvalidOperation:
        raise ValueError(f"invalid {name}: {value!r}") from None
    if amount != quantized:
        raise ValueError(f"{name} has too many decimal places")
    return amount


def _parse_date(value):
    if not isinstance(value, str):
        raise ValueError("date must be a string")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"invalid date: {value!r}") from None
    if parsed.strftime("%Y-%m-%d") != value:
        raise ValueError(f"invalid date: {value!r}")
    return value


def fifo_report(trades: list[dict]) -> dict:
    if not isinstance(trades, list):
        raise ValueError("trades must be a list")
    lots = []  # each [remaining_qty:int, remaining_total_cost:Decimal]
    sales = []
    total_realized = Decimal("0")

    for trade in trades:
        if not isinstance(trade, dict):
            raise ValueError("each trade must be a dict")
        for key in ("date", "side", "quantity", "price"):
            if key not in trade:
                raise ValueError(f"trade missing key: {key}")
        date = _parse_date(trade["date"])
        side = trade["side"]
        if side not in ("BUY", "SELL"):
            raise ValueError("side must be BUY or SELL")
        quantity = trade["quantity"]
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise ValueError("quantity must be an integer")
        if quantity <= 0:
            raise ValueError("quantity must be > 0")
        price = _parse_decimal(trade["price"], 4, "price")
        if price <= 0:
            raise ValueError("price must be > 0")
        fee = _parse_decimal(trade.get("fee", "0.00"), 2, "fee")
        if fee < 0:
            raise ValueError("fee must be >= 0")

        if side == "BUY":
            lots.append([quantity, quantity * price])
        else:
            inventory = sum(lot[0] for lot in lots)
            if quantity > inventory:
                raise ValueError("insufficient inventory")
            proceeds_exact = quantity * price - fee
            cost_exact = Decimal("0")
            to_sell = quantity
            while to_sell > 0:
                lot_qty, lot_cost = lots[0]
                taken = min(lot_qty, to_sell)
                consumed = lot_cost * Decimal(taken) / Decimal(lot_qty)
                cost_exact += consumed
                if taken == lot_qty:
                    lots.pop(0)
                else:
                    lots[0] = [lot_qty - taken, lot_cost - consumed]
                to_sell -= taken
            realized = _q2(proceeds_exact - cost_exact)
            sales.append(
                {
                    "date": date,
                    "quantity": quantity,
                    "proceeds": _q2(proceeds_exact),
                    "cost": _q2(cost_exact),
                    "realized": realized,
                }
            )
            total_realized += realized

    remaining = []
    inventory_quantity = 0
    for lot_qty, lot_cost in lots:
        if lot_qty > 0:
            remaining.append(
                {
                    "quantity": lot_qty,
                    "unit_cost": _q4(lot_cost / Decimal(lot_qty)),
                    "total_cost": _q2(lot_cost),
                }
            )
            inventory_quantity += lot_qty
    return {
        "sales": sales,
        "total_realized": _q2(total_realized),
        "remaining": remaining,
        "inventory_quantity": inventory_quantity,
    }
