from decimal import Decimal, InvalidOperation


def _check_groups(int_part: str, sep: str) -> str:
    groups = int_part.split(sep)
    if not (1 <= len(groups[0]) <= 3) or not groups[0].isdigit():
        raise ValueError(f"bad thousands grouping: {int_part!r}")
    for g in groups[1:]:
        if len(g) != 3 or not g.isdigit():
            raise ValueError(f"bad thousands grouping: {int_part!r}")
    return "".join(groups)


def parse_number(text: str) -> Decimal:
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    s = text.strip(" \t\u00a0")
    if not s:
        raise ValueError("empty input")
    negative = False
    if s.startswith("(") or s.endswith(")"):
        if not (s.startswith("(") and s.endswith(")") and len(s) >= 2):
            raise ValueError("unbalanced parentheses")
        inner = s[1:-1].strip(" \t\u00a0")
        if inner.startswith(("+", "-")):
            raise ValueError("sign cannot be combined with parentheses")
        negative = True
        s = inner
    elif s.startswith(("+", "-")):
        negative = s[0] == "-"
        s = s[1:]
    if not s:
        raise ValueError("no digits")
    if s.startswith(("+", "-")) or "(" in s or ")" in s:
        raise ValueError("misplaced sign or parenthesis")
    s = s.replace(" ", "")
    if not s or any(c not in "0123456789.," for c in s):
        raise ValueError(f"invalid characters in {text!r}")
    if not any(c.isdigit() for c in s):
        raise ValueError("no digits")

    has_dot = "." in s
    has_comma = "," in s
    if has_dot and has_comma:
        if s.rfind(".") > s.rfind(","):
            dec_sep, thou_sep = ".", ","
        else:
            dec_sep, thou_sep = ",", "."
        int_part, _, frac_part = s.rpartition(dec_sep)
        if dec_sep in int_part:
            raise ValueError("multiple decimal separators")
        if not int_part or not frac_part or not frac_part.isdigit():
            raise ValueError("bad decimal part")
        int_digits = _check_groups(int_part, thou_sep) if thou_sep in int_part else int_part
        if not int_digits.isdigit():
            raise ValueError("bad integer part")
        normalized = f"{int_digits}.{frac_part}"
    elif has_comma:
        if s.count(",") > 1:
            int_digits = _check_groups(s, ",")
            normalized = int_digits
        else:
            int_part, _, frac_part = s.partition(",")
            if not int_part or not frac_part or not int_part.isdigit() or not frac_part.isdigit():
                raise ValueError("bad comma decimal")
            normalized = f"{int_part}.{frac_part}"
    elif has_dot:
        if s.count(".") > 1:
            int_digits = _check_groups(s, ".")
            normalized = int_digits
        else:
            int_part, _, frac_part = s.partition(".")
            if not int_part or not frac_part or not int_part.isdigit() or not frac_part.isdigit():
                raise ValueError("bad dot decimal")
            normalized = f"{int_part}.{frac_part}"
    else:
        if not s.isdigit():
            raise ValueError("bad integer")
        normalized = s

    try:
        value = Decimal(normalized)
    except InvalidOperation:
        raise ValueError(f"invalid number: {text!r}") from None
    return -value if negative else value
