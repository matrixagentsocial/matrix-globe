import calendar
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext

CENT = Decimal("0.01")
TEN_PLACES = Decimal("0.0000000001")
CONVENTIONS = ("30/360_US", "30E/360", "ACT/365F", "ACT/ACT_ISDA")


def _parse_date(value, name):
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    if len(value) != 10 or value[4] != "-" or value[7] != "-":
        raise ValueError(f"invalid {name}: {value!r}")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"invalid {name}: {value!r}") from None
    if parsed.isoformat() != value:
        raise ValueError(f"invalid {name}: {value!r}")
    return parsed


def _parse_convention(value):
    if not isinstance(value, str) or value not in CONVENTIONS:
        raise ValueError(f"invalid convention: {value!r}")
    return value


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


def _validate_period(start_value, end_value, convention_value):
    convention = _parse_convention(convention_value)
    start = _parse_date(start_value, "start")
    end = _parse_date(end_value, "end")
    if end < start:
        raise ValueError("end must not be before start")
    return start, end, convention


def _is_last_day_of_february(day_date):
    return day_date.month == 2 and day_date.day == calendar.monthrange(day_date.year, 2)[1]


def _fraction_unrounded(start, end, convention):
    if start == end:
        return Decimal(0)
    if convention == "ACT/365F":
        return Decimal((end - start).days) / Decimal(365)
    if convention == "ACT/ACT_ISDA":
        total = Decimal(0)
        current = start
        while current < end:
            next_year = date(current.year + 1, 1, 1)
            segment_end = min(next_year, end)
            days = (segment_end - current).days
            days_in_year = 366 if calendar.isleap(current.year) else 365
            total += Decimal(days) / Decimal(days_in_year)
            current = segment_end
        return total
    if convention == "30E/360":
        d1 = min(start.day, 30)
        d2 = min(end.day, 30)
        days = 360 * (end.year - start.year) + 30 * (end.month - start.month) + (d2 - d1)
        return Decimal(days) / Decimal(360)
    # 30/360_US
    start_feb_last = _is_last_day_of_february(start)
    end_feb_last = _is_last_day_of_february(end)
    d1 = start.day
    if start_feb_last or d1 == 31:
        d1 = 30
    d2 = end.day
    if end_feb_last and start_feb_last:
        d2 = 30
    elif d2 == 31 and d1 >= 30:
        d2 = 30
    days = 360 * (end.year - start.year) + 30 * (end.month - start.month) + (d2 - d1)
    return Decimal(days) / Decimal(360)


def day_count_fraction(start: str, end: str, convention: str) -> Decimal:
    start_date, end_date, parsed_convention = _validate_period(start, end, convention)
    with localcontext() as context:
        context.prec = 50
        fraction = _fraction_unrounded(start_date, end_date, parsed_convention)
        return fraction.quantize(TEN_PLACES, rounding=ROUND_HALF_UP)


def accrued_interest(principal: str, annual_rate_percent: str, start: str, end: str, convention: str) -> Decimal:
    principal_amount = _parse_decimal(principal, "principal")
    if principal_amount < 0:
        raise ValueError("principal must be >= 0")
    try:
        principal_amount = principal_amount.quantize(CENT)
    except InvalidOperation:
        raise ValueError("principal must have at most 2 decimal places") from None
    # Re-parse to detect more than 2 decimal places exactly.
    raw_principal = _parse_decimal(principal, "principal")
    if raw_principal != principal_amount:
        raise ValueError("principal must have at most 2 decimal places")
    rate = _parse_decimal(annual_rate_percent, "annual_rate_percent")
    if rate < 0 or rate > 100:
        raise ValueError("annual_rate_percent must be between 0 and 100")
    start_date, end_date, parsed_convention = _validate_period(start, end, convention)
    with localcontext() as context:
        context.prec = 50
        fraction = _fraction_unrounded(start_date, end_date, parsed_convention)
        interest = principal_amount * (rate / Decimal(100)) * fraction
        return interest.quantize(CENT, rounding=ROUND_HALF_UP)
