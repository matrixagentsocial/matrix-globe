from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext

_MINOR = {"EUR": 2, "USD": 2, "GBP": 2, "CHF": 2, "CAD": 2, "AUD": 2, "JPY": 0, "KRW": 0}


def _code(value):
    if not isinstance(value, str):
        raise ValueError("currency code must be a string")
    code = value.upper()
    if len(code) != 3 or not code.isalpha() or not code.isascii():
        raise ValueError(f"invalid currency code: {value!r}")
    return code


def _rates(rates):
    if not isinstance(rates, dict):
        raise ValueError("rates must be a dict")
    out = {}
    for key, value in rates.items():
        code = _code(key)
        if isinstance(value, bool) or not isinstance(value, (str, int, Decimal, float)):
            raise ValueError(f"invalid rate for {code}")
        try:
            rate = value if isinstance(value, Decimal) else Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValueError(f"invalid rate for {code}") from None
        if not rate.is_finite() or rate <= 0:
            raise ValueError(f"rate for {code} must be finite and > 0")
        out[code] = rate
    if "EUR" in out and out["EUR"] != Decimal("1"):
        raise ValueError("EUR rate must be 1")
    out.setdefault("EUR", Decimal("1"))
    return out


def _amount(value):
    if not isinstance(value, str):
        raise ValueError("amount must be a string")
    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid amount: {value!r}") from None
    if not amount.is_finite():
        raise ValueError("amount must be finite")
    return amount


def _quantum(code):
    units = _MINOR.get(code, 2)
    return Decimal("1") if units == 0 else Decimal("1").scaleb(-units)


def convert_fx(amount: str, from_currency: str, to_currency: str, rates: dict) -> Decimal:
    amt = _amount(amount)
    src = _code(from_currency)
    dst = _code(to_currency)
    with localcontext() as ctx:
        ctx.prec = 50
        if src == dst:
            return amt.quantize(_quantum(dst), rounding=ROUND_HALF_UP)
        table = _rates(rates)
        if src not in table or dst not in table:
            raise ValueError("unknown currency")
        result = (amt / table[src]) * table[dst]
        return result.quantize(_quantum(dst), rounding=ROUND_HALF_UP)


def cross_rate(from_currency: str, to_currency: str, rates: dict) -> Decimal:
    src = _code(from_currency)
    dst = _code(to_currency)
    table = _rates(rates)
    if src not in table or dst not in table:
        raise ValueError("unknown currency")
    with localcontext() as ctx:
        ctx.prec = 50
        return (table[dst] / table[src]).quantize(Decimal("0.0000000001"), rounding=ROUND_HALF_UP)
