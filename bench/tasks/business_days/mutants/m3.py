from datetime import date, timedelta


def _holiday_set(holidays) -> set:
    return set(holidays) if holidays else set()


def is_business_day(d: date, holidays=()) -> bool:
    return d.weekday() < 5 and d not in _holiday_set(holidays)


def _next_business_day(d: date, hol: set) -> date:
    cur = d
    while not (cur.weekday() < 5 and cur not in hol):
        cur += timedelta(days=1)
    return cur


def _prev_business_day(d: date, hol: set) -> date:
    cur = d
    while not (cur.weekday() < 5 and cur not in hol):
        cur -= timedelta(days=1)
    return cur


def adjust_business_day(d: date, holidays=(), convention: str = "modified_following") -> date:
    if not isinstance(convention, str):
        raise ValueError("convention must be a string")
    hol = _holiday_set(holidays)
    key = convention.lower()
    if key == "following":
        return _next_business_day(d, hol)
    if key == "preceding":
        return _prev_business_day(d, hol)
    if key == "modified_following":
        nxt = _next_business_day(d, hol)
        if nxt.month != d.month or nxt.year != d.year:
            return _prev_business_day(d, hol)
        return nxt
    raise ValueError(f"unknown convention: {convention!r}")


def add_business_days(start: date, n: int, holidays=()) -> date:
    if not isinstance(n, int):
        raise ValueError("n must be an integer")
    hol = _holiday_set(holidays)
    if n == 0:
        return start
    step = timedelta(days=1) if n > 0 else timedelta(days=-1)
    remaining = abs(n)
    cur = start
    while remaining:
        cur += step
        if cur.weekday() < 5 and cur not in hol:
            remaining -= 1
    return cur
