# ISO 11649 RF creditor references

Implement in `solution.py`:

```python
def rf_reference(base: str) -> str
def is_valid_rf_reference(text: str) -> bool
```

Rules (all explicit; the traps are in these details):

1. Generation — normalization: `base` must be a `str`; remove every
   ASCII space `" "` and uppercase the rest (hyphens and other
   characters are **not** removed). A non-string `base` raises
   `ValueError`.
2. Generation — validity: the normalized base must be 1-21 characters
   long and entirely alphanumeric (`A`-`Z`, `0`-`9`). An empty base, a
   base longer than 21 characters, or one containing any other
   character raises `ValueError`.
3. Generation — result: `"RF"` + the 2 check digits + the normalized
   base, so the total length is at most 25. Example:
   `rf_reference("539007547034") == "RF18539007547034"`.
4. Check digits: form the string `base + "RF00"`, convert it to a
   numeric string by replacing each letter with its two-digit value
   (`A=10, B=11, ..., Z=35`) and keeping each digit as-is, interpret it
   as an integer, and take it mod 97. The check digits are
   `98 - (value mod 97)`, formatted as exactly two digits with a
   leading zero when needed (e.g. check 9 is `"09"`).
   Hand example: for base `"1"` the numeric string is
   `"1" + "27" + "15" + "00" = "1271500"`; `1271500 mod 97 = 24`, so
   the check digits are `98 - 24 = 74` and
   `rf_reference("1") == "RF741"`. For base `"7"` the check digits are
   `"09"`, so `rf_reference("7") == "RF097"`.
5. Validation — normalization: if `text` is not a `str`,
   `is_valid_rf_reference` returns `False`. Otherwise remove every
   ASCII space and uppercase the rest.
6. Validation — shape: the normalized text must start with `"RF"`, be
   5-25 characters long in total, be entirely alphanumeric, and the two
   characters after `"RF"` (the check digits) must both be digits.
7. Validation — checksum: moving the first 4 characters (`"RF"` plus the
   check digits) to the end and converting letters as in rule 4 must
   give a number with `mod 97 == 1`. Equivalently, the embedded check
   digits must equal the digits recomputed from the remaining base by
   rule 4; both statements describe the same check and both must hold
   (they always agree when the shape in rule 6 holds).
8. Validation returns `True` only when rules 5-7 all hold, and `False`
   otherwise (never raises). Examples: `is_valid_rf_reference("RF741")`
   is `True`, `is_valid_rf_reference("rf 741")` is `True` (spaces and
   case are normalized), `is_valid_rf_reference("RF751")` is `False`
   (wrong check digits), and `is_valid_rf_reference("RF74")` is `False`
   (too short).
9. Use only the stdlib.
