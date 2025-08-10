# Only lists per-user PythonCore registrations
# Uses fallback values as described in PEP 514

import os
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


with winreg.OpenKey(
    winreg.HKEY_CURRENT_USER, r"Software\Python\PythonCore"
) as company_key:
    print(
        "Company:",
        get_value(company_key, "DisplayName") or "Python Software Foundation",
    )
    print("Support:", get_value(company_key, "SupportUrl") or "http://www.python.org/")
    print()

    for tag in enum_keys(company_key):
        with winreg.OpenKey(company_key, tag) as tag_key:
            print("PythonCore\\" + tag)
            print("Name:", get_value(tag_key, "DisplayName") or ("Python " + tag))
            print(
                "Support:", get_value(tag_key, "SupportUrl") or "http://www.python.org/"
            )
            print("Version:", get_value(tag_key, "Version") or tag[:3])
            print("SysVersion:", get_value(tag_key, "SysVersion") or tag[:3])
            # Architecture is unknown because we are in HKCU
            # Tools may use alternate approaches to determine architecture when
            # the registration does not specify it.
            print(
                "SysArchitecture:", get_value(tag_key, "SysArchitecture") or "(unknown)"
            )

        try:
            ip_key = winreg.OpenKey(company_key, tag + "\\InstallPath")
        except FileNotFoundError:
            pass
        else:
            with ip_key:
                ip = get_value(ip_key, None)
                exe = get_value(ip_key, "ExecutablePath") or os.path.join(
                    ip, "python.exe"
                )
                exew = get_value(ip_key, "WindowedExecutablePath") or os.path.join(
                    ip, "python.exe"
                )
                print("InstallPath:", ip)
                print("ExecutablePath:", exe)
                print("WindowedExecutablePath:", exew)
        print()
