"""Compatibility namespace for local service packages.

Some service directories use deployment-friendly hyphenated names, while Python
imports use underscore names. The small shim packages under this namespace keep
runtime imports and tests stable without renaming directories on disk.
"""

