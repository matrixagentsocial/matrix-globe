# Day-count fractions and accrued interest

Implement in `solution.py`:

```python
def day_count_fraction(start: str, end: str, convention: str) -> Decimal
def accrued_interest(principal: str, annual_rate_percent: str, start: str, end: str, convention: str) -> Decimal
```

Rules (all explicit; the traps are in these details):

1. `start` and `end` must each be a `str` in exactly `YYYY-MM-DD` format naming a valid calendar date. Any other type, format, or an impossible date such as `"2024-02-30"` raises `ValueError`. If `end` is before `start`, both functions raise `ValueError`. If `end` equals `start`, the fraction is zero (rule 9) and accrued interest is `Decimal("0.00")` (for otherwise valid inputs).
2. `convention` must be a `str` exactly equal to one of `"30/360_US"`, `"30E/360"`, `"ACT/365F"`, `"ACT/ACT_ISDA"` (case-sensitive). Any other value, including `"act/365f"`, `"ACT/360"` or a non-string, raises `ValueError`.
3. In `accrued_interest`, `principal` must be a `str` parsed with `decimal.Decimal`. It must be finite, `>= 0`, and have at most 2 decimal places. A non-string, `"abc"`, `""`, `"NaN"`, `"Infinity"`, a negative value, or more than 2 decimal places such as `"10.005"` raises `ValueError`.
4. In `accrued_interest`, `annual_rate_percent` must be a `str` parsed with `decimal.Decimal`. It must be finite and satisfy `0 <= rate <= 100`. A non-string, an unparseable or non-finite string, a negative rate, or a rate above `100` raises `ValueError`.
5. The actual day difference is `(end - start).days` using real calendar dates, so leap days count. `ACT/365F` fraction is `actual_days / 365`, always with denominator `365` even in a leap year.
6. `ACT/ACT_ISDA` splits the period at each calendar-year boundary (`1 January`). Each portion contributes `days_in_portion / days_in_that_portion's_calendar_year`, where the denominator is `366` for a leap year and `365` otherwise. The fraction is the sum of the portions. A whole calendar year therefore contributes exactly `1`. Example: `2023-12-01` to `2024-02-01` is `31/365 + 31/366`.
7. `30/360_US` first adjusts the day numbers. Let `d1`, `m1`, `y1` be the start day/month/year and `d2`, `m2`, `y2` the end ones. A date is the last day of February if it is in February on the 28th (non-leap year) or 29th (leap year). If the start date is the last day of February, `d1` becomes `30`. If the end date is the last day of February and the start date is also the last day of February, `d2` becomes `30`; if the start date is not the last day of February, such an end date keeps its real day. Independently, if the start day is `31`, `d1` becomes `30`; if the end day is `31` and the adjusted `d1` is `>= 30`, `d2` becomes `30`. The day count is then `360*(y2-y1) + 30*(m2-m1) + (d2-d1)` with the adjusted days, and the fraction is `days / 360`.
8. `30E/360` caps each day at `30`: adjusted `d1 = min(start day, 30)` and adjusted `d2 = min(end day, 30)`, with no February special case. The day count is `360*(y2-y1) + 30*(m2-m1) + (d2-d1)` with the adjusted days, and the fraction is `days / 360`.
9. `day_count_fraction` returns a `Decimal` quantized to exactly 10 decimal places (exponent `-10`) with `ROUND_HALF_UP`. Equal dates return `Decimal("0.0000000000")`.
10. `accrued_interest` is computed from the **unrounded** fraction (the exact sum/quotient before the 10-place quantization of rule 9): `principal * (annual_rate_percent / 100) * unrounded_fraction`, quantized to cents (`Decimal("0.01")`) with `ROUND_HALF_UP`. It must not be computed from the 10-place rounded fraction returned by `day_count_fraction`. Divisions are evaluated with `Decimal` at precision `50` (for example via `decimal.localcontext`).
11. Use only the stdlib. Never use `float` for day-count or money maths.

Worked examples:

- `day_count_fraction("2024-01-31", "2024-07-31", "30/360_US")` is `180/360 = Decimal("0.5000000000")` (both 31sts become 30).
- `day_count_fraction("2023-01-01", "2024-01-01", "ACT/ACT_ISDA")` is `Decimal("1.0000000000")` (the whole of 2023, a non-leap year).
- `day_count_fraction("2023-12-01", "2024-02-01", "ACT/ACT_ISDA")` is `31/365 + 31/366`, i.e. `Decimal("0.1696309604")` after 10-place quantization.
- `day_count_fraction("2024-01-01", "2024-04-01", "ACT/365F")` is `91/365` (31 + 29 + 31 actual days), i.e. `Decimal("0.2493150685")`.
- `accrued_interest("10000.00", "5", "2024-01-31", "2024-07-31", "30/360_US")` is `10000 * 0.05 * 0.5 = Decimal("250.00")`.
