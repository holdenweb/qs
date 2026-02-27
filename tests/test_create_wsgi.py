"""Tests for qs.create_wsgi — WSGI entry-point file generation."""
import pytest

from qs.create_wsgi import create_wsgi, WSGIPY_TEMPLATE


class TestCreateWsgi:
    """create_wsgi() writes a wsgi.py into the current directory."""

    def test_writes_wsgi_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        create_wsgi("myapp")
        assert (tmp_path / "wsgi.py").exists()

    def test_default_port_is_2400(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        create_wsgi("myapp")
        content = (tmp_path / "wsgi.py").read_text()
        assert "port = 2400" in content

    def test_custom_port(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        create_wsgi("myapp", port=8080)
        content = (tmp_path / "wsgi.py").read_text()
        assert "port = 8080" in content

    def test_imports_app_from_named_module(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        create_wsgi("my_flask_app")
        content = (tmp_path / "wsgi.py").read_text()
        assert "from my_flask_app import app, application" in content

    def test_includes_main_guard(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        create_wsgi("myapp")
        content = (tmp_path / "wsgi.py").read_text()
        assert "if __name__ == '__main__':" in content


class TestWsgiTemplate:
    """Verify the template string itself has the expected placeholders."""

    def test_has_name_placeholder(self):
        assert "{name}" in WSGIPY_TEMPLATE

    def test_has_port_placeholder(self):
        assert "{port}" in WSGIPY_TEMPLATE

    def test_has_main_guard(self):
        assert "if __name__" in WSGIPY_TEMPLATE
