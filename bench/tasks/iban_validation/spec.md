# IBAN validation (mod-97, country lengths)

Implement in `solution.py`:

```python
def validate_iban(iban: str) -> bool
def normalize_iban(iban: str) -> str
```

Rules (all explicit; the traps are in these details):

1. `normalize_iban` removes **all** spaces (only the ASCII space
   `" "`; other characters are kept) and uppercases the result.
   Example: `"gb29 nwbk"` -> `"GB29NWBK"`. It does not validate.
2. `validate_iban` first normalizes as above, then returns `True` only
   if **all** of these hold, and `False` otherwise. It never raises for
   a malformed string (empty, wrong characters, wrong length, bad
   checksum all return `False`):
   - Total length matches the country table exactly:
     `AD 24, AT 20, BE 16, CH 21, DE 22, ES 24, FR 27, GB 22, IE 22,
     IT 27, LU 20, NL 18, NO 15, PL 28, PT 25, SE 24`.
     A country code not in this table returns `False`.
   - Structure: characters 1-2 are letters `A-Z` (country), characters
     3-4 are digits (check digits), and the remaining BBAN characters
     are alphanumeric `A-Z`/`0-9` only. Any other character (including
     `-`, `_`, tabs left after space removal) returns `False`.
   - Mod-97: move the first 4 characters to the end, convert letters
     to numbers (`A=10` ... `Z=35`), interpret the whole digit string
     as an integer, and require `value % 97 == 1`.
3. Inputs that are not strings raise `ValueError` in `normalize_iban`
   and return `False` in `validate_iban`.
4. Leading/trailing spaces are just spaces: they are removed like any
   other space. An IBAN that is valid with spaces is valid without.
5. Use only the stdlib.
