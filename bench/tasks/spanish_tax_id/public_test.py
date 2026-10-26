from solution import classify_spanish_id, is_valid_spanish_id


def test_public_nif_valid():
    assert classify_spanish_id("12345678Z") == "NIF"
    assert is_valid_spanish_id("12345678Z") is True


def test_public_nie_valid():
    assert classify_spanish_id("X1234567L") == "NIE"


def test_public_cif_valid():
    assert classify_spanish_id("A58818501") == "CIF"


def test_public_wrong_control_letter_invalid():
    assert classify_spanish_id("12345678A") is None
    assert is_valid_spanish_id("12345678A") is False


def test_public_lowercase_and_spaces_normalized():
    assert classify_spanish_id("1234 5678 z") == "NIF"
