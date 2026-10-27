# Pull request pr_test_3

This package contains three modules: `task_a.py`, `task_b.py`, `task_c.py`. Each section below is the spec for one module. Where a section says `solution.py`, it means that section's module file. Implement and review the package as a whole; a defect may be in any module.


## Module `task_a.py` — task `duplicate_payments`

# Find duplicate payments

Implement in `solution.py`:

```python
def find_duplicate_payments(payments: list[dict], window_days: int = 7) -> list[dict]
```

Rules (all explicit; the traps are in these details):

1. Each payment is a dict `{"id": str, "date": "YYYY-MM-DD", "vendor": str, "amount": str, "currency": str}`. Missing keys, non-dict entries, or wrong types (non-string `id`/`date`/`vendor`/`amount`/`currency`) raise `ValueError`. An empty `payments` list returns `[]`.
2. `id` must be a non-empty string. Two payments with the same `id` raise `ValueError`, even if every other field differs.
3. `date` must be a valid calendar date in exactly `YYYY-MM-DD` format (parsed strictly, e.g. `"2024-02-30"` and `"01/02/2024"` raise `ValueError`). `amount` must be a finite `Decimal` string with at most 2 decimal places (e.g. `"abc"`, `""`, `"NaN"`, `"Infinity"`, `"10.005"` raise `ValueError`). Amounts are signed: `"-50.00"` is allowed.
4. `window_days` must be an `int` (not `bool`) with `0 <= window_days <= 365`, otherwise `ValueError`. The default is `7`.
5. Vendor normalization is applied in exactly this order: (a) uppercase the string; (b) remove every character in the exact set `.,;:'"()/-` (period, comma, semicolon, colon, apostrophe, double quote, left parenthesis, right parenthesis, slash, hyphen); (c) collapse every run of internal whitespace to a single space and trim leading/trailing whitespace; (d) split on single spaces into tokens; (e) repeatedly drop the last token while it is in `{"SA","SL","SLU","LTD","LIMITED","INC","LLC","GMBH","BV","NV","SAS"}`, stopping when the last token is not in that set or no tokens remain. Example: `"ACME, S.L."` -> remove punctuation -> `"ACME SL"` -> drop `SL` -> `"ACME"`. Example: `"Foo-Bar / B.V."` -> `"FOOBAR BV"` -> drop `BV` -> `"FOOBAR"`. Example: `"SA Holdings"` stays `"SA HOLDINGS"` (only trailing tokens are dropped).
6. If the normalized vendor is empty (e.g. vendor `".,-"`, whose characters are all removed, or `"LTD"` alone, whose only token is dropped as a legal-form suffix) raise `ValueError`.
7. Currency is normalized by trimming whitespace and uppercasing (e.g. `" eur "` -> `"EUR"`). An empty currency after trimming raises `ValueError`.
8. Two distinct payments are directly duplicate if all hold: normalized vendors are equal (and non-empty), normalized currencies are equal, amounts are exactly equal as `Decimal` (signed, so `"-50.00"` is never a duplicate of `"50.00"`, while `"50.0"` equals `"50.00"` numerically), and the absolute difference between their dates is `<= window_days` days. Exactly `window_days` days apart counts; `window_days + 1` days does not.
9. Groups are the connected components of the direct-duplicate graph with size `>= 2`. Duplication is transitive through chains: if A-B are within the window and B-C are within the window, A, B and C form one group even if A-C are more than `window_days` apart. Every payment belongs to at most one group. Payments in no group are omitted.
10. Each returned group is `{"payment_ids": [...], "vendor": <normalized vendor>, "amount": <Decimal quantized to 2dp>, "currency": <normalized currency>}`. All payments in a group share the same normalized vendor, amount and currency, so those fields are the common values.
11. Inside a group, `payment_ids` are sorted by `(date, id)` ascending (date first, then the id string). Groups are sorted by `(earliest date in the group, first payment id in the group's sorted payment_ids)` ascending.
12. Worked example: payments `p1 2024-01-01 "Acme Ltd" "100.00" EUR`, `p2 2024-01-05 "ACME, LTD." "100.00" eur`, `p3 2024-01-20 "Other" "100.00" EUR` with the default window `7` return one group `{"payment_ids": ["p1", "p2"], "vendor": "ACME", "amount": Decimal("100.00"), "currency": "EUR"}`; `p3` is excluded (different vendor and too far from `p2`).
13. Use only the stdlib. Never use `float` for the money maths.


## Module `task_b.py` — task `eom_roll`

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


## Module `task_c.py` — task `fx_triangulation`

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
