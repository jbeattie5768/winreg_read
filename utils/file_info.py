"""
Simple file to display some size related stats on the RegEdit.exe
exported test files.

Uses the Rich module, so the command line I used was:

    uv run --with rich python file_info.py

"""

# ###############################################################
# Imports I use later
import os

from rich.console import Console  # pyright: ignore[reportMissingImports]
from rich.table import Table  # pyright: ignore[reportMissingImports]

# ###############################################################
# List of files to process
# You can't dump the whole reg in RegEdit. You must dump piecemeal.
# You don't need to do all, something like HKEY_CURRENT_USER is enough
# for these examples
tuple_of_files = (
    "regdump_HKEY_CLASSES_ROOT.txt",
    "regdump_HKEY_CURRENT_CONFIG.txt",
    "regdump_HKEY_CURRENT_USER.txt",
    "regdump_HKEY_LOCAL_MACHINE.txt",
    "regdump_HKEY_USERS.txt",
)

# ###############################################################
# Prepare Rich
table = Table(title="Win Reg HKEY List")
console = Console()
table.add_column("Filename", justify="right", style="cyan", no_wrap=True)
table.add_column("File Size", justify="right", style="cyan", no_wrap=True)
table.add_column("File Lines", justify="left", style="magenta")
table.add_column("Key Count", justify="left", style="green")

# ###############################################################
# Individual file information
table_list = []
for index, filename in enumerate(tuple_of_files):
    with open(filename, encoding="utf-16") as fid:
        this_table_row = []
        data = fid.readlines()

        this_table_row.append(filename)

        file_size_bytes = os.path.getsize(filename)

        # Conversion to kilobytes, megabytes, and gigabytes
        file_size_kb = file_size_bytes / 1024
        file_size_mb = file_size_kb / 1024
        file_size_gb = file_size_mb / 1024
        # print(f"File Size (Bytes): {file_size_bytes} B")
        # print(f"File Size (KB): {file_size_kb:.2f} KB")
        # print(f"File Size (MB): {file_size_mb:.2f} MB")
        # print(f"File Size (GB): {file_size_gb:.2f} GB")

        if file_size_kb < 1024:
            this_table_row.append(f"{file_size_kb:.2f} (KB)")
        else:
            this_table_row.append(f"{file_size_mb:.2f} (MB)")
        this_table_row.append(len(data))

        keynames = []
        for this_line in data:
            if this_line.startswith("Key Name:"):
                # Caution: Keys can have whitespace
                keynames.append(this_line.split("Key Name:")[1].strip())
        this_table_row.append(len(keynames))

    print(this_table_row)
    table_list.append(this_table_row)

# ###############################################################
# Output Rich Table
sorted_table = sorted(table_list, key=lambda x: x[2])  # Sort on line count
for this_row in sorted_table:
    table.add_row(
        str(this_row[0]), str(this_row[1]), str(this_row[2]), str(this_row[2])
    )

console.print(table)
