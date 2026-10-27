# Pull request pr_test_6

This package contains three modules: `task_a.py`, `task_b.py`, `task_c.py`. Each section below is the spec for one module. Where a section says `solution.py`, it means that section's module file. Implement and review the package as a whole; a defect may be in any module.


## Module `task_a.py` — task `running_balance`

# Running balance over sorted transactions

Implement in `solution.py`:

```python
def running_balance(transactions: list[dict], opening_balance: str) -> list[dict]
def closing_balance(transactions: list[dict], opening_balance: str) -> Decimal
```

Rules (all explicit; the traps are in these details):

1. `opening_balance` is a decimal string parsed with `decimal.Decimal`. It must be a string, finite, and have at most 2 decimal places (it may be negative, zero, or positive). Otherwise raise `ValueError` (including `"abc"`, `""`, `"NaN"`, `"Infinity"`, `"10.005"`, and non-string inputs). It is treated as quantized to exactly 2 decimal places.
2. `transactions` must be a `list`. A non-list raises `ValueError`. Each element must be a `dict` containing at least the keys `"id"`, `"value_date"`, `"booking_date"` and `"amount"`; a missing key or a non-dict element raises `ValueError`. Extra keys are ignored and do not appear in the output.
3. `"id"` must be a non-empty string, else `ValueError`. Ids must be unique across the whole list (exact string comparison); a duplicate id raises `ValueError`.
4. `"value_date"` and `"booking_date"` must each be strings in exactly `YYYY-MM-DD` format (4-digit year, 2-digit month, 2-digit day, hyphen separators) naming a valid calendar date. Anything else (for example `"2024-13-01"`, `"2024-02-30"`, `"01/02/2024"`, `"2024-1-1"`, or a non-string) raises `ValueError`.
5. `"amount"` must be a string parsed with `Decimal`, finite, with at most 2 decimal places. It is signed: credits are positive and debits are negative. Zero (`"0"`, `"0.00"`, `"-0.00"`) is allowed. Anything else (for example `"10.005"`, `"abc"`, `""`, `"NaN"`, a non-string such as a float or int) raises `ValueError`. Amounts are normalized to exactly 2 decimal places in the output (so `"-0.00"` becomes `Decimal("0.00")`).
6. Neither function mutates its input: the input list and its dicts are unchanged after the call.
7. Transactions are sorted by `value_date` ascending, then `booking_date` ascending, then `id` ascending using plain string comparison. The date strings sort the same lexicographically as chronologically because of the fixed format in Rule 4.
8. `running_balance` returns one output row per input transaction, in the sorted order of Rule 7. Each row is exactly `{"id": str, "value_date": str, "booking_date": str, "amount": Decimal, "balance": Decimal}`, where `value_date` and `booking_date` are the original strings, `amount` is the normalized amount (Rule 5), and `balance` is the running balance after applying that transaction: `opening_balance + sum of amounts of all rows up to and including this one`, in sorted order.
9. Every `amount` and `balance` in the output is a `Decimal` quantized to exactly 2 decimal places. Never use `float`.
10. If `transactions` is empty, `running_balance` returns `[]` and `closing_balance` returns the opening balance quantized to 2 decimal places.
11. `closing_balance` returns a single `Decimal` quantized to exactly 2 decimal places: the `balance` of the last row of `running_balance`, or the quantized opening balance when the list is empty. It applies exactly the same validation and sorting as `running_balance`.
12. Use only the stdlib.

Worked example: with opening `"100.00"` and transactions
`{"id": "b", "value_date": "2024-01-02", "booking_date": "2024-01-03", "amount": "10.00"}`,
`{"id": "a", "value_date": "2024-01-02", "booking_date": "2024-01-02", "amount": "-30.00"}`,
`{"id": "c", "value_date": "2024-01-01", "booking_date": "2024-01-05", "amount": "5.00"}`,
the sorted order is `c` (earliest value_date), then `a` (same value_date as `b` but earlier booking_date), then `b`. Balances are `105.00`, `75.00`, `85.00`, and `closing_balance` is `Decimal("85.00")`.


## Module `task_b.py` — task `spanish_bank_csv`

# Spanish bank statement CSV parsing

Implement in `solution.py`:

```python
def parse_bank_csv(text: str) -> list[dict]
def summarize_transactions(transactions: list[dict]) -> dict
```

Rules (all explicit; the traps are in these details):

1. `text` must be a string, otherwise `ValueError` is raised. It may
   start with a single BOM `"\ufeff"`, which is stripped before anything
   else. Lines are split as lines of the original text; line numbers
   below are 1-based in the original text (the first physical line is
   line 1, whether or not it is blank or the header).
2. Blank lines (empty, or containing only whitespace) are skipped
   everywhere and produce no row.
3. The first non-empty line must be exactly the header
   `Fecha;Concepto;Importe;Saldo` (case-sensitive, no extra spaces).
   Anything else, or no non-empty line at all, raises `ValueError`.
4. Every later non-empty line is one data row parsed as CSV with
   delimiter `;`, quote character `"`, and standard double-doublequote
   escaping (`""` inside a quoted field means one `"`). A quoted field
   may contain `;`. Quoted fields do not span lines. A row must produce
   exactly 4 fields, otherwise it is malformed.
5. Any malformed data row raises `ValueError` whose message contains
   the text `line <N>` where `<N>` is that row's 1-based line number in
   the original text (for example `line 4`). This includes wrong field
   counts, bad CSV quoting, bad dates and bad amounts.
6. Field 1, `Fecha` (after stripping surrounding whitespace), must be
   in exactly `dd/mm/yyyy` form (2-digit day, 2-digit month, 4-digit
   year) naming a real calendar date. It is output as ISO `yyyy-mm-dd`.
7. Field 2, `Concepto`, is kept exactly as the CSV parser returns it
   (after unquoting), with no stripping. It may be empty.
8. Fields 3 and 4, `Importe` and `Saldo` (each after stripping
   surrounding whitespace), use Spanish number format: an optional
   leading `-`, then either plain digits or thousands groups separated
   by `.` (first group 1-3 digits, every later group exactly 3 digits),
   then a decimal comma `,` followed by exactly 1 or 2 decimal digits.
   Examples of valid values: `"1.234,56"`, `"-250,00"`, `"0,5"`,
   `"1234,56"`. Examples of invalid values: `"1.234"` (no decimals),
   `"12,345"` (3 decimals), `"1.23,45"` (bad thousands group),
   `"1,234.56"` (English format), `""` for `Importe`, `"abc"`.
9. Amounts are converted to `Decimal` without `float` (remove the `.`
   thousands separators, replace `,` with `.`) and quantized to exactly
   2 decimal places, so `"0,5"` becomes `Decimal("0.50")` and
   `"1.234,56"` becomes `Decimal("1234.56")`.
10. `Importe` is required: empty raises `ValueError` (rule 5). `Saldo`
    may be empty, in which case the output balance is `None`; a
    non-empty `Saldo` is parsed exactly like `Importe`.
11. `parse_bank_csv` returns one dict per data row, in file order (rows
    are never sorted), each exactly
    `{"date": <ISO string>, "concept": <str>, "amount": <Decimal 2dp>,
    "balance": <Decimal 2dp or None>}`. A text with only a header (and
    possibly blank lines) returns `[]`.
12. `summarize_transactions(transactions)` takes a list as returned by
    `parse_bank_csv`. It must be a list of dicts each with a finite
    `Decimal` `"amount"` and a string `"date"`, otherwise `ValueError`
    is raised. It returns exactly `{"count": int, "credits": D2,
    "debits": D2, "net": D2, "first_date": <str or None>,
    "last_date": <str or None>}` where D2 means `Decimal` quantized to
    `Decimal("0.01")`, `credits` is the sum of all amounts `> 0`,
    `debits` is the sum of all amounts `< 0` kept as a negative total,
    `net` is `credits + debits`, and zero amounts count in `count` but
    in neither sum.
13. `first_date` is the `"date"` of the first row in the given list and
    `last_date` is the `"date"` of the last row in the given list (file
    order, not chronological order). For an empty list: `count` 0,
    `credits`/`debits`/`net` all `Decimal("0.00")`, and both dates
    `None`.
14. Only the stdlib may be used. Never use `float` for the amounts.
15. Example: the row `05/01/2024;Nomina;1.500,00;2.000,00` parses to
    `{"date": "2024-01-05", "concept": "Nomina",
    "amount": Decimal("1500.00"), "balance": Decimal("2000.00")}`.


## Module `task_c.py` — task `spanish_tax_id`

# Spanish tax identifiers (NIF / NIE / CIF)

Implement in `solution.py`:

```python
def classify_spanish_id(text: str) -> str | None
def is_valid_spanish_id(text: str) -> bool
```

Rules (all explicit; the traps are in these details):

1. Normalization (both functions): if `text` is not a `str`,
   `classify_spanish_id` returns `None` and `is_valid_spanish_id`
   returns `False`. Otherwise remove every ASCII space `" "` and every
   hyphen `"-"`, and uppercase the rest. All checks below use the
   normalized text. An empty normalized text is invalid.
2. `classify_spanish_id` returns `"NIF"`, `"NIE"` or `"CIF"` when the
   normalized text is a fully valid identifier of that kind (format
   **and** control character correct), and `None` otherwise.
   `is_valid_spanish_id(text)` is `True` exactly when
   `classify_spanish_id(text)` is not `None`.
3. NIF: exactly 9 characters — 8 digits followed by one uppercase letter
   (the control letter). The control letter must equal
   `"TRWAGMYFPDXBNJZSQVHLCKE"[number % 23]`, where `number` is the
   integer value of the 8 digits. Example: `12345678Z` is a valid NIF
   (12345678 % 23 = 14, and index 14 of the table is `Z`).
4. NIE: exactly 9 characters — one of `X`, `Y`, `Z`, then 7 digits, then
   the control letter. Replace the prefix with `0` for `X`, `1` for `Y`,
   `2` for `Z` to form an 8-digit number, then apply the same mod-23
   letter table as the NIF. Example: `X1234567L` is a valid NIE
   (01234567 % 23 = 19, index 19 is `L`).
5. CIF: exactly 9 characters — an initial letter, then 7 digits, then a
   control character (a digit or a letter). The initial letter must be
   one of `ABCDEFGHJKLMPQRSUVW` (exactly this set).
6. CIF control computation: let `d1..d7` be the 7 digits in order.
   Double the digits in odd positions (`d1, d3, d5, d7`) and sum the
   decimal digits of each double (e.g. `16 -> 1 + 6 = 7`); add the
   even-position digits (`d2, d4, d6`) unchanged. With that `total`,
   the control digit is `(10 - (total % 10)) % 10` and the control
   letter is `"JABCDEFGHI"[control digit]` (digit 0 -> `J`, 1 -> `A`,
   2 -> `B`, ..., 9 -> `I`). Example: `A58818501` is a valid CIF
   (digits `5881850` give control digit 1).
7. CIF control kind by initial letter: initials `A`, `B`, `E`, `H`
   require the control character to be the control **digit**; initials
   `K`, `P`, `Q`, `R`, `S`, `W` require the control **letter**; every
   other allowed initial (`C`, `D`, `F`, `G`, `J`, `L`, `M`, `U`, `V`)
   accepts either the correct digit or the correct letter. A control
   letter outside `A`-`J` can never be correct.
8. Anything that does not fully match one kind — wrong length, digits
   where letters belong or vice versa, a disallowed CIF initial, or a
   wrong control character — is invalid (`None` / `False`). Note that a
   normalized text starting with a digit can only be a NIF, one starting
   with `X`/`Y`/`Z` can only be a NIE, and one starting with any other
   letter can only be a CIF.
9. Use only the stdlib.
