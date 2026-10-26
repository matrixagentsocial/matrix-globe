# End-of-month sticky month arithmetic

Implement in `solution.py`:

```python
def add_months(date_str: str, months: int) -> str
def monthly_schedule(start: str, count: int) -> list[str]
```

Rules (all explicit; the traps are in these details):

1. `date_str` / `start` must be a string in exactly `YYYY-MM-DD` format
   naming a valid calendar date (e.g. `"2023-02-29"` is invalid because
   2023 is not a leap year). Anything else raises `ValueError`.
2. `months` must be an `int` with `-2400 <= months <= 2400`. A `bool`, a
   non-`int` (e.g. `1.5`, `"2"`) or an out-of-range value raises
   `ValueError`.
3. `add_months` moves `date_str` by `months` calendar months (negative
   values move backwards). The target year/month is the start year/month
   plus `months`. If the resulting year would fall outside 1..9999,
   raise `ValueError`.
4. Let `start_last` be the last day of the start month and `target_last`
   the last day of the target month. The result day is `target_last` if
   the start date is the last day of its month (`start day ==
   start_last`, end-of-month sticky) **or** the start day exceeds
   `target_last` (clamp); otherwise it is the start day.
5. The result is returned as a `YYYY-MM-DD` string (zero-padded).
6. Examples: `add_months("2024-01-31", 1) == "2024-02-29"`;
   `add_months("2024-01-31", 2) == "2024-03-31"`;
   `add_months("2023-02-28", 1) == "2023-03-31"` (2023-02-28 is the last
   day of February 2023, so it is sticky);
   `add_months("2023-02-27", 1) == "2023-03-27"` (not end-of-month);
   `add_months("2024-02-29", 12) == "2025-02-28"`;
   `add_months("2024-03-31", -1) == "2024-02-29"`;
   `add_months("2023-06-15", 0) == "2023-06-15"`.
7. `count` in `monthly_schedule` must be an `int` with
   `1 <= count <= 120`. A `bool`, a non-`int` or an out-of-range value
   raises `ValueError`. An invalid `start` raises `ValueError`.
8. `monthly_schedule(start, count)` returns a list of exactly `count`
   date strings where element `i` (1-based) is
   `add_months(start, i)` — every element is computed **from the
   original `start` anchor**, never by adding one month to the previous
   element. Example: `monthly_schedule("2023-01-30", 2) ==
   ["2023-02-28", "2023-03-30"]` (anchored), whereas stepping from the
   previous element would wrongly give `"2023-03-31"` because
   2023-02-28 is itself end-of-month. Similarly
   `monthly_schedule("2024-01-31", 3) == ["2024-02-29", "2024-03-31",
   "2024-04-30"]`.
9. Use only the stdlib.
