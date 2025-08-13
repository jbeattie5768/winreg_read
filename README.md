# The Story so Far

Reading UV docs and came across [Registration in the Windows registry](https://docs.astral.sh/uv/concepts/python-versions/#registration-in-the-windows-registry) which talked about [PEP 514](https://peps.python.org/pep-0514/).

I'd not known about this, not thought about it to be honest, but when you lok in the Windows Registry you can see the Python versions.

![Example of Python in the Windows Registry](image)

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

![alt text](/images/image-0.png)

Interesting, it's identified all the versions, but does not think they are executable. We will come back to that as it's wrong.  
It identifies _PythonCore_ as the PSF installations, which is correct according to PEP 514.

Lets run Sample2:

![alt text](/images/image-1.png)

Better, but still some issues: version numbers appear truncated and it can't get the system architecture.

Looking at the Windows `RegEdit.exe` application we can see there are executable paths as well as architecture and version data:

![alt text](/images/image-2.png)

Time to modify the code...but first lets read the [WinReg Documentation](https://docs.python.org/3.13/library/winreg.html)...brb....

Okay, lets create the simplest WinReg read that we can to make sure we understand:

```python
# The Win Registry is a series of root keys, each with subkeys and values.
# The root keys we are concerned with are HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE.
# Value type we don't care about, we are getting strings to print for the moment.
# Default access type is READ, so no worries for now. 
# We wil only be connecting locally, otherwise see `winreg.ConnectRegistry()`.

import winreg

# Open the specified key, returning a handle object
key_handle = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER,        # Root key
                              "Software\\Python\\PythonCore",  # SubKey
                              access=winreg.KEY_READ,)         # Default

# Ignore returned type, just worry about the value
dis_value, _ = winreg.QueryValueEx(key_handle,     # Key Handle Object
                                   "DisplayName")  # SubKey
uri_value, _ = winreg.QueryValueEx(key_handle, 
                                   "SupportUrl")   # SubKey

print(f"SubKey values: DisplayName='{dis_value}', SupportUrl='{uri_value}'")

```

Okay, pretty simple but very much hardcoded. Interestingly, the documentation says to use `winreg.QueryValueEx()` over the `winreg.QueryValue()` function that the sample code uses. This seems to be because the latter returns the first Null entry of the sub-key, which is the '_(Default)_' value and is usually empty.

If we use the preferred `winreg.QueryValueEx()` function in the sample code and only return the value string (ignore the value type, it's always 1 == `winreg.REG_SZ` for these values):

![alt text](/images/image-3.png)

Both the code samples for PEP 514 now run.  

----

## Can we do Better?

Reading the docs, there are functions that will enumerate the keys and values of an open registry key. We could use those to enumerate through the available sub-keys and values.

It might be too much to enumerate through every key, but we can continue to start from the given sub-key.

Let give tt a go and see what we end up with....

----

## Code to Traverse the Windows Registry

Well that was a rabbit-hole!

----

### Example Use

#### On the CLI

#### Programmatically

##### Example 1

Traverse a given HKEY and Subkey-path:

```python {hl_lines=[6]}
import read_winreg_values as rwv

hkey = rwv.winreg.HKEY_CURRENT_USER
key_path = r"software\python"

rwv.traverse_winreg_for_values(hkey, key_path)
```

![alt text](/images/image-4.png)

##### Example 2

Display the Python versions available from all manufacturers for the current user:

```python {hl_lines=[7, 9]}
import read_winreg_values as rwv

hkey = rwv.winreg.HKEY_CURRENT_USER
key_path = r"software\python"

# List Python versions for each available manufacturer
for this_subkey in rwv.get_keys(hkey, key_path):
    print(f"\n{this_subkey.title()} Python Versions:")
    for this_key in rwv.get_keys(hkey, '\\'.join([key_path, this_subkey])):
        print(f"\t{this_key}")
```

![alt text](/images/image-5.png)

##### Example 3

```python {hl_lines=[2]}
# ..and then if we wanted to see details of a particular Python version
rwv.traverse_winreg_for_values(hkey, "software\\python\\Astral\\CPython3.14.0b")
```

![alt text](/images/image-6.png)

----

## Issues

__Non-CONSTANT Type Values__: Some Type entries are numbers and not one of the Type constants.

__Forward Slash in Key Name__: At least one Key has forward slashes in it and for the Win Reg you cannot have backslashes in a key name, e.g.
HKEY_CURRENT_USER\Software\Classes\AppUserModelId\C:/ProgramData/ASUS/AsusSurvey/AsusSurvey.exe
The key is "C:/ProgramData/ASUS/AsusSurvey/AsusSurvey.exe", which means I can't use this to normalise slashes:
os.path.join(*path.title().replace(r"/", "\\").split("\\"))

__None Standard Characters__: There are some locale names that threw a UniDecodeError - I guess they did not match my console locale setting. Best to change your console default, for PS `chcp 65001` (UTF-8) worked for me...or just don't traverse those keys.

__Permission errors__: When you open WinRegEdit.exe it open in Admin mode. There are some keys you will need Admin permission to access. I catch and continue for those, but you may need to run the script as admin to access all the keys.

Win Reg Errors: There are some entries in my Win Reg that do not work, even in WinRegEdit.exe. Nothing I can do except fix the Windows Registry itself.

__RecursionErrror__: I was not keen on the counter in `get_keys()` and `get_values()` and instead used recursion (since we we exiting on OSError anyway). Something like this:

```python
def get_keys(hkey, path, index=0):
    try:
        yield winreg.EnumKey(winreg.OpenKey(hkey, path), index)
        yield from get_keys(hkey, path, index+1)
    except OSError as err:
        pass
```

The trouble with this, and something I did not know at the time, is that Python has a recursion limit (`ssys.getrecursionlimit`) and using recursion in the Keys and Values functions meant we exceed that limit, even for moderately long traversals. So I went back to the counter method. This was also the time I became concerned about key handles leaking.  
Perhaps less ~~Pedantic~~ Pythonic, but it's probably clearer to understand with the counter method anyway ;-)

----

## __My Test Cases__

```python
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
```

----

## ToDo's

__Save to JSON File__: Can optionally redirecto to a files as is. for ps:
`uv run python read_winreg_values.py -k "HKEY_CURRENT_USER" -p "Software\Python" > test.txt`

----

## Further Reading

- [Registry Hives](https://learn.microsoft.com/en-us/windows/win32/sysinfo/registry-hives)
