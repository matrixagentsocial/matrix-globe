from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext

Q6 = Decimal("0.000001")
_FREQ = {
    "annually": 1,
    "semiannually": 2,
    "quarterly": 4,
    "monthly": 12,
    "weekly": 52,
    "daily": 365,
    "continuous": None,
}


def _parse_percent(value, name):
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid {name}: {value!r}") from None
    if not parsed.is_finite():
        raise ValueError(f"{name} must be finite")
    if parsed < Decimal("-100"):
        raise ValueError(f"{name} must be > -100")
    return parsed


def _parse_frequency(frequency):
    if not isinstance(frequency, str):
        raise ValueError("frequency must be a string")
    key = frequency.strip().lower()
    if key not in _FREQ:
        raise ValueError(f"unknown frequency: {frequency!r}")
    return _FREQ[key]


def apr_to_apy(apr_percent: str, frequency: str) -> Decimal:
    apr = _parse_percent(apr_percent, "apr_percent")
    m = _parse_frequency(frequency)
    with localcontext() as ctx:
        ctx.prec = 50
        r = apr / Decimal(100)
        if m is None:
            result = (r.exp() - 1) * 100
        else:
            result = ((Decimal(1) + r / Decimal(m)) ** m - 1) * 100
        return result.quantize(Q6, rounding=ROUND_HALF_UP)


def apy_to_apr(apy_percent: str, frequency: str) -> Decimal:
    apy = _parse_percent(apy_percent, "apy_percent")
    m = _parse_frequency(frequency)
    with localcontext() as ctx:
        ctx.prec = 50
        y = apy / Decimal(100)
        if m is None:
            result = (Decimal(1) + y).ln() * 100
        else:
            # m * ((1+y)**(1/m) - 1) * 100 via exp/ln
            result = Decimal(m) * (((Decimal(1) + y).ln() / Decimal(m)).exp() - 1) * 100
        return result.quantize(Q6, rounding=ROUND_HALF_UP)
