import calendar
from datetime import date


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


def _check_int(value, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")


def add_months(date_str: str, months: int) -> str:
    start = _parse_date(date_str)
    _check_int(months, "months")
    if months < -2400 or months > 2400:
        raise ValueError("months out of range -2400..2400")
    total = start.year * 12 + (start.month - 1) + months
    target_year, target_month0 = divmod(total, 12)
    target_month = target_month0 + 1
    if target_year < 1 or target_year > 9999:
        raise ValueError("resulting date out of range")
    start_last = calendar.monthrange(start.year, start.month)[1]
    target_last = calendar.monthrange(target_year, target_month)[1]
    if start.day == start_last or start.day > target_last:
        day = target_last
    else:
        day = start.day
    return date(target_year, target_month, day).isoformat()


def monthly_schedule(start: str, count: int) -> list[str]:
    _parse_date(start)
    _check_int(count, "count")
    if count < 1 or count > 120:
        raise ValueError("count out of range 1..120")
    return [add_months(start, i) for i in range(1, count + 1)]
