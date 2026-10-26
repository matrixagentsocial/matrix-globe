# Allocate an amount by ratios

Implement in `solution.py`:

```python
def allocate_by_ratios(total: str, ratios: list) -> list[Decimal]
```

Rules (all explicit; the traps are in these details):

1. `total` is a money string parsed with `Decimal`. It must be finite and have at most 2 decimal places, otherwise `ValueError` (e.g. `"abc"`, `""`, `"NaN"`, `"Infinity"`, `"10.005"`). It may be negative, zero, or positive.
2. `ratios` must be a non-empty list, otherwise `ValueError`. Each entry is either an `int` (not `bool`) or a decimal string parseable by `Decimal` (a `Decimal` instance is also accepted). `float` entries, `bool` entries, non-numeric strings and any other types raise `ValueError`.
3. Every weight must be finite and `>= 0`, and at least one weight must be `> 0`, otherwise `ValueError`. Weights may have any number of decimal places when given as strings (e.g. `"1.5"`).
4. Negative totals: allocate the absolute value of `total` by the rules below, then negate every resulting part. Example: `"-0.01"` by `[1, 1]` -> `[Decimal("-0.01"), Decimal("0.00")]` (the negated zero part is `Decimal("0.00")`, which equals `Decimal("-0.00")`); the parts still sum exactly to `total`. A total of `"0.00"` returns one `Decimal("0.00")` per ratio.
5. Method (on the absolute total, in cents): each entry's exact share is `total_cents * weight / total_weight`. Give each entry the floor (truncation toward zero, all values non-negative here) of its exact share in whole cents.
6. Distribute the remaining cents one each in order of largest fractional remainder. Ties in fractional remainder are broken by larger weight, then by lower index. Each entry receives at most one remainder cent per pass; the number of remaining cents is always less than the number of positive-weight entries, so one pass suffices.
7. Entries with weight `0` always get `Decimal("0.00")` and never receive a remainder cent: remainder cents go only to entries with weight `> 0`, even when a zero-weight entry's fractional remainder would be considered (it is exactly `0` and it is explicitly skipped).
8. Return a list of `Decimal` values in the original input order, each quantized to exactly 2 decimal places (exponent `-2`), summing exactly to `total`.
9. Examples: `"100.00"` by `[1, 1, 1]` -> `[Decimal("33.34"), Decimal("33.33"), Decimal("33.33")]` (equal remainders and equal weights tie-break to the lower index first); `"10.00"` by `[2, 1, 1]` -> `[Decimal("5.00"), Decimal("2.50"), Decimal("2.50")]`; `"0.05"` by `[1, 1]` -> `[Decimal("0.03"), Decimal("0.02")]`; `"100.00"` by `[0, 1, 0]` -> `[Decimal("0.00"), Decimal("100.00"), Decimal("0.00")]`.
10. Further example (weight tie-break): `"0.03"` by `[1, 2]` -> exact shares `1` cent and `2` cents with no remainder, giving `[Decimal("0.01"), Decimal("0.02")]`. And `"0.05"` by `[1, 2]`: exact shares are `1.666...` and `3.333...` cents, floors `1` and `3`, one remaining cent goes to the larger fractional remainder (`0.666...`, index 0), giving `[Decimal("0.02"), Decimal("0.03")]`.
11. Use only the stdlib. Never use `float` for the money maths.
