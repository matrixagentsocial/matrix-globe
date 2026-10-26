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
