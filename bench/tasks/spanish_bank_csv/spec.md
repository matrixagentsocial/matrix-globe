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
