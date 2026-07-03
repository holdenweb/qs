"""Tests for qs.version — version is single-sourced from package metadata."""
import re
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch


def test_version_is_non_empty_string():
    from qs.version import __version__

    assert isinstance(__version__, str)
    assert __version__


def test_version_looks_like_a_version():
    from qs.version import __version__

    # e.g. 0.4.4b5 or 0.0.0.dev0 — at minimum starts with a number.
    assert re.match(r"^\d", __version__)


def test_package_matches_metadata():
    """__version__ must equal what importlib reports for the 'qs' dist."""
    from importlib.metadata import version

    from qs.version import __version__

    assert __version__ == version("qs")


def test_falls_back_when_dist_not_installed():
    """Running from an uninstalled source tree yields a dev fallback."""
    import importlib

    import qs.version

    # Patch at the source so the freshly re-imported name inside the
    # module raises PackageNotFoundError during reload.
    with patch("importlib.metadata.version", side_effect=PackageNotFoundError):
        reloaded = importlib.reload(qs.version)
        assert reloaded.__version__ == "0.0.0.dev0"

    # Restore real metadata-backed value for any later tests.
    importlib.reload(qs.version)
