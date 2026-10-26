import pytest

from solution import is_valid_rf_reference, rf_reference


def test_hidden_generate_zero_padded_check():
    # Base "7": numeric "7271500"; 7271500 % 97 = 89; 98 - 89 = 9 -> "09".
    assert rf_reference("7") == "RF097"
    assert is_valid_rf_reference("RF097") is True


def test_hidden_generate_letter_base():
    # Base "A": numeric "10271500"; mod 97 = 73; 98 - 73 = 25.
    assert rf_reference("A") == "RF25A"


def test_hidden_generate_mixed_base():
    # Base "ABC": numeric "101112271500" -> check digits 45.
    assert rf_reference("ABC") == "RF45ABC"
    assert is_valid_rf_reference("RF45ABC") is True


def test_hidden_generate_normalizes_spaces_and_case():
    assert rf_reference(" 5390 0754 7034 ") == "RF18539007547034"
    assert rf_reference("abc") == "RF45ABC"


def test_hidden_generate_max_length_base():
    result = rf_reference("A" * 21)
    assert len(result) == 25
    assert result.startswith("RF")
    assert is_valid_rf_reference(result) is True


def test_hidden_generate_too_long_raises():
    with pytest.raises(ValueError):
        rf_reference("A" * 22)


def test_hidden_generate_bad_characters_raise():
    with pytest.raises(ValueError):
        rf_reference("AB-CD")
    with pytest.raises(ValueError):
        rf_reference("AB!CD")
    with pytest.raises(ValueError):
        rf_reference("   ")


def test_hidden_generate_non_string_raises():
    with pytest.raises(ValueError):
        rf_reference(123)
    with pytest.raises(ValueError):
        rf_reference(None)


def test_hidden_validate_normalizes_spaces_and_case():
    assert is_valid_rf_reference("rf741") is True
    assert is_valid_rf_reference("RF74 1") is True
    assert is_valid_rf_reference("rf18 5390 0754 7034") is True


def test_hidden_validate_wrong_check_digit_variants():
    # Correct check digits for base "1" are 74.
    assert is_valid_rf_reference("RF741") is True
    assert is_valid_rf_reference("RF751") is False
    assert is_valid_rf_reference("RF731") is False


def test_hidden_validate_too_short_and_too_long():
    assert is_valid_rf_reference("RF74") is False
    assert is_valid_rf_reference("RF") is False
    assert is_valid_rf_reference("") is False
    assert is_valid_rf_reference("RF18" + "A" * 22) is False


def test_hidden_validate_wrong_prefix():
    assert is_valid_rf_reference("XX741") is False
    assert is_valid_rf_reference("FR741") is False


def test_hidden_validate_check_positions_must_be_digits():
    assert is_valid_rf_reference("RF7A1") is False
    assert is_valid_rf_reference("RFA41") is False


def test_hidden_validate_non_alphanumeric():
    assert is_valid_rf_reference("RF74-1") is False
    assert is_valid_rf_reference("RF74!") is False


def test_hidden_validate_non_string():
    assert is_valid_rf_reference(None) is False
    assert is_valid_rf_reference(741) is False


def test_hidden_roundtrip_various_bases():
    for base in ("HELLO123", "X9", "42", "539007547034", "Z"):
        generated = rf_reference(base)
        assert generated == "RF" + generated[2:4] + base
        assert is_valid_rf_reference(generated) is True
        # Flipping the last character breaks the checksum.
        replacement = "0" if generated[-1] != "0" else "1"
        assert is_valid_rf_reference(generated[:-1] + replacement) is False
