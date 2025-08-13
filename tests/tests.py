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


def test_get_keys_permission_error():
    with patch(
        "read_winreg_values.winreg.OpenKey",
        side_effect=PermissionError("Access denied"),
    ):
        with patch("builtins.print") as mock_print:
            # Should not yield any keys, just print the error
            result = list(
                read_winreg_values.get_keys(
                    read_winreg_values.winreg.HKEY_CURRENT_USER, "some\\path"
                )
            )
            assert result == []
            mock_print.assert_called_once()
            assert "Permission Error" in mock_print.call_args[0][0]


def test_get_values_permission_error():
    with patch(
        "read_winreg_values.winreg.OpenKey",
        side_effect=PermissionError("Access denied"),
    ):
        with patch("builtins.print") as mock_print:
            # Should not yield any values, just print the error
            result = list(
                read_winreg_values.get_values(
                    read_winreg_values.winreg.HKEY_CURRENT_USER, "some\\path"
                )
            )
            assert result == []
            mock_print.assert_called_once()
            assert "Permission Error" in mock_print.call_args[0][0]


def test_get_winreg_values_simple(monkeypatch):
    def fake_get_keys(h, p):
        if p == "Software\\Test":
            return iter(["Subkey"])
        else:
            return iter([])

    def fake_get_values(h, p):
        if p.endswith("Subkey"):
            return iter([("name2", "val2", "type2")])
        else:
            return iter([("name1", "val1", "type1")])

    monkeypatch.setattr(read_winreg_values, "get_keys", fake_get_keys)

    monkeypatch.setattr(read_winreg_values, "get_values", fake_get_values)

    # Patch print to capture output
    # Only testing the print statements really
    with patch("builtins.print") as mock_print:
        read_winreg_values.traverse_winreg_for_values(
            read_winreg_values.winreg.HKEY_CURRENT_USER, "Software\\Test"
        )

        # Check that print was called for each key and value
        # Using a multi-line print in the code, with defined
        # spacing as well, is not making this any easier
        calls = [
            call("\nComputer\\HKEY_CURRENT_USER\\Software\\Test"),
            call("\ttype1            ", "name1                   ", "val1"),
            call("\nComputer\\HKEY_CURRENT_USER\\Software\\Test\\Subkey"),
            call("\ttype2            ", "name2                   ", "val2"),
        ]

        mock_print.assert_has_calls(calls, any_order=False)


def test_get_winreg_values_recursion(monkeypatch):
    def fake_get_keys(h, p):
        if p == "Root":
            return iter(["Sub1"])
        elif p == "Root\\Sub1":
            return iter(["Sub2"])
        else:
            return iter([])

    def fake_get_values(h, p):
        return iter([(p, "value", 1)])

    monkeypatch.setattr(read_winreg_values, "get_keys", fake_get_keys)

    monkeypatch.setattr(read_winreg_values, "get_values", fake_get_values)

    # Patch print to capture output
    # Only testing the print statements really
    with patch("builtins.print") as mock_print:
        breakpoint
        read_winreg_values.traverse_winreg_for_values(
            read_winreg_values.winreg.HKEY_CURRENT_USER, "Root"
        )

        # Check that print was called for each key and value
        # Using a multi-line print in the code, with defined
        # spacing as well, is not making this any easier
        expected = [
            call("\nComputer\\HKEY_CURRENT_USER\\Root"),
            call("\tREG_SZ           ", "Root                    ", "value"),
            call("\nComputer\\HKEY_CURRENT_USER\\Root\\Sub1"),
            call("\tREG_SZ           ", "Root\\Sub1               ", "value"),
            call("\nComputer\\HKEY_CURRENT_USER\\Root\\Sub1\\Sub2"),
            call("\tREG_SZ           ", "Root\\Sub1\\Sub2          ", "value"),
        ]

        mock_print.assert_has_calls(expected, any_order=False)
