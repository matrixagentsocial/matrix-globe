import re

COUNTRY_LENGTHS = {
    "AD": 24, "AT": 20, "BE": 16, "CH": 21, "DE": 22, "ES": 24,
    "FR": 27, "GB": 22, "IE": 22, "IT": 27, "LU": 20, "NL": 18,
    "NO": 15, "PL": 28, "PT": 25, "SE": 24,
}

_STRUCTURE = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]+$")


def normalize_iban(iban: str) -> str:
    if not isinstance(iban, str):
        raise ValueError("iban must be a string")
    return iban.replace(" ", "").upper()


def validate_iban(iban: str) -> bool:
    if not isinstance(iban, str):
        return False
    code = iban.replace(" ", "")
    if not code:
        return False
    country = code[:2]
    if country not in COUNTRY_LENGTHS:
        return False
    if len(code) != COUNTRY_LENGTHS[country]:
        return False
    if not _STRUCTURE.match(code):
        return False
    rearranged = code[4:] + code[:4]
    digits = ""
    for ch in rearranged:
        if ch.isdigit():
            digits += ch
        else:
            digits += str(ord(ch) - 55)  # A=10 ... Z=35
    return int(digits) % 97 == 1
