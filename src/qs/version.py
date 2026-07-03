"""Expose the installed package version as ``__version__``.

The version is defined once, in ``pyproject.toml``. We read it back from the
installed distribution metadata so there is a single source of truth. When
running from a source tree that has not been installed (no distribution
metadata), we fall back to a clearly-marked development string.
"""
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("qs")
except PackageNotFoundError:  # running from an uninstalled source tree
    __version__ = "0.0.0.dev0"
