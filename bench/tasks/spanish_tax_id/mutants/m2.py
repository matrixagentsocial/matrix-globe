_LETTER_TABLE = "TRWAGMYFPDXBNJZSQVHLCKE"
_CIF_INITIALS = set("ABCDEFGHJKLMPQRSUVW")
_CIF_DIGIT_ONLY = set("ABEH")
_CIF_LETTER_ONLY = set("KPQRSW")
_CIF_CONTROL_LETTERS = "ABCDEFGHIJ"


def _normalize(text):
    if not isinstance(text, str):
        return None
    return text.replace(" ", "").replace("-", "").upper()


def _mod23_letter(number):
    return _LETTER_TABLE[number % 23]


def _is_digits(text):
    return all(char in "0123456789" for char in text)


def _is_upper_letter(char):
    return "A" <= char <= "Z"


def _classify_nif(text):
    if len(text) != 9 or not _is_digits(text[:8]) or not _is_upper_letter(text[8]):
        return None
    if text[8] == _mod23_letter(int(text[:8])):
        return "NIF"
    return None


def _classify_nie(text):
    prefixes = {"X": "0", "Y": "1", "Z": "2"}
    if (
        len(text) != 9
        or text[0] not in prefixes
        or not _is_digits(text[1:8])
        or not _is_upper_letter(text[8])
    ):
        return None
    number = int(prefixes[text[0]] + text[1:8])
    if text[8] == _mod23_letter(number):
        return "NIE"
    return None


def _cif_control(digits):
    total = 0
    for index, char in enumerate(digits):
        value = int(char)
        if index % 2 == 0:  # d1, d3, d5, d7 (1-based odd positions)
            doubled = value * 2
            total += doubled // 10 + doubled % 10
        else:
            total += value
    control_digit = (10 - (total % 10)) % 10
    return control_digit, _CIF_CONTROL_LETTERS[control_digit]


def _classify_cif(text):
    if (
        len(text) != 9
        or text[0] not in _CIF_INITIALS
        or not _is_digits(text[1:8])
    ):
        return None
    control_digit, control_letter = _cif_control(text[1:8])
    control = text[8]
    if text[0] in _CIF_DIGIT_ONLY:
        ok = control == str(control_digit)
    elif text[0] in _CIF_LETTER_ONLY:
        ok = control == control_letter
    else:
        ok = control == str(control_digit) or control == control_letter
    return "CIF" if ok else None


def classify_spanish_id(text: str) -> str | None:
    normalized = _normalize(text)
    if not normalized:
        return None
    if _is_digits(normalized[0]):
        return _classify_nif(normalized)
    if normalized[0] in "XYZ":
        return _classify_nie(normalized)
    return _classify_cif(normalized)


def is_valid_spanish_id(text: str) -> bool:
    return classify_spanish_id(text) is not None
