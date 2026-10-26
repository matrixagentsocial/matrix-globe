# Currency rounding with ISO-4217 minor units

Implement in `solution.py`:

```python
def round_money(amount: str, currency: str, mode: str = "HALF_UP") -> Decimal
```

Rules (all explicit; the traps are in these details):

1. `amount` is a decimal string parsed with `decimal.Decimal`. It must
   be finite; `"abc"`, `""`, `"NaN"`, `"Infinity"` raise `ValueError`.
   Negative amounts are allowed and round symmetrically (see rule 4).
2. `currency` is an ISO-4217 code, case-insensitive (`"eur"` == `"EUR"`).
   Minor units (decimal places) for the supported currencies:
   `EUR 2, USD 2, GBP 2, CHF 2, AUD 2, CAD 2, JPY 0, KRW 0, VND 0,
   BHD 3, KWD 3, OMR 3, TND 3, JOD 3`.
   Any other currency code raises `ValueError`.
3. `mode` is case-insensitive and must be one of:
   - `"HALF_UP"`: ties go away from zero (`2.5 -> 3`, `-2.5 -> -3` at 0 places).
   - `"HALF_EVEN"`: ties go to the even neighbour (banker's rounding;
     `2.5 -> 2`, `3.5 -> 4`, `-2.5 -> -2` at 0 places).
   - `"DOWN"`: toward zero (truncate; `1.239 -> 1.23`, `-1.239 -> -1.23` at 2 places).
   - `"UP"`: away from zero (`1.231 -> 1.24`, `-1.231 -> -1.24` at 2 places).
   Any other mode raises `ValueError`.
4. The result is a `Decimal` quantized to exactly the currency's minor
   units (exponent `-2`, `0` or `-3`). `Decimal`'s own rounding modes
   already behave as rule 3 states for negative numbers; do not take
   `abs()` and re-apply a sign incorrectly, and never use `float`.
5. Only the currency's minor-unit quantum is applied. Do not round to
   cash denominations (for example no 0.05 CHF cash rounding).
6. Use only the stdlib.
