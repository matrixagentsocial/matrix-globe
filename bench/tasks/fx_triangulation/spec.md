# FX conversion through EUR triangulation

Implement in `solution.py`:

```python
def convert_fx(amount: str, from_currency: str, to_currency: str, rates: dict) -> Decimal
def cross_rate(from_currency: str, to_currency: str, rates: dict) -> Decimal
```

Rules (all explicit; the traps are in these details):

1. `rates` must be a `dict`. It maps a currency code to the units of that
   currency per 1 EUR. Rate values may be `str`, `int` or `Decimal`
   (never `bool` and never `float`); each is converted with `Decimal`
   (via `str(value)` for `str`/`int`). Any other type, any unparseable
   value, any non-finite value, or any value `<= 0` raises `ValueError`.
   Every entry in `rates` is validated, even entries not used by the
   conversion. Rate keys are currency codes under rule 3; an invalid key
   raises `ValueError`.
2. All arithmetic uses `decimal.Decimal` with precision 50
   (`localcontext` prec 50) and never `float`.
3. Currency codes must be strings of exactly 3 letters `A-Z`. Matching is
   uppercase-insensitive: codes (including `rates` keys) are normalised
   to upper case before use, so `"usd"` means `"USD"`. A code that is not
   a string, is not exactly 3 characters, or contains a non-letter raises
   `ValueError`.
4. EUR has rate 1. `rates` may omit `"EUR"`, meaning rate 1. If `"EUR"`
   is present (in any letter case) its rate must equal 1, otherwise
   `ValueError` is raised.
5. A currency is known if, after normalisation, it is `"EUR"` or a key of
   `rates`. In `convert_fx` (except for the same-currency case in rule 7)
   and always in `cross_rate`, an unknown `from_currency` or
   `to_currency` raises `ValueError`.
6. `amount` must be a string parseable by `Decimal`, and finite.
   `"abc"`, `""`, `"NaN"`, `"Infinity"`, a non-string, or a non-finite
   value raises `ValueError`. Negative amounts are allowed.
7. Same-currency shortcut: if the normalised `from_currency` and
   `to_currency` are equal, `convert_fx` needs no rate lookup. It returns
   `amount` rounded under rule 8 to that currency's minor units, without
   checking whether the currency is known and without validating or
   looking up `rates` at all. (Code format under rule 3 and `amount`
   under rule 6 are still checked.)
8. Final rounding uses `ROUND_HALF_UP` to the target (`to_currency`)
   minor units. Minor units: `EUR`, `USD`, `GBP`, `CHF`, `CAD`, `AUD`
   have 2; `JPY`, `KRW` have 0; every other currency code has 2. So a
   2-unit result is quantized to `Decimal("0.01")` and a 0-unit result to
   `Decimal("1")`. In `Decimal`, `ROUND_HALF_UP` rounds away from zero,
   so `Decimal("-2.5")` to 0 places becomes `Decimal("-3")`.
9. Otherwise conversion goes through EUR and rounds only at the end:
   `eur = amount / rate[from_currency]`, then
   `result = eur * rate[to_currency]`, then rule 8 rounding. No
   intermediate rounding is applied, not even of the EUR amount.
10. `cross_rate(from_currency, to_currency, rates)` returns
    `rate[to_currency] / rate[from_currency]` quantized to exactly 10
    decimal places (`Decimal("0.0000000001")`) with `ROUND_HALF_UP`
    at precision 50. For two equal known currencies it returns
    `Decimal("1.0000000000")`.
11. Examples: with `rates = {"USD": "1.10", "GBP": "0.88"}`,
    `convert_fx("110", "USD", "GBP", rates)` is `Decimal("88.00")`
    because 110 / 1.10 = 100 EUR and 100 * 0.88 = 88 GBP; and
    `cross_rate("USD", "GBP", rates)` is `Decimal("0.8000000000")`.
12. JPY example: with `rates = {"JPY": "160"}`,
    `convert_fx("100", "EUR", "JPY", rates)` is `Decimal("16000")`
    (0 decimal places), and `convert_fx("100.4", "JPY", "JPY", rates)`
    is `Decimal("100")`.
13. Only the stdlib may be used. Never use `float` for the maths.
