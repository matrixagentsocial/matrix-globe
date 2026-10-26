# Pro-rata billing for a period with mid-cycle price changes

Implement in `solution.py`:

```python
def prorate_period(period_start: str, period_end: str, changes: list[dict]) -> dict
```

Rules:

1. `period_start` and `period_end` are ISO date strings `"YYYY-MM-DD"` naming valid calendar dates. The billing period is `[period_start, period_end)`: `period_start` is included and `period_end` is exclusive. `period_end` must be strictly after `period_start`, otherwise `ValueError`. Invalid date strings (bad format, or a non-existent date such as `"2024-02-30"`) raise `ValueError`.
2. `changes` must be a non-empty list of dicts. Each entry is `{"date": "YYYY-MM-DD", "monthly_price": str}`. Any missing key, invalid date, or invalid entry shape raises `ValueError`. Entries may be given in any order and are applied in date order.
3. Each `monthly_price` must be a string parseable as `Decimal`, finite, `>= 0`, with at most 2 decimal places. Values such as `"-1.00"`, `"10.005"`, `"abc"`, `""`, `"NaN"` raise `ValueError`.
4. Duplicate effective dates are forbidden: two entries with the same `"date"` raise `ValueError`, even if that date lies outside the period.
5. The entry with the earliest date must have a date `<= period_start`, otherwise `ValueError` (no plan covers the start of the period). That earliest applicable plan applies from `period_start`. More precisely, the plan in force at `period_start` is the entry with the greatest date `<= period_start`; earlier entries are superseded (but still validated). Entries with a date `>= period_end` are ignored for segmentation (including an entry exactly on `period_end`), but they are still validated under rules 2-4.
6. Segments are consecutive `[seg_start, seg_end)` intervals covering the whole period, split at each change date strictly inside the period. Adjacent segments with the same `monthly_price` are merged into a single segment. Therefore a mid-period change to the same price produces a single segment for the whole period.
7. `period_days` is the number of actual calendar days in `[period_start, period_end)` (so a period spanning a leap-day February counts 29 days for that month). Each segment's `days` is its actual number of days, and the segment days sum to `period_days`.
8. Each segment amount is `monthly_price * segment_days / period_days`, computed with `Decimal` (never `float`) and quantized to cents (2dp) with `ROUND_HALF_UP`, per segment.
9. The return value is `{"period_days": int, "segments": [...], "total": D2}`. Each segment is `{"from": iso_date_str, "to": iso_date_str, "days": int, "monthly_price": D2, "amount": D2}`, where `"from"` is the inclusive segment start, `"to"` is the exclusive segment end (for the last segment this is exactly `period_end`), and `D2` means a `Decimal` quantized to exactly 2 decimal places. `"total"` is the sum of the (rounded) segment amounts, quantized to cents.
10. Worked example: period `"2024-03-01"` to `"2024-04-01"` (31 days) with changes `[{"date": "2024-03-01", "monthly_price": "31.00"}, {"date": "2024-03-16", "monthly_price": "62.00"}]` gives segment 1 from `2024-03-01` to `2024-03-16`, 15 days, amount `31.00 * 15 / 31 = Decimal("15.00")`; segment 2 from `2024-03-16` to `2024-04-01`, 16 days, amount `62.00 * 16 / 31 = Decimal("32.00")`; `total` is `Decimal("47.00")`.
11. Leap-year example: period `"2024-02-01"` to `"2024-03-01"` has `period_days == 29`. A single plan at `"29.00"` from `2024-02-01` gives one segment of 29 days with amount `Decimal("29.00")`.
12. Use only the Python standard library.
