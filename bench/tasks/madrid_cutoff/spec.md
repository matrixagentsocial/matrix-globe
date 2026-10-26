# Madrid cut-off: payment value date

Implement in `solution.py`:

```python
def is_madrid_business_day(date_str: str, holidays=()) -> bool
def payment_value_date(submitted: str, holidays=()) -> str
```

Rules:

1. A Madrid business day is a Monday-Friday whose date is not in `holidays`. Saturdays and Sundays are never business days.
2. `holidays` is a collection (e.g. list, tuple or set) of ISO date strings `"YYYY-MM-DD"`, each naming a valid calendar date. Any invalid holiday string (bad format, non-existent date, or a non-string entry) raises `ValueError`. A single string passed as `holidays` itself (instead of a collection of strings) also raises `ValueError`. Duplicate holidays are allowed.
3. `is_madrid_business_day(date_str, holidays=())` requires `date_str` to be a valid `"YYYY-MM-DD"` calendar date; otherwise it raises `ValueError`. It returns `True` exactly when rule 1 holds for that date.
4. `submitted` is a naive Europe/Madrid local datetime string `"YYYY-MM-DDTHH:MM"` or `"YYYY-MM-DDTHH:MM:SS"` (24-hour clock). No offset suffix is allowed: any offset (`+...`, `-...` after the time, or a trailing `Z`), a space instead of `T`, a missing time, invalid calendar/clock values, or any other format raises `ValueError`.
5. The cut-off is 17:00 local wall-clock time. If the submitted date is a Madrid business day AND the local time is strictly before 17:00, the value date is that submitted date. In all other cases (time `>= 17:00`, or the date is a weekend or holiday) the value date is the next Madrid business day strictly after the submitted date.
6. `payment_value_date` returns the value date as a `"YYYY-MM-DD"` string.
7. Nonexistent local times raise `ValueError`: a wall time that falls in the spring-forward gap (for example `"2026-03-29T02:30"`, when clocks jump from 02:00 to 03:00 in Europe/Madrid) does not exist. Detect this with a `zoneinfo` round-trip: attach `ZoneInfo("Europe/Madrid")`, convert to UTC and back, and require the wall time to match. This check applies even if that date is a weekend.
8. Ambiguous local times are accepted: a wall time in the fall-back overlap (for example `"2026-10-25T02:30"`, when 02:00-03:00 occurs twice) is valid and is treated by its wall time for the cut-off comparison in rule 5. (Its date decides business-day status as usual.)
9. Use only the Python standard library (`zoneinfo` for Europe/Madrid). Do not hard-code daylight-saving dates; the gap/overlap behaviour must follow the timezone rules.
10. Worked examples (no holidays unless stated): `"2026-03-27T16:59"` (Friday) -> `"2026-03-27"`; `"2026-03-27T17:00"` -> `"2026-03-30"` (Monday, because Saturday and Sunday follow); a Saturday submission `"2026-03-28T10:00"` -> `"2026-03-30"`; if `"2026-03-30"` is passed as a holiday, `"2026-03-27T17:00"` -> `"2026-03-31"`.
11. More examples: Friday `"2026-10-23T16:00"` -> `"2026-10-23"`; Friday `"2026-10-23T17:00"` -> `"2026-10-26"` (the Monday after the fall-back Sunday 2026-10-25). `"2026-03-29T02:30"` raises `ValueError` (gap), while `"2026-10-25T02:30"` is accepted and, being a Sunday, gives `"2026-10-26"`.
