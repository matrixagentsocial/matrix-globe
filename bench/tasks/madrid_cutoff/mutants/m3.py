import re
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    MADRID = ZoneInfo("Europe/Madrid")
except ZoneInfoNotFoundError:  # Windows / slim images without tzdata
    MADRID = None
CUTOFF = time(17, 0)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$")


def _parse_date(value):
    if not isinstance(value, str) or not _DATE_RE.match(value):
        raise ValueError(f"invalid date: {value!r}")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"invalid date: {value!r}") from None


def _parse_holidays(holidays):
    if isinstance(holidays, str):
        holidays = [holidays]
    if holidays is None:
        raise ValueError("holidays must be a collection of date strings")
    try:
        items = list(holidays)
    except TypeError:
        raise ValueError("holidays must be a collection of date strings") from None
    return {_parse_date(item) for item in items}


def is_madrid_business_day(date_str, holidays=()):
    day = _parse_date(date_str)
    holiday_set = _parse_holidays(holidays)
    return day.weekday() < 5 and day not in holiday_set


def _next_business_day(day, holiday_set):
    candidate = day + timedelta(days=1)
    while candidate.weekday() >= 5 or candidate in holiday_set:
        candidate += timedelta(days=1)
    return candidate


def payment_value_date(submitted, holidays=()):
    holiday_set = _parse_holidays(holidays)
    if not isinstance(submitted, str) or not _DT_RE.match(submitted):
        raise ValueError(f"invalid submitted datetime: {submitted!r}")
    fmt = "%Y-%m-%dT%H:%M:%S" if len(submitted) == 19 else "%Y-%m-%dT%H:%M"
    try:
        naive = datetime.strptime(submitted, fmt)
    except ValueError:
        raise ValueError(f"invalid submitted datetime: {submitted!r}") from None
    if MADRID is not None:
        attached = naive.replace(tzinfo=MADRID)
        round_tripped = attached.astimezone(timezone.utc).astimezone(MADRID)
        if round_tripped.replace(tzinfo=None) != naive:
            raise ValueError(f"nonexistent local time: {submitted!r}")
    else:
        # Fallback without tzdata: Europe/Madrid follows the EU rule,
        # clocks jump 02:00 -> 03:00 on the last Sunday of March, so
        # local times 02:00-02:59 on that day do not exist.
        last_march_day = date(naive.year, 3, 31)
        last_sunday_march = last_march_day - timedelta(
            days=(last_march_day.weekday() + 1) % 7
        )
        if naive.date() == last_sunday_march and naive.hour == 2:
            raise ValueError(f"nonexistent local time: {submitted!r}")
    day = naive.date()
    if day.weekday() < 5 and day not in holiday_set and naive.time() < CUTOFF:
        return day.isoformat()
    return _next_business_day(day, holiday_set).isoformat()
