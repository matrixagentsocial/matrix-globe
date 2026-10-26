# Business days with Modified Following

Implement in `solution.py` (dates are `datetime.date` objects):

```python
def is_business_day(d: date, holidays=()) -> bool
def adjust_business_day(d: date, holidays=(), convention: str = "modified_following") -> date
def add_business_days(start: date, n: int, holidays=()) -> date
```

Rules (all explicit; the traps are in these details):

1. A business day is Monday to Friday (`weekday() < 5`) and not in
   `holidays`. `holidays` may be any iterable of `date` objects
   (list, set, tuple); duplicates and holidays that fall on a weekend
   have no extra effect.
2. `adjust_business_day` conventions (case-insensitive):
   - `"following"`: if `d` is a business day return `d`, else the next
     business day.
   - `"modified_following"`: like `"following"`, **but** if the next
     business day falls in a different calendar month, return the
     previous business day instead.
   - `"preceding"`: if `d` is a business day return `d`, else the
     previous business day.
   Any other convention raises `ValueError`.
3. `add_business_days(start, n, holidays)`:
   - `n == 0`: return `start` unchanged, even if it is not a business day.
   - `n > 0`: move forward one calendar day at a time, counting only
     business days, until `n` business days have been counted. The
     start date itself is never counted.
   - `n < 0`: same, moving backward.
   - `n` must be an `int` (`bool` is not accepted); otherwise `ValueError`.
   `add_business_days` does **not** apply a Following/Modified
   Following adjustment to the start date first: counting starts from
   the calendar day after (or before) `start`.
4. Use only the stdlib.
