import pytest

from solution import normalize_iban, validate_iban


def test_hidden_valid_fr_iban():
    assert validate_iban("FR14 2004 1010 0505 0001 3M02 606") is True


def test_hidden_valid_es_iban():
    assert validate_iban("ES91 2100 0418 4502 0005 1332") is True


def test_hidden_valid_it_iban():
    assert validate_iban("IT60 X054 2811 1010 0000 0123 456") is True


def test_hidden_valid_nl_iban():
    assert validate_iban("NL91 ABNA 0417 1643 00") is True


def test_hidden_valid_be_iban():
    assert validate_iban("BE68 5390 0754 7034") is True


def test_hidden_valid_ch_iban():
    assert validate_iban("CH93 0076 2011 6238 5295 7") is True


def test_hidden_valid_no_iban():
    assert validate_iban("NO93 8601 1117 947") is True


def test_hidden_lowercase_valid():
    assert validate_iban("gb29 nwbk 6016 1331 9268 19") is True


def test_hidden_no_spaces_valid():
    assert validate_iban("DE89370400440532013000") is True


def test_hidden_leading_trailing_spaces():
    assert validate_iban("  GB29 NWBK 6016 1331 9268 19  ") is True


def test_hidden_bad_check_digits():
    assert validate_iban("DE88 3704 0044 0532 0130 00") is False


def test_hidden_unknown_country():
    assert validate_iban("US29 NWBK 6016 1331 9268 19") is False


def test_hidden_dashes_rejected():
    assert validate_iban("GB29-NWBK-6016-1331-9268-19") is False


def test_hidden_empty_rejected():
    assert validate_iban("") is False
    assert validate_iban("   ") is False


def test_hidden_letter_in_check_digits():
    assert validate_iban("GB2A NWBK 6016 1331 9268 19") is False


def test_hidden_gb_too_long():
    assert validate_iban("GB29 NWBK 6016 1331 9268 199") is False


def test_hidden_non_string_returns_false():
    assert validate_iban(None) is False
    assert validate_iban(12345) is False


def test_hidden_normalize_non_string_raises():
    with pytest.raises(ValueError):
        normalize_iban(None)


def test_hidden_swapped_digits_invalid():
    # Valid DE IBAN with two BBAN digits swapped must fail mod-97.
    assert validate_iban("DE89 3704 0044 0532 0130 01") is False
