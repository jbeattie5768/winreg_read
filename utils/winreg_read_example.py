"""
Simplest Read with WinReg.

* The Win Registry is a series of root keys, each with subkeys and values.
* The root keys we are mostly concerned with at the moment is HKEY_CURRENT_USER.
* Value type is currently always null-terminated strings ('winreg.REG_SZ' == 1) for
* these entries I am getting, ignore it for the moment.
* We wil only be connecting locally, otherwise see `winreg.ConnectRegistry()`.
"""

import winreg

# Open the specified key, returning a handle object.
key_handle = winreg.OpenKeyEx(
    winreg.HKEY_CURRENT_USER,  # Root key
    "Software\\Python\\PythonCore",  # subkey
    access=winreg.KEY_READ,
)  # Default is KEY_READ

# We don't care about returned type at the moment, just worry about the value
dis_value, _ = winreg.QueryValueEx(
    key_handle,  # Key Handle Object
    "DisplayName",
)  # 'DisplayName' is a value in the subkey

uri_value, _ = winreg.QueryValueEx(
    key_handle, "SupportUrl"
)  # 'SupportUrl' is a value in the subkey

print(f"SubKey values: DisplayName='{dis_value}', SupportUrl='{uri_value}'")
