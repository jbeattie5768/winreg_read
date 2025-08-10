Reading UV docs and came across [Registration in the Windows registry](https://docs.astral.sh/uv/concepts/python-versions/#registration-in-the-windows-registry) which talked about [PEP 514](https://peps.python.org/pep-0514/).

I'd not known about this, not thought about it to be honest, but when you lok in the Windows Registry you can see the Python versions.

![Example of Python in the Windows Regsitry](image)

Scanning through PEP 514 there are two Python [Sample Code](https://peps.python.org/pep-0514/#sample-code) sections that read the registry and show the "Company-Tag pairs". The two code samples do:

1. Enumerate the registry and display the most-preferred target for the tag. Backwards-compatible handling of PythonCore is omitted
2. Only lists the PythonCore entries for the current user. Where data is missing, the defaults in PEP 514 are substituted.

I've not used the Python WinReg module, so lets run the code samples and see what happens.

----

Firstly it is looking for User (HKEY_CURRENT_USER) and System (HKEY_LOCAL_MACHINE) installations of Python. I've installed one System Python and a few User versions:

| HKEY Root | Python Version | Company
|-----------|----------------|---------
| User      | 3.10.18        | Astral
| User      | 3.11.13        | PSF
| User      | 3.12.11        | Astral
| User      | 3.13.5         | Astral
| User      | 3.14.0b4       | Astral
| System    | 3.13.3         | PSF

Using UV makes it extremely simple to add/remove User Python versions.
My default Python version  to run these samples if 3.13.5.

Lets run Sample1:

![alt text](image.png)

Interesting, it's identified all the versions, but does not think they are executable. We will come back to that as it's wrong.

Lets run Sample2:

![alt text](image-1.png)

Better, but still some issues: version numbers appear truncated and it can't get the system architecture.

Looking at the Windows `RegEdit.exe` application we can see there are executable paths and architecture and version data:

![alt text](image-2.png)

Time to modify the code...but first lets read the [WinReg Documentation](https://docs.python.org/3.13/library/winreg.html)...brb....

```python
"""
Simplest Read with WinReg

* The Win Registry is a series of root keys, each with subkeys and values.
* The root keys we are concerned with are HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE.
* Value type is always null-terminated strings ('winreg.REG_SZ' == 1). 
* We wil only be connecting locally, otherwise see `winreg.ConnectRegistry()`.
"""
import winreg

# Open the specified key, returning a handle object.
key_handle = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER,        # Root key
                              "Software\\Python\\PythonCore",  # subkey
                              access=winreg.KEY_READ,)         # Default is KEY_READ

# Ignore returned type, just worry about the value
dis_value, _ = winreg.QueryValueEx(key_handle,     # Key Handle Object
                                   "DisplayName")  # 'DisplayName' is a value in the subkey
uri_value, _ = winreg.QueryValueEx(key_handle, 
                                   "SupportUrl")   # 'SupportUrl' is a value in the subkey

print(f"SubKey values: DisplayName='{dis_value}', SupportUrl='{uri_value}'")

```

Okay, pretty simple but very much hardcoded. Interestingly, the documntation says to use `winreg.QueryValueEx()` over `winreg.QueryValue()` that the sample code uses. This seems to be because the latter returns the first Null entry of the sub-key, which is the '_(Default)_' value and is usually empty.

If we use the preferred `winreg.QueryValueEx()` function in the sample code and only return the value string (ignore the value type, it's always 1 == `winreg.REG_SZ`):

![alt text](image-3.png)

That is now correct.  

----
