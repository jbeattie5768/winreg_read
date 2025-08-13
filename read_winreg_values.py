import argparse
import winreg

MAX_PRINT_TYPE_COL_WIDTH = 17  # Max I've seen is "REG_EXPAND_SZ"
MAX_PRINT_NAME_COL_WIDTH = 24  # Some are >>100 chars
MAX_PRINT_VALUE_COL_WIDTH = None  # Not used, no Limit

REG_TYPE_DICT = {
    0: "REG_NONE",
    1: "REG_SZ",
    2: "REG_EXPAND_SZ",
    3: "REG_BINARY",
    4: "REG_DWORD",  # 4 is also "REG_DWORD_LITTLE_ENDIAN"
    5: "REG_DWORD_BIG_ENDIAN",
    6: "REG_LINK",
    7: "REG_MULTI_SZ",
    8: "REG_RESOURCE_LIST",
    9: "REG_FULL_RESOURCE_DESCRIPTOR",
    10: "REG_RESOURCE_REQUIREMENTS_LIST",
    11: "REG_QWORD",  # 11 is also "REG_QWORD_LITTLE_ENDIAN"
    # xx: Some names have other int values as the Type
}

HKEY_CONST_LIST = [  # https://docs.python.org/3/library/winreg.html#hkey-constants
    winreg.HKEY_CLASSES_ROOT,
    winreg.HKEY_CURRENT_USER,
    winreg.HKEY_LOCAL_MACHINE,
    winreg.HKEY_USERS,
    winreg.HKEY_CURRENT_CONFIG,
]

HKEY_CONST_DICT = {  # https://docs.python.org/3/library/winreg.html#hkey-constants
    winreg.HKEY_CLASSES_ROOT: "HKEY_CLASSES_ROOT",
    winreg.HKEY_CURRENT_USER: "HKEY_CURRENT_USER",
    winreg.HKEY_LOCAL_MACHINE: "HKEY_LOCAL_MACHINE",
    winreg.HKEY_USERS: "HKEY_USERS",
    winreg.HKEY_CURRENT_CONFIG: "HKEY_CURRENT_CONFIG",
    "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
    "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
    "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
    "HKEY_USERS": winreg.HKEY_USERS,
    "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG,
}


def parse_arguments():
    parser = argparse.ArgumentParser()

    # Mandatory
    parser.add_argument(
        "-k", "--key", "--hkey", help="Enter HKey, e.g. 'HKEY_CURRENT_USER'."
    )

    parser.add_argument(
        "-p",
        "--path",
        "--subkey",
        help="Subkey-path to traverse from, e.g. 'Software\\python'",
    )

    return parser.parse_args()


def get_keys(hkey, path):
    """Yield all subkey names under the given HKey and sub-key path."""
    try:
        # Explicitly close handles, otherwise risk of leaks for large traversals
        with winreg.OpenKey(hkey, path) as key:
            index = 0
            while True:
                try:
                    yield winreg.EnumKey(key, index)
                    index += 1
                except OSError:  # Expected when no more keys to yield
                    break

    except FileNotFoundError as err:
        msg = f"\n{path} is not a valid path"
        raise FileNotFoundError(msg) from err
    except PermissionError as err:
        print(f"{err}: Permission Error: you may need to run the script as Admin.")


def get_values(hkey, path):
    """Yield all (name, value, type) tuples for values under the given HKey and sub-key path."""
    try:
        # Explicitly close handles, otherwise risk of leaks for large traversals
        with winreg.OpenKey(hkey, path) as key:
            index = 0
            while True:
                try:
                    yield winreg.EnumValue(key, index)
                    index += 1
                except OSError:  # Expected when no more values to yield
                    break

    except FileNotFoundError as err:
        msg = f"\n{path} is not a valid path"
        raise FileNotFoundError(msg) from err
    except PermissionError as err:
        print(f"{err}: Permission Error: you may need to run the script as Admin.")


def _check_root_key(hkey):
    """
    Check Valid HKEY.

    Only the following predefined Win Reg keys are supported:
        HKEY_CLASSES_ROOT
        HKEY_CURRENT_USER
        HKEY_LOCAL_MACHINE
        HKEY_USERS
        HKEY_CURRENT_CONFIG

    See: https://learn.microsoft.com/en-us/windows/win32/sysinfo/predefined-keys
    See: https://docs.python.org/3/library/winreg.html#hkey-constants

    Args:
        hkey: One of 3 possible types:
            1. A valid WinReg HKEY_* Constant
                e.g. winreg.HKEY_CLASSES_ROOT
            2. The int representation of a WinReg HKEY_* Constant
                e.g. 18446744071562067968
            3. A string of the HKEY constant name
                e.g. 'HKEY_CLASSES_ROOT'
    Return:
        A valid WinReg HKEY as an int

    """
    if hkey is None:
        raise TypeError("None is not a valid type")  # noqa: TRY003, EM101

    # As an int, or a winreg.HKEY_* constant
    if isinstance(hkey, int):
        if hkey >= 2**64:  # 64K limit for total size of all values of a key
            raise OverflowError("The int too big to convert")  # noqa: TRY003, EM101
        if hkey not in HKEY_CONST_LIST:
            raise TypeError("The int is not a valid winreg.HKEY_* type")  # noqa: TRY003, EM101

    # If it's a string, try and make it a winreg.HKEY_* constant
    if isinstance(hkey, str):
        try:
            hkey = HKEY_CONST_DICT[
                hkey
            ]  # Alternatively use getattr(winreg, hkey) & AttributeError
        except KeyError as err:
            raise TypeError("The string is not a HKEY_* string") from err  # noqa: TRY003, EM101

    return hkey


def traverse_winreg_for_values(root_hkey, subkey_path):
    r"""
    Get Windows Registry Values.

    Traverses the Windows Registry printing the Key:Value
    pairs.

    Args:
        root_hkey:
            One of:
                1. The predefined winreg.HKEY_* constants
                    e.g. winreg.HKEY_CURRENT_USER
                2. A string representation of the HKEY Constant
                    e.g. "HKEY_CURRENT_USER"
                3. The integer representation of the winreg.HKEY_* constant
                    e.g. 18446744071562067968

        subkey_path:
            A string that identifies the key path to start traversing from.
            Examples are:
                r'Software\Python'
                r'Software\Python\PythonCore'
                r'SYSTEM\Keyboard Layout'

            The exact subkey-path will be dependent on root_hkey
            passed and your Windows platform.

    """

    # ######################################
    # Internal function to get and print the
    # Key:Value pairs for a given key-path as
    # spaced cols:
    #   Type         Name         Value
    #
    def _print_values_for_path_key(root_hkey, path):
        for name, value, type in get_values(root_hkey, path):
            if not name:
                # '(Default)' entries with a Value are not named
                name = "(Default)"  # ...so name it

            print(  # Show the Type if possible, otherwise use what the reg returns
                f"\t{REG_TYPE_DICT.get(type, str(type)):<{MAX_PRINT_TYPE_COL_WIDTH}}",
                f"{name:<{MAX_PRINT_NAME_COL_WIDTH}}",
                f"{value}",
            )

    # ######################################
    # Check passed args
    root_hkey = _check_root_key(root_hkey)
    path = subkey_path.title()  # Follow Win Reg convention
    # Not exact, but close enough

    # ######################################
    # Main Functionality
    print(f"\nComputer\\{HKEY_CONST_DICT[root_hkey]}\\{path}")

    _print_values_for_path_key(root_hkey, path)

    # Iterate through any subkeys on this upper path
    for subkey in get_keys(root_hkey, path):
        # Update path, or handle no path ("") case
        sub_path = f"{path}\\{subkey}" if path else subkey
        print(f"\nComputer\\{HKEY_CONST_DICT[root_hkey]}\\{sub_path}")

        _print_values_for_path_key(root_hkey, sub_path)

        try:
            # Recurse into any lower subkeys under the current subkey
            for sub_subkey in get_keys(root_hkey, sub_path):
                traverse_winreg_for_values(root_hkey, f"{sub_path}\\{sub_subkey}")

        except RecursionError as err:  # This should not happen, but....
            print(err)


def walk_winreg():
    """Script Main Function."""
    args = parse_arguments()

    # Error checking on passed args done in function
    traverse_winreg_for_values(args.key, args.path)


if __name__ == "__main__":
    walk_winreg()
