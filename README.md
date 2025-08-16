# Traversing Win Reg for Values 🗝️🪟

## Overview 📖

**Traversing Win Reg for Values** is a Python script that allows users to traverse a specified HKEY and key-path in the Windows Registry, reading and printing all found named values to the console. The script is useful for inspecting registry contents, debugging, or exporting registry data. Output can be piped to a file for further analysis.

## Features ✨

- 🔍 Traverse any user-specified root HKEY and subkey path in the Windows Registry.
- 📋 Print all values found under the specified path and its subkeys.
- 🚫 Optionally exclude specific key-paths from traversal.
- 🔒 Handles permission errors.
- 💾 Output can be redirected to a file for offline analysis.

## Requirements 🛠️

- **Python 3.13+**  
- **WinReg module**  
  The [winreg](https://docs.python.org/3/library/winreg.html) module is included with Python on Windows and provides access to the Windows Registry API.

## Installation ⬇️

Clone the repository or download the script directly:

```sh
git clone https://github.com/yourusername/winreg-traverse.git
cd winreg-traverse
```

Or download [read_winreg_values.py](read_winreg_values.py) directly.

## Usage 🏃

Run the script from the command line:

```pwsh
uv run python read_winreg_values.py HKEY_CURRENT_USER "Software\\Python"
```

- **HKEY**: The root registry hive (e.g., `HKEY_CURRENT_USER`, `HKEY_LOCAL_MACHINE`, etc.).
- **Key-Path**: The subkey path to start traversal from (e.g., `Software\\Python`).

### Optional Arguments ⚙️

- `-e`, `--exclude`: List of key-paths to exclude from traversal.

**Example:**

```sh
uv run python read_winreg_values.py HKEY_CURRENT_USER "Software" -e "Software\Wow6432Node"
```

### Run Programmatically 🐍

```python
# Read Python versions example
import read_winreg_values as rwv

HKEY = rwv.winreg.HKEY_CURRENT_USER     # User installs
# HKEY = rwv.winreg.HKEY_LOCAL_MACHINE  # System installs

KEY_PATH = r"software\python"

# List Python versions
# There may be more than one manufacturer
for this_subkey in rwv.get_keys(HKEY, KEY_PATH):
    print(f"\n{this_subkey.title()} Python Versions:")
    for this_key in rwv.get_keys(HKEY, "\\".join([KEY_PATH, this_subkey])):
        print(f"\t{this_key}")
```

### Redirect Output ➡️📄

To save the output to a file:

```pwsh
python read_winreg_values.py HKEY_CURRENT_USER "Software\\Python" > output.txt
```

## Libraries Used 📚

- [winreg](https://docs.python.org/3/library/winreg.html)  
  Standard Python library for accessing the Windows Registry.

- [argparse](https://docs.python.org/3/library/argparse.html)  
  Standard Python library for parsing command-line arguments.

## Miscellaneous Files 🗂️

Files unrelated to the functionality of `read_winreg_values.py`, but perhaps useful:

Simple files that I used on the REPL to perform an initial _looksee_ at the text files exported from the Windows `regedit.exe` application:

```text
    /utils
        file_analyse.py
        file_info.py
```

Updates to the sample code from [PEP 514](https://peps.python.org/pep-0514/) that now allows the Python Registry entries to be read (it did not correctly work directly copied from the PEP):

```text
    /pep514_sample_code
        pep514_sample1.py
        pep514_sample2.py
```

###### Note: _These samples are the reason I started this script__

## License 📝

This project is open source and available under the [MIT License](https://opensource.org/licenses/MIT).

---

- _Readme <ins>mostly</ins> generated with ChatGPT through my `create_readme.md` prompt._
