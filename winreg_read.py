import argparse
import winreg

MAX_PRINT_TYPE_COL_WIDTH = 17  # Some will be truncated
MAX_PRINT_NAME_COL_WIDTH = 24  # Some are >>100 chars
MAX_PRINT_VALUE_COL_WIDTH = None  # Not used, no Limit imposed

REG_TYPE_DICT = {  # https://docs.python.org/3/library/winreg.html#value-types
    # "REG_UNKNOWN" is used for Types other than these
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


def _parse_arguments():
    parser = argparse.ArgumentParser(
        description="Traverse Windows Registry and Print the Values",
    )

    # Positional
    parser.add_argument(
        "key",
        metavar="HKey",
        type=str,
        help="Enter HKey, e.g. 'HKEY_CURRENT_USER'",
    )

    parser.add_argument(
        "path",
        metavar="Key-Path",
        type=str,
        help="Subkey-Path to traverse from, e.g. 'Software\\python'",
    )

    # Optional
    parser.add_argument(
        "-e",
        "--exclude",
        nargs="*",
        help="""List of Key-Paths to exclude from being traversed, i.e. ignored.
                Expected to be '-e 'path1' 'path2' 'pathn''
                """,
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

    Any HKEY_CONST_DICT entry:
        'winreg.HKEY_*' constant
        'HKEY_*' string constant

    See: https://learn.microsoft.com/en-us/windows/win32/sysinfo/predefined-keys
    See: https://docs.python.org/3/library/winreg.html#hkey-constants

    Args:
        hkey: One of 3 possible types:
            1. A valid 'winreg.HKEY_*' constant
                e.g. 'winreg.HKEY_CLASSES_ROOT'
            2. The int representation of a 'winreg.HKEY_*' constant
                e.g. 18446744071562067968
            3. A string of the 'HKEY_*' constant name
                e.g. 'HKEY_CLASSES_ROOT'
    Return:
        A valid 'winreg.HKEY_*' constant (which is really a 2^64 int).

    """
    if hkey is None:
        raise TypeError("None is not a valid type")  # noqa: TRY003, EM101

    # As an int, or a 'winreg.HKEY_*' constant
    if isinstance(hkey, int):
        if hkey not in HKEY_CONST_LIST:
            raise TypeError("The int is not a valid 'winreg.HKEY_*' constant")  # noqa: TRY003, EM101

    # As a string, convert to a 'winreg.HKEY_*' constant
    if isinstance(hkey, str):
        try:
            hkey = HKEY_CONST_DICT[
                hkey
            ]  # Alternatively use getattr(winreg, hkey) & AttributeError
        except KeyError as err:
            raise TypeError("The string is not a valid 'HKEY_*' string") from err  # noqa: TRY003, EM101

    return hkey


def traverse_winreg_for_values(root_hkey, subkey_path, exclude_keys):
    r"""
    Get Windows Registry Values.

    Traverses the Windows Registry printing the Key:Value
    pairs for the passed HKEY and Subkey-Path.

    Args:
        root_hkey:
            One of 3 possible types:
                1. A valid 'winreg.HKEY_*' constant
                    e.g. 'winreg.HKEY_CLASSES_ROOT'
                2. The int representation of a 'winreg.HKEY_*' constant
                    e.g. 18446744071562067968
                3. A string of the 'HKEY_*' constant name
                    e.g. 'HKEY_CLASSES_ROOT'

        subkey_path:
            A string that identifies the key path to start traversing from.
            Examples are:
                r'Software\Python'
                r'Software\Python\PythonCore'
                r'SYSTEM\Keyboard Layout'

            The exact subkey-path will be dependent on root_hkey
            passed and your Windows platform.

        exclude_keys:
            List of Path-Keys to not traverse or get the Name:Value pairs for
            Example is:
                ["{D3E34B21-9D75-101A-8C3D-00AA001A1652}",
                 "System\Currentcontrolset\ServiceState",
                 "HARDWARE\DESCRIPTION"]]

    """

    # ######################################
    # Internal function to get and print the
    # Name:Value pairs for a given key-path as
    # spaced cols:
    #   Type         Name         Value
    #
    def _print_values_for_path_key(root_hkey, path):
        for name, value, type in get_values(root_hkey, path):
            if not name:  # '(Default)' entries with a Value are not named
                name = "(Default)"  # ...so name it

            print(
                f"\t{REG_TYPE_DICT.get(type, 'REG_UNKNOWN'):<{MAX_PRINT_TYPE_COL_WIDTH}}",
                f"{name:<{MAX_PRINT_NAME_COL_WIDTH}}",
                f"{value}",
            )

    # ######################################
    # Check passed function arguments
    root_hkey = _check_root_key(root_hkey)

    # Key-Path is case insensitive, but change it as close as we can
    # to the Win Reg convention so when we print it, it looks pretty.
    # No other checks for the key-path here. If it's wrong, a
    # FileNotFoundError exception will be raised when we try to access it.
    path = subkey_path.title()

    if isinstance(exclude_keys, list):
        # FORCE to one format style for when we later use 'xxx in exclude_keys'
        exclude_keys = [x.upper() for x in exclude_keys]
    else:
        print(f"Exclude '{exclude_keys}' not valid, should be list(str)")
        print("Ignoring and continuing with no exclusions.")
        exclude_keys = []

    # ######################################
    # Main Functionality
    print(f"\nComputer\\{HKEY_CONST_DICT[root_hkey]}\\{path}")

    _print_values_for_path_key(root_hkey, path)

    # Iterate through any yielded subkeys on this input path
    for subkey in get_keys(root_hkey, path):
        # Update path, or handle no root-path case ("")
        sub_path = f"{path}\\{subkey}" if path else subkey

        if sub_path.upper() in exclude_keys:
            print(f"\nUser Excluded: key-path={sub_path}")
            continue

        print(f"\nComputer\\{HKEY_CONST_DICT[root_hkey]}\\{sub_path}")

        _print_values_for_path_key(root_hkey, sub_path)

        try:
            # Recurse into any lower subkeys under the current subkey
            for sub_subkey in get_keys(root_hkey, sub_path):
                sub_subpath = f"{sub_path}\\{sub_subkey}"

                if sub_subpath.upper() in exclude_keys:
                    print(f"\nUser Excluded: key-path={sub_subpath}")
                    continue

                traverse_winreg_for_values(
                    root_hkey,
                    sub_subpath,
                    exclude_keys,
                )

        except RecursionError as err:  # This should not happen, but....
            print(err)


def walk_winreg():
    """Script Main Function."""
    args = _parse_arguments()

    # Error checking on passed args done in function
    traverse_winreg_for_values(args.key, args.path, args.exclude)


if __name__ == "__main__":
    walk_winreg()
