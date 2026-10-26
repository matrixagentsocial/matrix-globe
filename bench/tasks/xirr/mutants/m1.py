from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation, localcontext

_CENT = Decimal("0.01")
_SIX_DP = Decimal("0.000001")


def _parse_date(text):
    if not isinstance(text, str):
        raise ValueError("date must be a string")
    parts = text.split("-")
    if (
        len(parts) != 3
        or len(parts[0]) != 4
        or len(parts[1]) != 2
        or len(parts[2]) != 2
        or not all(p.isdigit() for p in parts)
    ):
        raise ValueError(f"invalid date: {text!r}")
    try:
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError:
        raise ValueError(f"invalid date: {text!r}") from None


def _parse_amount(text):
    if not isinstance(text, str):
        raise ValueError("amount must be a string")
    try:
        amount = Decimal(text)
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid amount: {text!r}") from None
    if not amount.is_finite():
        raise ValueError("amount must be finite")
    return amount


def _combine(cashflows):
    if not isinstance(cashflows, list) or not cashflows:
        raise ValueError("cashflows must be a non-empty list")
    totals = {}
    for entry in cashflows:
        if not isinstance(entry, (list, tuple)) or len(entry) != 2:
            raise ValueError("each cashflow must be a (date, amount) pair")
        day = _parse_date(entry[0])
        amount = _parse_amount(entry[1])
        totals.setdefault(day, amount)
    if len(totals) < 2:
        raise ValueError("need at least 2 distinct dates")
    ordered = sorted(totals.items())
    amounts = [amount for _, amount in ordered]
    if not any(a > 0 for a in amounts) or not any(a < 0 for a in amounts):
        raise ValueError("need at least one positive and one negative amount")
    earliest = ordered[0][0]
    return [((day - earliest).days, amount) for day, amount in ordered]


def _parse_rate(rate_percent):
    if not isinstance(rate_percent, str):
        raise ValueError("rate_percent must be a string")
    try:
        rate = Decimal(rate_percent)
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid rate: {rate_percent!r}") from None
    if not rate.is_finite():
        raise ValueError("rate must be finite")
    if rate <= Decimal("-100"):
        raise ValueError("rate_percent must be > -100")
    return rate


def _npv_unquantized(rate_fraction, flows):
    # rate_fraction is r (not percent); flows are (days, amount) pairs.
    base = Decimal(1) + rate_fraction
    total = Decimal(0)
    for days, amount in flows:
        fraction = Decimal(days) / Decimal(365)
        total += amount / (base**fraction)
    return total


def _npv_and_derivative(rate_fraction, flows):
    base = Decimal(1) + rate_fraction
    total = Decimal(0)
    deriv = Decimal(0)
    for days, amount in flows:
        fraction = Decimal(days) / Decimal(365)
        discount = base**fraction
        total += amount / discount
        deriv -= amount * fraction / (base * discount)
    return total, deriv


def npv(rate_percent: str, cashflows: list[tuple[str, str]]) -> Decimal:
    flows = _combine(cashflows)
    rate = _parse_rate(rate_percent)
    with localcontext() as ctx:
        ctx.prec = 50
        value = _npv_unquantized(rate / Decimal(100), flows)
        return value.quantize(_CENT, rounding=ROUND_HALF_UP)


def xirr(cashflows: list[tuple[str, str]]) -> Decimal:
    flows = _combine(cashflows)
    with localcontext() as ctx:
        ctx.prec = 50
        lo = Decimal("-0.9999")  # -99.99%
        hi = Decimal("100")  # 10000%
        solution = None

        # Newton from 10%.
        rate = Decimal("0.10")
        for _ in range(100):
            value, deriv = _npv_and_derivative(rate, flows)
            if value == 0:
                solution = rate
                break
            if deriv == 0:
                break
            step = value / deriv
            new_rate = rate - step
            if new_rate <= lo or new_rate >= hi:
                break
            rate = new_rate
            if abs(step) < Decimal("1e-18") and abs(
                _npv_unquantized(rate, flows)
            ) < Decimal("1e-9"):
                solution = rate
                break

        # Bisection fallback on the bracket.
        if solution is None:
            f_lo = _npv_unquantized(lo, flows)
            f_hi = _npv_unquantized(hi, flows)
            if f_lo == 0:
                solution = lo
            elif f_hi == 0:
                solution = hi
            elif (f_lo > 0) == (f_hi > 0):
                raise ValueError("no sign change; cannot find XIRR")
            else:
                for _ in range(200):
                    mid = (lo + hi) / 2
                    f_mid = _npv_unquantized(mid, flows)
                    if f_mid == 0:
                        lo = hi = mid
                        break
                    if (f_mid > 0) == (f_lo > 0):
                        lo, f_lo = mid, f_mid
                    else:
                        hi = mid
                    if hi - lo < Decimal("1e-14"):
                        break
                solution = (lo + hi) / 2

        result = (solution * Decimal(100)).quantize(
            _SIX_DP, rounding=ROUND_HALF_UP
        )
        if result == 0:
            result = Decimal("0.000000")
        return result
