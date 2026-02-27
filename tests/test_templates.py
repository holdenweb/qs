"""Tests for Jinja2 deployment script templates.

Each template is rendered with sample variables and checked for expected
content.  These tests catch accidental breakage of the shell scripts and
uWSGI config that get deployed to production servers.
"""
import pytest
from jinja2 import Environment, PackageLoader


@pytest.fixture
def jinja_env():
    """Jinja2 environment using the qs package templates."""
    return Environment(
        loader=PackageLoader("qs", "templates"),
        autoescape=False,
    )


SAMPLE_VARS = dict(PROJECT="myapp", PORT_NO=9876, VERSION="1.0.0", HOME_DIR="/home/testuser")


# ------------------------------------------------------------------
# base_template
# ------------------------------------------------------------------
class TestBaseTemplate:

    def test_is_bash_script(self, jinja_env):
        content = jinja_env.get_template("base_template").render(**SAMPLE_VARS)
        assert content.startswith("#!/bin/bash")

    def test_sources_ssh_env(self, jinja_env):
        content = jinja_env.get_template("base_template").render(**SAMPLE_VARS)
        assert "source ~/.ssh/env" in content

    def test_sets_apphome(self, jinja_env):
        content = jinja_env.get_template("base_template").render(**SAMPLE_VARS)
        assert "APPHOME=$HOME/apps/myapp" in content

    def test_sets_pythonpath(self, jinja_env):
        content = jinja_env.get_template("base_template").render(**SAMPLE_VARS)
        assert "PYTHONPATH=${APPHOME}/src" in content

    def test_sets_pidfile(self, jinja_env):
        content = jinja_env.get_template("base_template").render(**SAMPLE_VARS)
        assert 'PIDFILE="${APPHOME}/tmp/myapp.pid"' in content


# ------------------------------------------------------------------
# start
# ------------------------------------------------------------------
class TestStartTemplate:

    def test_inherits_base_variables(self, jinja_env):
        content = jinja_env.get_template("start").render(**SAMPLE_VARS)
        assert "APPHOME=$HOME/apps/myapp" in content
        assert "PIDFILE=" in content

    def test_checks_already_running(self, jinja_env):
        content = jinja_env.get_template("start").render(**SAMPLE_VARS)
        assert "Already running" in content
        assert "exit 99" in content

    def test_starts_uwsgi(self, jinja_env):
        content = jinja_env.get_template("start").render(**SAMPLE_VARS)
        assert ".venv/bin/uwsgi --ini" in content

    def test_logs_start_time(self, jinja_env):
        content = jinja_env.get_template("start").render(**SAMPLE_VARS)
        assert "Started at" in content


# ------------------------------------------------------------------
# stop
# ------------------------------------------------------------------
class TestStopTemplate:

    def test_stops_uwsgi(self, jinja_env):
        content = jinja_env.get_template("stop").render(**SAMPLE_VARS)
        assert "uwsgi --stop" in content

    def test_removes_pidfile(self, jinja_env):
        content = jinja_env.get_template("stop").render(**SAMPLE_VARS)
        assert "rm $PIDFILE" in content

    def test_exits_if_not_running(self, jinja_env):
        content = jinja_env.get_template("stop").render(**SAMPLE_VARS)
        assert "No PID file" in content
        assert "exit 99" in content


# ------------------------------------------------------------------
# kill
# ------------------------------------------------------------------
class TestKillTemplate:

    def test_sends_kill_9(self, jinja_env):
        content = jinja_env.get_template("kill").render(**SAMPLE_VARS)
        assert "kill -9" in content

    def test_reads_pidfile(self, jinja_env):
        content = jinja_env.get_template("kill").render(**SAMPLE_VARS)
        assert "cat $PIDFILE" in content


# ------------------------------------------------------------------
# uwsgi.ini
# ------------------------------------------------------------------
class TestUwsgiIniTemplate:

    def test_sets_port(self, jinja_env):
        content = jinja_env.get_template("uwsgi.ini").render(**SAMPLE_VARS)
        assert "http-socket = 127.0.0.1:9876" in content

    def test_sets_virtualenv_path(self, jinja_env):
        content = jinja_env.get_template("uwsgi.ini").render(**SAMPLE_VARS)
        assert "/apps/myapp/.venv/" in content

    def test_sets_wsgi_file(self, jinja_env):
        content = jinja_env.get_template("uwsgi.ini").render(**SAMPLE_VARS)
        assert "/apps/myapp/wsgi.py" in content

    def test_sets_pidfile(self, jinja_env):
        content = jinja_env.get_template("uwsgi.ini").render(**SAMPLE_VARS)
        assert "/apps/myapp/tmp/myapp.pid" in content

    def test_enables_master_mode(self, jinja_env):
        content = jinja_env.get_template("uwsgi.ini").render(**SAMPLE_VARS)
        assert "master = True" in content

    def test_workers_and_threads(self, jinja_env):
        content = jinja_env.get_template("uwsgi.ini").render(**SAMPLE_VARS)
        assert "workers = 2" in content
        assert "threads = 2" in content

    def test_touch_reload_enabled(self, jinja_env):
        content = jinja_env.get_template("uwsgi.ini").render(**SAMPLE_VARS)
        assert "touch-reload" in content
