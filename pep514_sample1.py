# Display most-preferred environments.
# Assumes a 64-bit operating system
# Does not correctly handle PythonCore compatibility

import winreg


def enum_keys(key):
    i = 0
    while True:
        try:
            yield winreg.EnumKey(key, i)
        except OSError:
            break
        i += 1


def get_value(key, value_name):
    try:
        value, type = winreg.QueryValueEx(key, value_name)
        return value
    except FileNotFoundError:
        return None


seen = set()
for hive, key, flags in [
    (winreg.HKEY_CURRENT_USER, r"Software\Python", 0),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Python", winreg.KEY_WOW64_64KEY),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Python", winreg.KEY_WOW64_32KEY),
]:
    with winreg.OpenKeyEx(hive, key, access=winreg.KEY_READ | flags) as root_key:
        for company in enum_keys(root_key):
            if company == "PyLauncher":
                continue

            with winreg.OpenKey(root_key, company) as company_key:
                for tag in enum_keys(company_key):
                    if (company, tag) in seen:
                        if company == "PythonCore":
                            # TODO: Backwards compatibility handling
                            pass
                        continue
                    seen.add((company, tag))

                    try:
                        with winreg.OpenKey(
                            company_key, tag + r"\InstallPath"
                        ) as ip_key:
                            exec_path = get_value(ip_key, "ExecutablePath")
                            exec_args = get_value(ip_key, "ExecutableArguments")
                            if company == "PythonCore" and not exec_path:
                                # TODO: Backwards compatibility handling
                                pass
                    except OSError:
                        exec_path, exec_args = None, None

                    if exec_path:
                        print(
                            "{}\\{} - {} {}".format(
                                company, tag, exec_path, exec_args or ""
                            )
                        )
                    else:
                        print("{}\\{} - (not executable)".format(company, tag))
