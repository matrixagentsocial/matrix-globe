from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_DOWN,
    ROUND_FLOOR,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    ROUND_UP,
)

MINOR_UNITS = {
    "EUR": 2,
    "USD": 2,
    "GBP": 2,
    "CHF": 2,
    "AUD": 2,
    "CAD": 2,
    "JPY": 0,
    "KRW": 0,
    "VND": 0,
    "BHD": 3,
    "KWD": 3,
    "OMR": 3,
    "TND": 3,
    "JOD": 3,
}

MODES = {
    "HALF_UP": ROUND_HALF_UP,
    "HALF_EVEN": ROUND_HALF_EVEN,
    "DOWN": ROUND_FLOOR,
    "UP": ROUND_UP,
}


def round_money(amount: str, currency: str, mode: str = "HALF_UP") -> Decimal:
    if not isinstance(amount, str) or not isinstance(currency, str) or not isinstance(mode, str):
        raise ValueError("amount, currency and mode must be strings")
    try:
        value = Decimal(amount)
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid amount: {amount!r}") from None
    if not value.is_finite():
        raise ValueError("amount must be finite")
    code = currency.upper()
    if code not in MINOR_UNITS:
        raise ValueError(f"unsupported currency: {currency!r}")
    mode_key = mode.upper()
    if mode_key not in MODES:
        raise ValueError(f"unsupported rounding mode: {mode!r}")
    places = MINOR_UNITS[code]
    quantum = Decimal(1).scaleb(-places) if places else Decimal(1)
    return value.quantize(quantum, rounding=MODES[mode_key])
