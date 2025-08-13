from unittest.mock import MagicMock, call, patch

import pytest

import read_winreg_values


@pytest.mark.parametrize(
    "type",
    [read_winreg_values.winreg.HKEY_CURRENT_USER, "HKEY_CURRENT_USER"],
)
def test_check_root_key_valid(type):
    assert (
        read_winreg_values._check_root_key(type)
        == read_winreg_values.winreg.HKEY_CURRENT_USER
    )


@pytest.mark.parametrize(
    "type",
    [None, 12345678901234567890, "INVALID_KEY"],
)
def test_check_root_key_invalid(type):
    with pytest.raises(TypeError):
        read_winreg_values._check_root_key(type)


@pytest.mark.parametrize(
    "type",
    [2**64 + 1],
)
def test_check_root_key_overflow(type):
    with pytest.raises(OverflowError):
        read_winreg_values._check_root_key(type)


def test_get_keys_yields_keys():
    with patch("read_winreg_values.winreg.OpenKey") as mock_openkey:
        mock_key = MagicMock()
        mock_openkey.return_value.__enter__.return_value = mock_key
        mock_key.__enter__.return_value = mock_key
        mock_key.__exit__.return_value = False
        with patch(
            "read_winreg_values.winreg.EnumKey", side_effect=["sub1", "sub2", OSError]
        ):
            keys = list(
                read_winreg_values.get_keys(
                    read_winreg_values.winreg.HKEY_CURRENT_USER, "Some\\Path"
                )
            )
            assert keys == ["sub1", "sub2"]


def test_get_values_yields_values():
    with patch("read_winreg_values.winreg.OpenKey") as mock_openkey:
        mock_key = MagicMock()
        mock_openkey.return_value.__enter__.return_value = mock_key
        with patch(
            "read_winreg_values.winreg.EnumValue",
            side_effect=[("name", "val", 1), OSError],
        ):
            values = list(
                read_winreg_values.get_values(
                    read_winreg_values.winreg.HKEY_CURRENT_USER, "Some\\Path"
                )
            )
            assert values == [("name", "val", 1)]


def test_get_keys_file_not_found():
    with patch("read_winreg_values.winreg.OpenKey", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            list(
                read_winreg_values.get_keys(
                    read_winreg_values.winreg.HKEY_CURRENT_USER, "bad\\path"
                )
            )


def test_get_values_file_not_found():
    with patch("read_winreg_values.winreg.OpenKey", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            list(
                read_winreg_values.get_values(
                    read_winreg_values.winreg.HKEY_CURRENT_USER, "bad\\path"
                )
            )


def test_get_winreg_values_simple(monkeypatch):
    # Mock get_keys to return one subkey, then no sub-subkeys
    # Only testing the print statements really
    monkeypatch.setattr(read_winreg_values, "get_keys", lambda h, p: iter(["subkey"]))

    # Mock get_values to return one value for each key
    def fake_get_values(h, p):
        if p.endswith("subkey"):
            return iter([("name2", "val2", 1)])
        else:
            return iter([("name1", "val1", 1)])

    monkeypatch.setattr(read_winreg_values, "get_values", fake_get_values)
    # Patch print to capture output
    with patch("builtins.print") as mock_print:
        read_winreg_values.get_winreg_values(
            read_winreg_values.winreg.HKEY_CURRENT_USER, "Software\\Test"
        )
        # Check that print was called with expected values
        calls = [
            call("\nSoftware\\Test"),
            call("\tname1                   val1"),
            call("\nSoftware\\Test\\subkey"),
            call("\tname2                   val2"),
        ]
        mock_print.assert_has_calls(calls, any_order=False)


def test_get_winreg_values_recursion(monkeypatch):
    # Simulate a tree: root -> sub1 -> sub2
    # Only testing the print statements really
    def fake_get_keys(h, p):
        if p == "Root":
            return iter(["Sub1"])
        elif p == "Root\\Sub1":
            return iter(["Sub2"])
        else:
            return iter([])

    monkeypatch.setattr(read_winreg_values, "get_keys", fake_get_keys)

    # Simulate values at each level
    def fake_get_values(h, p):
        return iter([(p, "value", 1)])

    monkeypatch.setattr(read_winreg_values, "get_values", fake_get_values)
    with patch("builtins.print") as mock_print:
        breakpoint
        read_winreg_values.get_winreg_values(
            read_winreg_values.winreg.HKEY_CURRENT_USER, "Root"
        )
        # Check that print was called for each key and value
        expected = [
            call("\nRoot"),
            call("\tRoot                    value"),
            call("\nRoot\\Sub1"),
            call("\tRoot\\Sub1               value"),
            call("\nRoot\\Sub1\\Sub2"),
            call("\tRoot\\Sub1\\Sub2          value"),
        ]
        mock_print.assert_has_calls(expected, any_order=False)
