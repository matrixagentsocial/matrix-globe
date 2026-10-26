from solution import normalize_iban, validate_iban


def test_valid_gb_iban_with_spaces():
    assert validate_iban("GB29 NWBK 6016 1331 9268 19") is True


def test_valid_de_iban():
    assert validate_iban("DE89 3704 0044 0532 0130 00") is True


def test_invalid_checksum():
    assert validate_iban("GB29 NWBK 6016 1331 9268 18") is False


def test_normalize_uppercases_and_strips_spaces():
    assert normalize_iban("gb29 nwbk") == "GB29NWBK"


def test_invalid_wrong_length():
    assert validate_iban("DE89 3704 0044 0532 0130") is False
