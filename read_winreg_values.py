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


def get_winreg_values(root_hkey, path):
    r"""
    Get Windows Registry Values.

    Walks through the Windows Registry printing the Key:Value
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

        path:
            A path string that identifies the sub-key to open.
            Examples are:
                'Software\Python'
                'Software\Python\PythonCore'
                'SYSTEM\Keyboard Layout'

            The exact path will be dependent on root_hkey
            passed and your Windows platform.

    """

    # ######################################
    # Internal function to get and print the
    # Key:Value pairs for a given key-path
    def _print_values_for_path_key(root_hkey, path):
        for name, value, type in get_values(root_hkey, path):
            if not name:
                # '(Default)' entries with a Value are not named, so name it
                name = "(Default)"

            # try:
            #     name_str = f"{name}"
            # except UnicodeEncodeError:
            #     name_str = "UnicodeEncodeError!"

            # try:
            #     value_res = f"{value}"
            # except UnicodeEncodeError:
            #     value_res = "UnicodeEncodeError!"

            print(  # Show the Type if possible, otherwise use what the reg returns
                f"\t{REG_TYPE_DICT.get(type, str(type)):<{MAX_PRINT_TYPE_COL_WIDTH}}",
                # f"\t{type}:<{MAX_PRINT_TYPE_COL_WIDTH}",
                f"{name:<{MAX_PRINT_NAME_COL_WIDTH}}",
                f"{value}",
            )

    # ######################################

    root_hkey = _check_root_key(root_hkey)

    path = path.title()  # Follow Reg convention (it's not exact, but looks better)
    print(f"\nComputer\\{HKEY_CONST_DICT[root_hkey]}\\{path}")

    _print_values_for_path_key(root_hkey, path)

    # Iterate through any subkeys on this upper path
    for subkey in get_keys(root_hkey, path):
        # Update path or handle "" edge case
        sub_path = f"{path}\\{subkey}" if path else subkey
        print(f"\nComputer\\{HKEY_CONST_DICT[root_hkey]}\\{sub_path}")

        _print_values_for_path_key(root_hkey, sub_path)

        try:
            # Recurse into any lower subkeys under the current subkey
            for sub_subkey in get_keys(root_hkey, sub_path):
                get_winreg_values(root_hkey, f"{sub_path}\\{sub_subkey}")

        except RecursionError as err:  # This should not happen, but....
            print(err)


if __name__ == "__main__":
    root_hkey = winreg.HKEY_CURRENT_USER
    root_path = r"Software\Python"  # List User Python installs
    # root_path = r"Software\Classes\.py\OpenWithProgids"  # .py files associated with
    # root_path = r"Software\Classes\AppUserModelId\c:/ProgramData/ASUS/AsusSurvey/AsusSurvey.exe"  # Fwd slash in key
    # root_path = r"Software\Classes\AppUserModelId"  # Fwd slash in key
    # root_path = ""  # Not recommended for all HKey types

    # root_hkey = winreg.HKEY_LOCAL_MACHINE  # Possible PermissionError's
    # root_path = r"Software\Python"  # List System 'Pythoncore' installs
    # root_path = r"HARDWARE\DEVICEMAP\VIDEO"  # Unusual Name:Value
    # root_path = r"Software\Microsoft\Input\Locales\Loc_0039\Inputmethods"  # Unusual Char
    # root_path = r"Software\Microsoft\Windows Nt\Currentversion\FontMapperFamilyFallback"  # Char Encoding
    # root_path = r"System\Controlset001\Control\Class\{4D36E96C-E325-11Ce-Bfc1-08002Be10318}\Configuration\Reset"  # Unusual Types
    # root_path = ""  # Not recommended

    # root_hkey = winreg.HKEY_CLASSES_ROOT
    # root_path = s"Wow6432Node\Appid\OneDrive.EXE"  # Errors: Reg does not work on my Laptop for this entry
    # root_path = r"Installer\Dependencies"  # Mentions System Python
    # root_path = ""  # Not recommended, likely get error unless you have a "perfect" Win Reg

    # root_hkey = winreg.HKEY_USERS
    # root_path = ""  # Not recommended, nothing of interest

    # root_hkey = winreg.HKEY_CURRENT_CONFIG
    # root_path = ""  # Pretty much empty for me

    get_winreg_values(root_hkey, root_path)


# TODO(JB): Print to JSON?
# TODO(JB): Add HKey when printing Path. SOme PAths are long, but its better to have the HKe constant name included
# TODO(JB): May need to set PS console to "chcp 65001" to display correct
