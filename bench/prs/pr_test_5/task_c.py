def _normalize(text):
    return text.replace(" ", "").upper()


def _is_alnum(text):
    return all(
        ("A" <= char <= "Z") or ("0" <= char <= "9") for char in text
    )


def _numeric_value(text):
    pieces = []
    for char in text:
        if "0" <= char <= "9":
            pieces.append(char)
        else:
            pieces.append(str(ord(char) - ord("A") + 10))
    return int("".join(pieces))


def _check_digits(base):
    remainder = _numeric_value(base + "RF00") % 97
    return f"{98 - remainder:02d}"


def rf_reference(base: str) -> str:
    if not isinstance(base, str):
        raise ValueError("base must be a string")
    normalized = _normalize(base)
    if not 1 <= len(normalized) <= 21 or not _is_alnum(normalized):
        raise ValueError("base must be 1-21 alphanumeric characters")
    return "RF" + _check_digits(normalized) + normalized


def is_valid_rf_reference(text: str) -> bool:
    if not isinstance(text, str):
        return False
    normalized = _normalize(text)
    if not normalized.startswith("RF"):
        return False
    if not 5 <= len(normalized) <= 25:
        return False
    if not _is_alnum(normalized):
        return False
    if not all("0" <= char <= "9" for char in normalized[2:4]):
        return False
    # Check 1: rearranged (first 4 chars moved to the end) mod 97 == 1.
    rearranged = normalized[4:] + normalized[:4]
    if _numeric_value(rearranged) % 97 != 1:
        return False
    # Check 2: embedded check digits match recomputation from the base.
    return normalized[2:4] == _check_digits(normalized[4:])
