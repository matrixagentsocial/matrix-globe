import calendar
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext

CENT = Decimal("0.01")


def _parse_decimal(value, name):
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid {name}: {value!r}") from None
    if not parsed.is_finite():
        raise ValueError(f"{name} must be finite")
    return parsed


def _parse_principal(value):
    amount = _parse_decimal(value, "principal")
    if amount <= 0:
        raise ValueError("principal must be > 0")
    try:
        quantized = amount.quantize(CENT)
    except InvalidOperation:
        raise ValueError("principal must have at most 2 decimal places") from None
    if amount != quantized:
        raise ValueError("principal must have at most 2 decimal places")
    return quantized


def _parse_rate(value):
    rate = _parse_decimal(value, "annual_rate_percent")
    if rate < 0 or rate > 100:
        raise ValueError("annual_rate_percent must be between 0 and 100")
    return rate


def _parse_start_date(value):
    if not isinstance(value, str):
        raise ValueError("start_date must be a string")
    if len(value) != 10 or value[4] != "-" or value[7] != "-":
        raise ValueError(f"invalid start_date: {value!r}")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"invalid start_date: {value!r}") from None
    if parsed.isoformat() != value:
        raise ValueError(f"invalid start_date: {value!r}")
    return parsed


def _add_months(start, months_ahead):
    index = start.year * 12 + (start.month - 1) + months_ahead
    year, month_zero = divmod(index, 12)
    month = month_zero + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def amortize(principal: str, annual_rate_percent: str, months: int, start_date: str) -> list[dict]:
    if isinstance(months, bool) or not isinstance(months, int):
        raise ValueError("months must be an integer")
    if months < 1 or months > 360:
        raise ValueError("months must be between 1 and 360")
    principal_amount = _parse_principal(principal)
    rate_percent = _parse_rate(annual_rate_percent)
    start = _parse_start_date(start_date)
    with localcontext() as context:
        context.prec = 50
        monthly_rate = rate_percent / Decimal(1200)
        if monthly_rate == 0:
            level_payment = (principal_amount / months).quantize(CENT, rounding=ROUND_HALF_UP)
        else:
            level_payment = (
                principal_amount * monthly_rate / (Decimal(1) - (Decimal(1) + monthly_rate) ** (-months))
            ).quantize(CENT, rounding=ROUND_HALF_UP)
        schedule = []
        balance = principal_amount
        for number in range(1, months + 1):
            interest = (balance * monthly_rate).quantize(CENT, rounding=ROUND_HALF_UP)
            if number == months:
                principal_part = balance
                payment = (balance + interest).quantize(CENT, rounding=ROUND_HALF_UP)
            else:
                payment = level_payment
                principal_part = payment - interest
            new_balance = (balance - principal_part).quantize(CENT, rounding=ROUND_HALF_UP)
            schedule.append(
                {
                    "n": number,
                    "date": _add_months(start, number).isoformat(),
                    "payment": payment,
                    "interest": interest,
                    "principal": principal_part,
                    "balance": new_balance,
                }
            )
            balance = new_balance
    return schedule


def total_interest(schedule) -> Decimal:
    total = Decimal("0.00")
    for row in schedule:
        total += row["interest"]
    return total.quantize(CENT, rounding=ROUND_HALF_UP)
