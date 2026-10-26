# Parse European / US number formats

Implement in `solution.py`:

```python
def parse_number(text: str) -> Decimal
```

Parse a human-written number and return a `decimal.Decimal`.
Invalid input raises `ValueError`. Rules (all explicit; the traps are
in these details):

1. Strip leading/trailing whitespace (space, tab, non-breaking space
   `"\u00a0"`). Empty after stripping raises `ValueError`.
2. Parentheses: if the stripped text starts with `(` and ends with
   `)`, the number is negative and the parentheses are removed. A
   leading `+`/`-` sign **inside** or outside the parentheses combined
   with parentheses raises `ValueError` (so `"-(1,5)"` and `"(-1,5)"`
   are invalid). Unbalanced parentheses raise `ValueError`.
3. Without parentheses, one optional leading `+` or `-` sign is allowed.
   A sign anywhere else, or two signs, raises `ValueError`.
4. Interior spaces (space and `"\u00a0"`) are thousands separators:
   remove them. Example: `"-1 234,56"` -> `Decimal("-1234.56")`.
   After removal the remaining characters must be digits, `.` or `,`
   only; anything else raises `ValueError`. There must be at least
   one digit.
5. Decimal / thousands separator decision (after sign, parentheses
   and spaces are handled):
   - Both `.` and `,` present: the **rightmost** of the two is the
     decimal separator, the other is the thousands separator.
     `"1.234,56"` -> `1234.56`; `"1,234.56"` -> `1234.56`;
     `"1.234.567,89"` -> `1234567.89`.
   - Only `,` present: if there is more than one `,`, they are
     thousands separators (`"1,234,567"` -> `1234567`). If there is
     exactly one `,`, it is the decimal separator
     (`"1,234"` -> `Decimal("1.234")`, `"12,5"` -> `12.5`).
   - Only `.` present: if there is more than one `.`, they are
     thousands separators (`"1.234.567"` -> `1234567`). If there is
     exactly one `.`, it is the decimal separator
     (`"1.234"` -> `Decimal("1.234")`, `"12.5"` -> `12.5`).
   - Neither present: a plain integer.
6. Thousands grouping is validated whenever a thousands separator is
   used: the first group has 1-3 digits and every later group has
   exactly 3 digits, and the decimal part (if any) has at least 1
   digit. `"12,34,56"`, `"1.23.456"`, `"1,2345.6"` (bad grouping of
   the thousands part) and `"1,234."` raise `ValueError`. A trailing
   or leading decimal separator with no digits on one side (`".5"`
   is allowed only as a decimal with an empty integer part? No:)
   `".5"`, `"5."`, `",5"` and `"5,"` all raise `ValueError`; the
   integer part and the decimal part must both be non-empty.
7. Never use `float`. Use only the stdlib.
