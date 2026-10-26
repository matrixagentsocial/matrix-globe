# Percent change

Implement in `solution.py`:

```python
def percent_change(old: str, new: str) -> Decimal | None
def apply_percent_change(old: str, percent: str) -> Decimal
```

Rules (all explicit; the traps are in these details):

1. All inputs are decimal strings parsed with `Decimal`. They must be finite (not `"NaN"`, `"Infinity"`, `"-Infinity"`), otherwise `ValueError`. Non-string inputs, unparseable strings such as `"abc"` or `""`, also raise `ValueError`. Inputs may have any number of decimal places (e.g. `"10.005"` is accepted here) and any sign.
2. `percent_change(old, new)` computes `(new - old) / abs(old) * 100`. The denominator is the absolute value of `old`, so the sign of the result is the sign of `new - old` alone.
3. The result of `percent_change` is quantized to exactly 2 decimal places with `ROUND_HALF_UP` (so `str()` shows cents of a percent, e.g. `Decimal("10.00")`).
4. If `old == 0` and `new == 0`, `percent_change` returns `Decimal("0.00")`. If `old == 0` and `new != 0`, it returns `None` (no finite percent change exists). Note `"0.00"` and `"-0"` both compare equal to zero.
5. Examples for `percent_change`: `("100", "110")` -> `Decimal("10.00")`; `("110", "100")` -> `Decimal("-9.09")` (because `-10/110*100 = -9.0909...`); `("3", "2")` -> `Decimal("-33.33")`; `("0", "5")` -> `None`; `("0", "0")` -> `Decimal("0.00")`.
6. Negative-base examples: `("-100", "-50")` -> `Decimal("50.00")` (the value rose by 50 toward zero: `(-50 - -100)/100*100`); `("-100", "-150")` -> `Decimal("-50.00")`; equivalently `("-200", "-100")` -> `Decimal("50.00")` and `("-200", "-300")` -> `Decimal("-50.00")`. Without the `abs()` these signs would flip.
7. `apply_percent_change(old, percent)` computes `old * (1 + percent / 100)` and quantizes the result to exactly 2 decimal places with `ROUND_HALF_UP`. `percent` follows the same parsing rules as rule 1 (finite decimal string, any sign, any number of decimal places), otherwise `ValueError`.
8. Examples for `apply_percent_change`: `("100.00", "10")` -> `Decimal("110.00")`; `("100.00", "-10")` -> `Decimal("90.00")`; `("50.00", "2.5")` -> `Decimal("51.25")`; `("0.00", "10")` -> `Decimal("0.00")`; `("33.33", "10")` -> `Decimal("36.66")` (because `33.33 * 1.1 = 36.663` rounds to `36.66`).
9. Both functions return `Decimal` values with exponent exactly `-2` (except the `None` case of rule 4).
10. Use only the stdlib. Never use `float` for the maths.
