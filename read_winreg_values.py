# Win Reg mentioned in UV documentation:
# https://docs.astral.sh/uv/concepts/python-versions/#registration-in-the-windows-registry
#
# There is some sample code in PeP 514, but it did not work:
# https://peps.python.org/pep-0514/#sample-code
#
# Instead I came up with my own based on the Python winreg module.
#

import sys
import winreg

MAX_PRINT_COL_WIDTH = 24  # 2nd column value data alignment

# https://docs.python.org/3/library/winreg.html#hkey-constants
valid_root_hkeys = {
    "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
    "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
    "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
    "HKEY_USERS": winreg.HKEY_USERS,
    "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG,
}


def list_all_subkey_values(hkey, subkey=""):
    """
    List all the values within a given registry subkey.

    Args:
        hkey: The Registry Root Entry Key. Either a string or HKey object (Hive)
            Strings are validated via validate_root_key() function and should be one of the following:
                "HKEY_CLASSES_ROOT"
                "HKEY_CURRENT_USER"
                "HKEY_LOCAL_MACHINE"
                "HKEY_USERS"
                "HKEY_CURRENT_CONFIG"
        subkey: Subkey from which to start recursively from.

    """
    if isinstance(hkey, str):  # Otherwise its an HKey Object
        print(f"Computer\\\\{hkey.upper()}\\\\")
        hkey = validate_root_key(hkey)
    try:
        key = winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ)
        print(f"\t{subkey}")
        i = 0
        while True:
            try:
                value_name, value_data, _ = winreg.EnumValue(key, i)

                if value_name:
                    print(f"\t\t{value_name:<{MAX_PRINT_COL_WIDTH}}{value_data}")
                else:
                    print(f"\t\t{'Default':<{MAX_PRINT_COL_WIDTH}}{value_data}")
                i += 1
            except OSError:  # Catch OSError when EnumValue runs out of values
                break
        winreg.CloseKey(key)
        print()  # Newline for better readability
    except FileNotFoundError:
        print(f"Registry key not found: {subkey}")


def list_all_subkey_values_recursive(hkey, subkey=""):
    """
    Recursively list all subkeys under a given registry path starting point.

    Args:
        hkey: The Registry Root Entry Key. Either a string or HKey object (Hive)
        Strings are validated via validate_root_key() function and should be one of the following:
            "HKEY_CLASSES_ROOT"
            "HKEY_CURRENT_USER"
            "HKEY_LOCAL_MACHINE"
            "HKEY_USERS"
            "HKEY_CURRENT_CONFIG"

        subkey: Subkey from which to start recursively from.

    """
    if isinstance(hkey, str):  # Otherwise its an HKey Object
        print(f"Computer\\\\{hkey.upper()}\\\\")
        hkey = validate_root_key(hkey)

    try:
        with winreg.OpenKeyEx(hkey, subkey, 0, winreg.KEY_READ) as key:
            list_all_subkey_values(hkey, subkey)

            # Enumerate subkeys at the current level
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    full_subkey_path = (
                        f"{subkey}\\{subkey_name}" if subkey else subkey_name
                    )

                    # Recursively call the function for each subkey
                    list_all_subkey_values_recursive(hkey, full_subkey_path)
                    i += 1
                except OSError:  # Catch OSError when EnumValue runs out of values
                    break
    except FileNotFoundError:
        print(f"Registry key not found: {subkey}")


def list_all_subkey_recursive(hkey, subkey=""):
    """
    Recursively list all subkeys under a given registry path starting point.

    Args:
        hkey: The Registry Root Entry Key. Either a string or HKey object (Hive)
            Strings are validated via validate_root_key() function and should be one of the following:
                "HKEY_CLASSES_ROOT"
                "HKEY_CURRENT_USER"
                "HKEY_LOCAL_MACHINE"
                "HKEY_USERS"
                "HKEY_CURRENT_CONFIG"
        subkey: Subkey from which to start recursively from.

    """
    if isinstance(hkey, str):  # Otherwise its an HKey Object
        print(f"Computer\\\\{hkey.upper()}\\\\")
        hkey = validate_root_key(hkey)

    try:
        with winreg.OpenKeyEx(hkey, subkey, 0, winreg.KEY_READ) as key:
            # Enumerate subkeys at the current level
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    full_subkey_path = (
                        f"{subkey}\\{subkey_name}" if subkey else subkey_name
                    )
                    print(f"\t{full_subkey_path}")
                    # Recursively call the function for each subkey
                    list_all_subkey_recursive(hkey, full_subkey_path)
                    i += 1
                except OSError:  # Catch OSError when EnumValue runs out of values
                    break
    except FileNotFoundError:
        print(f"Registry key not found: {subkey}")


def validate_root_key(root_hkey):
    """
    Validates the root key against known valid root keys.

    Args:
        root_hkey (str): The root key to validate.

    Returns:
        winreg.HKEY_*: The corresponding HKEY constant if valid.

    Raises:
        KeyError: If the provided root_hkey str is not valid.

    """
    try:
        return valid_root_hkeys[root_hkey.upper()]
    except KeyError:
        print(
            f"Invalid root key: {root_hkey}.",
            f"\nMust be one of: {', '.join(valid_root_hkeys.keys())}",
        )
        sys.exit(1)


if __name__ == "__main__":
    initial_path = r"software\\python"
    # initial_path = r"Software\\Google"
    # Convert to POSIX path and Title case for consistency
    initial_path = initial_path.replace(r"/", "\\\\").title()

    for this_root_hkey in ["HKEY_CURRENT_USER", "HKEY_LOCAL_MACHINE"]:
        print(f"\n{'':#^50}\n")

        # list_all_subkey_recursive(this_root_hkey, initial_path)
        # list_all_subkey_values(
        #     this_root_hkey, "Software\\Python\\PythonCore\\"
        # )  # No recursion
        list_all_subkey_values_recursive(this_root_hkey, initial_path)
