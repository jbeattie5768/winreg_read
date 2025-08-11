import os
import winreg

MAX_PRINT_COL_WIDTH = 24  # Align 2nd column from 1st column


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
                except OSError:
                    break
    except (OSError, FileNotFoundError) as err:
        msg = f"\n{path} is not a valid path"
        raise FileNotFoundError(msg) from err


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
                except OSError:
                    break
    except (OSError, FileNotFoundError) as err:
        msg = f"\n{path} is not a valid path"
        raise FileNotFoundError(msg) from err


def get_winreg_values(root_hkey, path):
    r"""
    Get Windows Registry Values.

    Walks through the Windows Registry printing the Key:Value
    pairs.

    Args:
        root_hkey:
            One of the predefined winreg.HKEY_* constants
                winreg.HKEY_CLASSES_ROOT
                winreg.HKEY_CURRENT_USER
                winreg.HKEY_LOCAL_MACHINE
                winreg.HKEY_USERS
                winreg.HKEY_CURRENT_CONFIG
        path:
            A path string that identifies the sub-key to open.
            Examples are:
                'Software\Python'
                'Software\Python\PythonCore'
                'SYSTEM\Keyboard Layout'

            The exact path will be dependent on root_hkey
            passed and your Windows platform.

    """

    # Internal function to get and print the
    # Key:Value pairs for a given key-path
    def _print_values_for_path_key(root_hkey, path):
        for name, value, _ in get_values(root_hkey, path):
            if name:
                print(f"\t{name:<{MAX_PRINT_COL_WIDTH}}{value}")
            else:
                # '(Default)' entries with a Value are not named, so name it
                print(f"\t{'(Default)':<{MAX_PRINT_COL_WIDTH}}{value}")

    # Normalise path: title and backslashes
    path = os.path.join(*path.title().replace(r"/", "\\").split("\\"))  # noqa: PTH118
    print(f"\n{path}")

    _print_values_for_path_key(root_hkey, path)

    # Iterate through any subkeys on this upper path
    for subkey in get_keys(root_hkey, path):
        sub_path = (  # Update path or handle "" edge case
            f"{path}\\{subkey}" if path else subkey
        )
        print(f"\n{sub_path}")

        _print_values_for_path_key(root_hkey, sub_path)

        try:
            # Recurse into any lower subkeys under the current subkey
            for sub_subkey in get_keys(root_hkey, sub_path):
                get_winreg_values(root_hkey, f"{sub_path}\\{sub_subkey}")

        except RecursionError as err:  # This should not happen, but....
            print(err)


if __name__ == "__main__":
    root_hkey = winreg.HKEY_CURRENT_USER
    hkey_str = "HKEY_CURRENT_USER"
    root_hkey = winreg.HKEY_LOCAL_MACHINE
    root_path = r"software\\/\\/\\/\\/\\/\\/PYTHON"
    # root_path = r"Software\7-Zip"
    # root_path = r"Software\Google"
    # root_path = r"SYSTEM//////\\\\\////////keyboard layout"
    # root_path = r"AppEvents"
    # root_path = r""

    print(f"Computer\\\\{hkey_str.upper()}\\\\")
    get_winreg_values(root_hkey, root_path)


# TODO(JB): Test with https://github.com/bitranox/fake_winreg ??
# TODO(JB): HKEY_CLASSES_ROOT is a subkey of HKEY_LOCAL_MACHINE\Software <- deny or confirm and doc
# TODO(JB): Print to JSON?
# TODO(JB): Handle different types passed to func = [int, HKEYType, str]
def check_key(key):
    if key is None:
        raise TypeError("None is not a valid type")  # noqa: TRY003, EM101

    # As an int, or a winreg.HKEY_* constant
    if isinstance(key, int):
        if key >= 2**64:  # 64K limit for total size of all values of a key
            raise OverflowError("The int too big to convert")  # noqa: TRY003, EM101
        if key not in [
            winreg.HKEY_CLASSES_ROOT,  # Int should match one of these
            winreg.HKEY_CURRENT_USER,
            winreg.HKEY_LOCAL_MACHINE,
            winreg.HKEY_USERS,
            winreg.HKEY_CURRENT_CONFIG,
        ]:
            raise TypeError("The int is not a valid winreg.HKEY_* type")  # noqa: TRY003, EM101

    # If its a String, try and make it a winreg.HKEY_* constant
    if isinstance(key, str):
        try:
            key = getattr(winreg, key)
        except AttributeError as err:
            raise TypeError("The string is not a HKEY_* string") from err  # noqa: TRY003, EM101

    return key


def print_hkey_values():
    print(f"HKEY_CLASSES_ROO    = {winreg.HKEY_CLASSES_ROOT}")
    print(f"HKEY_CURRENT_USER   = {winreg.HKEY_CURRENT_USER}")
    print(f"HKEY_LOCAL_MACHINE  = {winreg.HKEY_LOCAL_MACHINE}")
    print(f"HKEY_USERS          = {winreg.HKEY_USERS}")
    print(f"HKEY_CURRENT_CONFIG = {winreg.HKEY_CURRENT_CONFIG}")
