# Pull request pr_test_4

This package contains three modules: `task_a.py`, `task_b.py`, `task_c.py`. Each section below is the spec for one module. Where a section says `solution.py`, it means that section's module file. Implement and review the package as a whole; a defect may be in any module.


## Module `task_a.py` — task `idempotent_ledger`

# Idempotent payment ledger

Implement in `solution.py`:

```python
def process_payments(requests: list[dict]) -> dict
```

Rules:

1. `requests` must be a list of dicts, processed strictly in the given order. A non-list argument raises `ValueError`. An empty list returns `{"applied": [], "duplicates": [], "conflicts": [], "balances": {}}`.
2. Each request is a dict with fields `"key"`, `"account"`, `"currency"`, `"amount"` and `"reference"`. A missing field, or a request that is not a dict, raises `ValueError`.
3. Every request is validated before it is processed, including a repeat of an earlier key: an invalid repeat raises `ValueError` rather than being recorded as a duplicate or conflict (see rule 8).
4. Validation: `"key"` must be a non-empty string; `"account"` must be a non-empty string; `"currency"` must be a string of exactly 3 letters (A-Z, case-insensitive) and is normalized to upper case (so `"eur"` becomes `"EUR"`); `"amount"` must be a string parseable as `Decimal`, finite, strictly `> 0`, with at most 2 decimal places; `"reference"` must be a string (it may be empty). Any violation raises `ValueError`. Examples of invalid amounts: `"0.00"`, `"-1.00"`, `"10.005"`, `"abc"`, `""`, `"NaN"`.
5. Balances are kept per `(account, currency)` pair, starting at `Decimal("0.00")`. Account names are case-sensitive and are used exactly as given; only the currency is normalized.
6. The first occurrence of a key is applied: the amount is added to that `(account, currency)` balance, and an entry `{"key": key, "account": account, "currency": normalized_currency, "amount": D2, "balance_after": D2}` is appended to `"applied"` in processing order. `D2` means a `Decimal` quantized to exactly 2 decimal places (so `"10"` is recorded as `Decimal("10.00")` and `"10.5"` as `Decimal("10.50")`).
7. A later request whose key was already seen is compared with the first occurrence's payload: account (exactly as given), normalized currency, amount as a `Decimal` (so `"10.0"` and `"10.00"` are identical), and reference. If all four are identical, it is a duplicate: it is not applied, and its key is appended to `"duplicates"`. Each duplicate occurrence appends one entry, in the order the repeats occur.
8. If a later request with an already-seen key differs in any of those four payload fields, it is a conflict: it is not applied, and `{"key": key, "reason": "payload differs from first occurrence"}` (exactly that reason string) is appended to `"conflicts"`, one entry per conflict occurrence, in occurrence order. Later repeats are always compared against the first occurrence, never against a duplicate or conflict.
9. Duplicates and conflicts never change any balance, never add to `"applied"` and never create a balance entry.
10. The return value is `{"applied": [...], "duplicates": [...], "conflicts": [...], "balances": {...}}`. `"balances"` maps `"ACCOUNT:CCY"` (account exactly as given, then a colon, then the normalized currency) to the final `D2` balance, and contains an entry for every `(account, currency)` pair that had at least one applied payment. The `"balances"` dict is ordered by its keys sorted ascending (lexicographic).
11. All money values are `Decimal`, never `float`.
12. Worked example: requests `[{"key": "k1", "account": "A", "currency": "eur", "amount": "10.00", "reference": "r1"}, {"key": "k2", "account": "A", "currency": "EUR", "amount": "5.50", "reference": ""}, {"key": "k1", "account": "A", "currency": "EUR", "amount": "10.0", "reference": "r1"}]` give two applied entries with `balance_after` `Decimal("10.00")` and `Decimal("15.50")`, `duplicates == ["k1"]`, no conflicts, and `balances == {"A:EUR": Decimal("15.50")}`. Changing the third request's amount to `"11.00"` instead makes it a conflict with the exact reason above.
13. Use only the Python standard library.


## Module `task_b.py` — task `madrid_cutoff`

# Madrid cut-off: payment value date

Implement in `solution.py`:

```python
def is_madrid_business_day(date_str: str, holidays=()) -> bool
def payment_value_date(submitted: str, holidays=()) -> str
```

Rules:

1. A Madrid business day is a Monday-Friday whose date is not in `holidays`. Saturdays and Sundays are never business days.
2. `holidays` is a collection (e.g. list, tuple or set) of ISO date strings `"YYYY-MM-DD"`, each naming a valid calendar date. Any invalid holiday string (bad format, non-existent date, or a non-string entry) raises `ValueError`. A single string passed as `holidays` itself (instead of a collection of strings) also raises `ValueError`. Duplicate holidays are allowed.
3. `is_madrid_business_day(date_str, holidays=())` requires `date_str` to be a valid `"YYYY-MM-DD"` calendar date; otherwise it raises `ValueError`. It returns `True` exactly when rule 1 holds for that date.
4. `submitted` is a naive Europe/Madrid local datetime string `"YYYY-MM-DDTHH:MM"` or `"YYYY-MM-DDTHH:MM:SS"` (24-hour clock). No offset suffix is allowed: any offset (`+...`, `-...` after the time, or a trailing `Z`), a space instead of `T`, a missing time, invalid calendar/clock values, or any other format raises `ValueError`.
5. The cut-off is 17:00 local wall-clock time. If the submitted date is a Madrid business day AND the local time is strictly before 17:00, the value date is that submitted date. In all other cases (time `>= 17:00`, or the date is a weekend or holiday) the value date is the next Madrid business day strictly after the submitted date.
6. `payment_value_date` returns the value date as a `"YYYY-MM-DD"` string.
7. Nonexistent local times raise `ValueError`: a wall time that falls in the spring-forward gap (for example `"2026-03-29T02:30"`, when clocks jump from 02:00 to 03:00 in Europe/Madrid) does not exist. Detect this with a `zoneinfo` round-trip: attach `ZoneInfo("Europe/Madrid")`, convert to UTC and back, and require the wall time to match. This check applies even if that date is a weekend.
8. Ambiguous local times are accepted: a wall time in the fall-back overlap (for example `"2026-10-25T02:30"`, when 02:00-03:00 occurs twice) is valid and is treated by its wall time for the cut-off comparison in rule 5. (Its date decides business-day status as usual.)
9. Use only the Python standard library (`zoneinfo` for Europe/Madrid). Do not hard-code daylight-saving dates; the gap/overlap behaviour must follow the timezone rules.
10. Worked examples (no holidays unless stated): `"2026-03-27T16:59"` (Friday) -> `"2026-03-27"`; `"2026-03-27T17:00"` -> `"2026-03-30"` (Monday, because Saturday and Sunday follow); a Saturday submission `"2026-03-28T10:00"` -> `"2026-03-30"`; if `"2026-03-30"` is passed as a holiday, `"2026-03-27T17:00"` -> `"2026-03-31"`.
11. More examples: Friday `"2026-10-23T16:00"` -> `"2026-10-23"`; Friday `"2026-10-23T17:00"` -> `"2026-10-26"` (the Monday after the fall-back Sunday 2026-10-25). `"2026-03-29T02:30"` raises `ValueError` (gap), while `"2026-10-25T02:30"` is accepted and, being a Sunday, gives `"2026-10-26"`.


## Module `task_c.py` — task `percent_change`

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
