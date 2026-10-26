from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENT = Decimal("0.01")
ALLOWED_RATES = {Decimal("0"), Decimal("4"), Decimal("10"), Decimal("21")}


def _q2(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


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


def _canonical(rate):
    return format(rate.normalize(), "f")


def vat_breakdown(lines: list[dict], mode: str) -> dict:
    if mode not in ("PER_LINE", "PER_INVOICE"):
        raise ValueError("mode must be PER_LINE or PER_INVOICE")
    if not isinstance(lines, list):
        raise ValueError("lines must be a list")
    parsed = []
    for line in lines:
        if not isinstance(line, dict):
            raise ValueError("each line must be a dict")
        for key in ("quantity", "unit_net", "vat_rate"):
            if key not in line:
                raise ValueError(f"line missing key: {key}")
        quantity = line["quantity"]
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise ValueError("quantity must be an integer")
        if quantity <= 0:
            raise ValueError("quantity must be > 0")
        unit_net = _parse_decimal(line["unit_net"], 4, "unit_net")
        if unit_net < 0:
            raise ValueError("unit_net must be >= 0")
        rate = _parse_decimal(line["vat_rate"], 4, "vat_rate")
        if rate not in ALLOWED_RATES:
            raise ValueError("vat_rate not allowed")
        parsed.append((quantity, unit_net, rate))

    groups = {}  # canonical -> [rate, net, vat]
    order = []
    if mode == "PER_LINE":
        for quantity, unit_net, rate in parsed:
            key = _canonical(rate)
            if key not in groups:
                groups[key] = [rate, Decimal("0"), Decimal("0")]
                order.append(key)
            line_net = quantity * unit_net
            line_vat = _q2(line_net * rate / Decimal(100))
            groups[key][1] += line_net
            groups[key][2] += line_vat
    else:
        exact = {}
        for quantity, unit_net, rate in parsed:
            key = _canonical(rate)
            if key not in exact:
                exact[key] = [rate, Decimal("0")]
                order.append(key)
            exact[key][1] += quantity * unit_net
        for key in order:
            rate, exact_net = exact[key]
            group_net = _q2(exact_net)
            group_vat = _q2(group_net * rate / Decimal(100))
            groups[key] = [rate, group_net, group_vat]

    by_rate = {}
    total_net = Decimal("0")
    total_vat = Decimal("0")
    for key in order:
        rate, net, vat = groups[key]
        net = _q2(net)
        vat = _q2(vat)
        by_rate[key] = {"net": net, "vat": vat, "gross": _q2(net + vat)}
        total_net += net
        total_vat += vat
    total_net = _q2(total_net)
    total_vat = _q2(total_vat)
    return {
        "net": total_net,
        "vat": total_vat,
        "gross": _q2(total_net + total_vat),
        "by_rate": by_rate,
    }
