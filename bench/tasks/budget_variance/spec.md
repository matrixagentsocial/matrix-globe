# Budget variance report

Implement in `solution.py`:

```python
def variance_report(lines: list[dict]) -> list[dict]
def variance_summary(lines: list[dict]) -> dict
```

Rules (all explicit; the traps are in these details):

1. Each line is a dict `{"name": str, "kind": "revenue" | "cost", "budget": str, "actual": str}`. Missing keys, non-dict entries, a non-string `name`, or a `kind` other than exactly `"revenue"` or `"cost"` raise `ValueError`. Both functions apply the same validation; `variance_summary` must raise on the same bad input as `variance_report`.
2. `budget` and `actual` are money strings parsed with `Decimal`. They may have any sign (negative revenue and negative cost are allowed), must be finite, and must have at most 2 decimal places. Inputs such as `"abc"`, `""`, `"NaN"`, `"Infinity"` or `"10.005"` raise `ValueError`.
3. `variance_report` returns one dict per input line, in input order (no sorting, no grouping). Each dict is exactly `{"name", "kind", "budget", "actual", "variance", "variance_percent", "favourable", "status"}` with the line's original `name` and `kind`.
4. `budget` and `actual` in the output are `Decimal` quantized to exactly 2 decimal places. `variance` is `actual - budget` (signed, in that order for both kinds), quantized to exactly 2 decimal places.
5. `favourable` is `True` when `variance > 0` for a `revenue` line, or when `variance < 0` for a `cost` line. When `variance == 0`, `favourable` is `False` for both kinds. Otherwise `favourable` is `False`.
6. `status` is `"favourable"` when `favourable` is `True`, `"on_budget"` when `variance == 0`, and `"unfavourable"` otherwise. So a zero-variance line is always `{"favourable": False, "status": "on_budget"}`.
7. `variance_percent` is `(variance / budget * 100)` computed from the signed variance and the signed budget, quantized to 2 decimal places with `ROUND_HALF_UP`. If `budget == 0`, `variance_percent` is `None` (even when `variance` is also `0`). Example: revenue budget `"100.00"`, actual `"110.00"` -> variance `10.00`, percent `10.00`. Cost budget `"100.00"`, actual `"110.00"` -> variance `10.00`, percent `10.00` (the percent keeps the sign of the variance; favourability is reported separately).
8. `variance_summary` returns exactly `{"total_budget_revenue", "total_actual_revenue", "total_budget_cost", "total_actual_cost", "net_budget", "net_actual", "net_variance", "favourable_count", "unfavourable_count", "on_budget_count"}`. All money values are `Decimal` quantized to exactly 2 decimal places; the counts are `int`.
9. The four totals are the plain sums of the respective `budget`/`actual` values over lines of that kind only. A kind with no lines totals `Decimal("0.00")`.
10. `net_budget` is `total_budget_revenue - total_budget_cost`. `net_actual` is `total_actual_revenue - total_actual_cost`. `net_variance` is `net_actual - net_budget`.
11. `favourable_count`, `unfavourable_count` and `on_budget_count` count lines by their `status` as defined in rule 6, over all lines of both kinds. The three counts sum to `len(lines)`.
12. Empty `lines` returns `[]` from `variance_report`, and a summary whose money values are all `Decimal("0.00")` and whose counts are all `0`.
13. Worked example: lines `[{"name":"Sales","kind":"revenue","budget":"100.00","actual":"110.00"}, {"name":"Rent","kind":"cost","budget":"50.00","actual":"40.00"}]` -> report variances `10.00` (favourable) and `-10.00` (favourable, because cost fell); summary `net_budget 50.00`, `net_actual 70.00`, `net_variance 20.00`, `favourable_count 2`.
14. Use only the stdlib. Never use `float` for the money maths.
