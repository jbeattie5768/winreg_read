"""
Analyse saved Windows 'RegEdit.exe' HKEY files.
Just looking to see what different data we get in the reg.

Ran these various command in the console.
Can run the script though, just change the hardcoded files.

The command to start the console was:
    uv run python

Alternatively to run the script:
    uv run python file_analyse.py

"""

# ###############################################################
# Imports I use later
import fileinput
from collections import Counter
from pprint import pprint

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

print("\n###############################################################\n")
# Open file - use 'UTF-16' to prevent UnicodeDecodeError om the console
# There are some 'locale' characters that will not work for UTF-8

print("Loading files...")
with fileinput.input(files=tuple_of_files, encoding="utf-16") as fid:
    data = list(fid)

# Alternatively, for just opening one file:
# with open('regdump_HKEY_CURRENT_USER.txt', encoding='utf-16') as fid:
#     data = fid.readlines()

print("\n###############################################################\n")
# File info

line_count = len(data)
print(f"Line Count: {line_count}")

c = Counter(data)
blank_lines = c["\n"]
print(f"Lines Blank: {blank_lines}")
print(f"...that accounts for {blank_lines / line_count:.2%} of all lines")

# OPTIONAL: Remove blank lines (it was almost 20% for me)
data = list(filter(lambda x: x != "\n", data))
new_count = len(data)
print(
    f"...removed blanks lines, which has reduced line count by {100 - ((new_count / line_count) * 100):.4}%"
)
print(f"Updated Line Count: {new_count}")

print("\n###############################################################\n")
# Look at the first few lines to see what we are working with

print("This is what the file contents looks like:\n")
pprint(data[0:20])

print("\n###############################################################\n")
# What Can we find out about Keys

keynames = []
for this_line in data:
    if this_line.startswith("Key Name:"):
        # Caution: Keys can have whitespace
        keynames.append(this_line.split("Key Name:")[1].strip())
print(f"Key Count: {len(keynames)}\n")
print("First few Key Names....\n")
pprint(keynames[:12])  # Print 1st 12

# Likely the longest and deepest key-paths are the same...
longest_path = max(keynames, key=len)
print(f"\nLongest key-path is {len(longest_path)} characters.")
print(f"With {len(longest_path.split('\\'))} keys in it:\n")
print(longest_path)  # The actual key-path

deepest_path = max(keynames, key=lambda x: len(x.split("\\")))
print(f"\nDeepest key-path is {len(deepest_path)} characters.")
print(f"With {len(deepest_path.split('\\'))} keys in it:\n")
print(deepest_path)  # The actual key-path

# There should be NO duplicate keys: false and []
print(f"\nDuplicates = {keynames.count(keynames) > 1}")
seen = set()
duplicates = set()
for num in keynames:
    if num in seen:
        duplicates.add(num)
    seen.add(num)
pprint(list(duplicates))

# So Key Names are like a path, i.e. the path is made up of keys

print("\n###############################################################\n")
# What HKEY entries do we have, e.g. 'HKEY_CURRENT_USER', etc

hkeys = []
for index, key in enumerate(keynames):
    hkeys.append(keynames[index].split("\\")[0])
print("HKEYS listed:\n")
pprint(set(hkeys))

print("\n###############################################################\n")
# What Types are used

types = []
for this_line in data:
    if this_line.startswith("  Type:"):
        types.append(this_line.split()[1])
print("Types found:\n")
pprint(set(types))

# For me, there is a 'REG_UNKNOWN' type, lets looks at it

print("\n###############################################################\n")

# 'REG_UNKNOWN' type
# The text files show nothing in terms of value, but if we want to
# look in RegEdit for what caused the Type to be set, we can find
# the 'REG_UNKNOWN' entries, find the associated key and copy that
# key-path into RegEdit and take a look

lines_with_unknown = []  # list of lines containing 'REG_UNKNOWN'
for index, value in enumerate(data):
    if data[index].startswith("  Type:            REG_UNKNOWN"):
        lines_with_unknown.append(index)

# Find the key-path for the chosen 'REG_UNKNOWN' entry
if lines_with_unknown:
    list_index = 10  # e.g. lines_with_unknown[10] = random choice
    # Walk back from list_index till we find 'Key Name'
    for this_line in range(lines_with_unknown[list_index], 0, -1):
        if data[this_line].startswith("Key Name:          "):
            print(
                f"\nREG_UNKNOWN Type: Copy and Paste this line into RegEdit:\n\n"
                f"computer\\{data[this_line].split('Key Name:          ')[1]}"
            )
            break
    # Now copy and paste that key-path into RegEdit (paste over the whole
    # RegEdit path, the 'computer' prefix has been added above)
    # We can look at the lines in the file contents printed below, and there
    # should be some associated Key 'Name' entries that match in RegEdit:
    pprint(
        # This will print 'lines_with_unknown[list_index] - this_line'
        # lines after the *Key* producing 'REG_UNKNOWN' types
        data[this_line : lines_with_unknown[list_index]],
        width=120,
    )
else:
    print("No 'REG_UNKNOWN' entries found")
    # You should see that the 'REG_UNKNOWN' type is a Hex number. e.g. 0x4007

print("\n###############################################################\n")
# What does the 'Class Name' entry give us

class_names = []
for index, value in enumerate(data):  # Keep the index for later
    if data[index].startswith("Class Name:"):
        class_names.append((data[index].split("Class Name:")[1].lstrip(), index))
print("First few Class Names (value, lineindex)..\n")
pprint(class_names[:12])  # Print 1st few
c = Counter([x[0] for x in class_names])  # Just count the class name
print("\nThe most common Class Name entries:\n")
pprint(c.most_common())

# I think this is the RegEdit exporter being clever.
# Looking at a few of these in RegEdit I cannot determine what is
# generating these entries.
# It appears the Class, ClassID and ClLassGuid are defined under
# 'HKEY_CLASSES_ROOT'
#
# Later the same appear as named "Name" entries. I think the exporter
# is being clever and making the association for the file export.
#
# Update: Even if I use the Python WinReg module, I cannot get access
# to the files 'Class Name' entries from the registry. I can safely
# ignore these (you may have to investigate further if your use-case
# differs)

print("\n###############################################################\n")
# Time to go and write some code....
