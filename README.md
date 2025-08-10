Reading UV docs and came across [Registration in the Windows registry](https://docs.astral.sh/uv/concepts/python-versions/#registration-in-the-windows-registry) which talked about [PEP 514](https://peps.python.org/pep-0514/).

I'd not known about this, not thought about it to be honest, but when you lok in the Windows Registry you can see the Python versions.

![Example of Python in the Windows Regsitry](image)

Scanning through PEP 514 there are two Python [Sample Code](https://peps.python.org/pep-0514/#sample-code) sections that read the registry and show the "Company-Tag pairs". The two code samples do:

1. Enumerate the registry and display the most-preferred target for the tag. Backwards-compatible handling of PythonCore is omitted
2. Only lists the PythonCore entries for the current user. Where data is missing, the defaults in PEP 514 are substituted.

I've not used the Python WinReg module, lets run this and see what happens:
