from solution import classify_spanish_id, is_valid_spanish_id


def test_hidden_nif_zero_number():
    # 0 % 23 = 0 -> 'T'.
    assert classify_spanish_id("00000000T") == "NIF"


def test_hidden_nif_wrong_letter():
    assert classify_spanish_id("12345678A") is None
    assert is_valid_spanish_id("12345678A") is False


def test_hidden_nie_y_prefix():
    # Y -> 1: 11234567 % 23 = 10 -> 'X'.
    assert classify_spanish_id("Y1234567X") == "NIE"


def test_hidden_nie_z_prefix():
    # Z -> 2: 21234567 % 23 = 1 -> 'R'.
    assert classify_spanish_id("Z1234567R") == "NIE"


def test_hidden_nie_wrong_letter():
    assert classify_spanish_id("X1234567A") is None


def test_hidden_nie_lowercase_hyphens():
    assert classify_spanish_id("x-1234567-l") == "NIE"


def test_hidden_cif_digit_required_valid_and_wrong():
    # Digits 1234567: odd doubles 2+6+1+5, evens 2+4+6, total 26,
    # control digit 4, control letter 'D'. A requires the digit.
    assert classify_spanish_id("A12345674") == "CIF"
    assert classify_spanish_id("A1234567D") is None
    assert classify_spanish_id("A12345675") is None


def test_hidden_cif_letter_required():
    # P requires the control letter 'D' for digits 1234567.
    assert classify_spanish_id("P1234567D") == "CIF"
    assert classify_spanish_id("P12345674") is None


def test_hidden_cif_either_accepted():
    # C accepts either the correct digit or the correct letter.
    assert classify_spanish_id("C12345674") == "CIF"
    assert classify_spanish_id("C1234567D") == "CIF"
    assert classify_spanish_id("C1234567E") is None
    assert classify_spanish_id("C12345675") is None


def test_hidden_cif_given_example_wrong_control():
    assert classify_spanish_id("A58818501") == "CIF"
    assert classify_spanish_id("A58818502") is None
    assert classify_spanish_id("A5881850A") is None


def test_hidden_cif_zero_control_digit_and_letter():
    # Digits 0000000 give total 0, control digit 0, control letter 'J'.
    assert classify_spanish_id("A00000000") == "CIF"
    assert classify_spanish_id("P0000000J") == "CIF"
    assert classify_spanish_id("A0000000J") is None


def test_hidden_cif_disallowed_initials():
    # I, N, O and T are not in ABCDEFGHJKLMPQRSUVW.
    for text in ("I12345674", "N12345674", "O12345674", "T12345674"):
        assert classify_spanish_id(text) is None
        assert is_valid_spanish_id(text) is False


def test_hidden_wrong_lengths():
    assert classify_spanish_id("1234567Z") is None
    assert classify_spanish_id("12345678") is None
    assert classify_spanish_id("123456789Z") is None
    assert classify_spanish_id("X123456L") is None


def test_hidden_bad_characters():
    assert classify_spanish_id("123456789") is None  # control must be a letter
    assert classify_spanish_id("1234567*Z") is None
    assert classify_spanish_id("ABCDEFGHI") is None


def test_hidden_non_string_inputs():
    assert classify_spanish_id(None) is None
    assert classify_spanish_id(12345678) is None
    assert is_valid_spanish_id(None) is False
    assert is_valid_spanish_id(12345678) is False


def test_hidden_empty_and_blank():
    assert classify_spanish_id("") is None
    assert classify_spanish_id("   ") is None
    assert classify_spanish_id("---") is None
    assert is_valid_spanish_id("") is False


def test_hidden_spaces_and_hyphens_normalized():
    assert classify_spanish_id("1234-5678-Z") == "NIF"
    assert classify_spanish_id("A 5881850 1") == "CIF"
    assert is_valid_spanish_id(" x1234567l ") is True
