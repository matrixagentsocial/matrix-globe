import pytest

from solution import is_valid_rf_reference, rf_reference


def test_public_generate_known_example():
    # ISO 11649 style example: base 539007547034 has check digits 18.
    assert rf_reference("539007547034") == "RF18539007547034"


def test_public_generate_small_base():
    # Numeric "1271500"; 1271500 % 97 = 24; 98 - 24 = 74.
    assert rf_reference("1") == "RF741"


def test_public_validate_generated():
    assert is_valid_rf_reference("RF18539007547034") is True
    assert is_valid_rf_reference(rf_reference("HELLO123")) is True


def test_public_validate_wrong_check_digits():
    assert is_valid_rf_reference("RF751") is False


def test_public_generate_empty_raises():
    with pytest.raises(ValueError):
        rf_reference("")
