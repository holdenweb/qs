"""Tests for qs deploy logic.

The deploy() function orchestrates git, subprocess, Fabric SSH, Jinja2
templating, and MongoDB lookups.  We mock all external boundaries and
verify the orchestration logic.
"""
import sys
import uuid
from unittest.mock import MagicMock, patch

import pytest

from qs.deploy import deploy, deploy_cli
from qs.models import App, Server


# ------------------------------------------------------------------
# deploy_cli() — argument handling
# ------------------------------------------------------------------
class TestDeployCli:

    def test_exits_with_usage_on_no_args(self):
        with patch.object(sys, "argv", ["deploy"]):
            with pytest.raises(SystemExit):
                deploy_cli()

    def test_exits_with_usage_on_too_many_args(self):
        with patch.object(sys, "argv", ["deploy", "app1", "app2"]):
            with pytest.raises(SystemExit):
                deploy_cli()

    def test_passes_single_arg_to_deploy(self):
        with patch.object(sys, "argv", ["deploy", "myapp"]):
            with patch("qs.deploy.deploy") as mock_deploy:
                deploy_cli()
                mock_deploy.assert_called_once_with("myapp")


# ------------------------------------------------------------------
# deploy() — version extraction from git tags
# ------------------------------------------------------------------
class TestDeployVersionExtraction:

    def test_exits_when_no_git_tag(self):
        """If HEAD has no tag, deploy must exit with a clear message."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="\n")
            with pytest.raises(SystemExit, match="Unable to find any tag"):
                deploy("myapp")

    def test_exits_when_tag_is_just_v(self):
        """A tag of exactly 'v' with nothing after it is also empty."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="v\n")
            with pytest.raises(SystemExit, match="Unable to find any tag"):
                deploy("myapp")


# ------------------------------------------------------------------
# deploy() — database lookups
# ------------------------------------------------------------------
class TestDeployAppLookup:

    def test_exits_when_app_not_found(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="v1.0.0\n")
            with pytest.raises(SystemExit, match="not found"):
                deploy("nonexistent-app")

    def test_exits_when_app_has_no_port(self):
        App(id=uuid.uuid4(), name="no-port-app", port=None).save()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="v1.0.0\n")
            with pytest.raises(SystemExit, match="no port"):
                deploy("no-port-app")

    def test_exits_when_server_not_found(self):
        App(
            id=uuid.uuid4(), name="orphan-app",
            port=8080, server=uuid.uuid4(),
        ).save()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="v1.0.0\n")
            with pytest.raises(SystemExit, match="no server"):
                deploy("orphan-app")


# ------------------------------------------------------------------
# deploy() — version agreement between git and uv
# ------------------------------------------------------------------
class TestDeployVersionAgreement:

    def test_exits_when_uv_and_git_disagree(self):
        server_id = uuid.uuid4()
        App(id=uuid.uuid4(), name="myapp", port=8080, server=server_id).save()
        Server(id=server_id, hostname="test.example.com").save()

        with patch("subprocess.run") as mock_run, \
             patch("qs.deploy.Connection"):
            mock_run.side_effect = [
                MagicMock(stdout="v1.0.0\n"),         # git tag
                MagicMock(stdout="myapp 2.0.0\n"),    # uv version (mismatch!)
            ]
            with pytest.raises(SystemExit, match="disagree on version"):
                deploy("myapp")


# ------------------------------------------------------------------
# deploy() — guards the destructive remote wipe
# ------------------------------------------------------------------
class TestDeployRemoteDirGuard:

    @pytest.fixture(autouse=True)
    def _workdir(self, tmp_path, monkeypatch):
        """Run in a temp dir so the local template files deploy() writes
        before the guard check don't land in the project root."""
        monkeypatch.chdir(tmp_path)

    def test_exits_when_remote_app_dir_missing(self):
        """If the target apps/<name> dir is absent, deploy must abort
        before running the destructive `rm -rf` block."""
        server_id = uuid.uuid4()
        App(id=uuid.uuid4(), name="myapp", port=8080, server=server_id).save()
        Server(id=server_id, hostname="deploy.example.com").save()

        with patch("subprocess.run") as mock_run, \
             patch("qs.deploy.Connection") as MockConn, \
             patch("qs.deploy.Transfer"), \
             patch("qs.deploy.create_wsgi"):
            mock_run.side_effect = [
                MagicMock(stdout="v1.0.0\n"),
                MagicMock(stdout="myapp 1.0.0\n"),
            ]
            mock_conn = MagicMock()
            MockConn.return_value = mock_conn
            # `test -d apps/myapp` reports failure (dir does not exist).
            mock_conn.run.return_value.ok = False

            with pytest.raises(SystemExit, match="not found"):
                deploy("myapp")

            # The destructive wipe must never have been attempted.
            remote_cmds = [str(c) for c in mock_conn.run.call_args_list]
            assert not any("rm -rf" in c for c in remote_cmds)


# ------------------------------------------------------------------
# deploy() — happy-path integration (everything mocked)
#
# We use tmp_path + monkeypatch.chdir so that the template files
# deploy() writes land in a temp directory rather than cwd, and we
# do NOT mock builtins.open (which would break Jinja2 template loading).
# ------------------------------------------------------------------
class TestDeployHappyPath:

    @pytest.fixture(autouse=True)
    def _workdir(self, tmp_path, monkeypatch):
        """Run each test in a temporary directory."""
        monkeypatch.chdir(tmp_path)
        self.tmp = tmp_path

    def _setup_db(self):
        server_id = uuid.uuid4()
        App(id=uuid.uuid4(), name="myapp", port=8080, server=server_id).save()
        Server(id=server_id, hostname="deploy.example.com").save()

    def _make_subprocess_side_effects(self):
        return [
            MagicMock(stdout="v1.0.0\n"),         # git tag
            MagicMock(stdout="myapp 1.0.0\n"),    # uv version
        ]

    def test_connects_to_correct_server(self):
        self._setup_db()
        with patch("subprocess.run") as mock_run, \
             patch("qs.deploy.Connection") as MockConn, \
             patch("qs.deploy.Transfer"), \
             patch("qs.deploy.create_wsgi"):
            mock_run.side_effect = self._make_subprocess_side_effects()
            MockConn.return_value = MagicMock()

            deploy("myapp")

            MockConn.assert_called_once()
            call_kw = MockConn.call_args.kwargs
            assert call_kw["host"] == "deploy.example.com"
            # SSH user and key come from env vars (QS_SSH_USER / QS_SSH_KEY)
            # with defaults of the current OS user and ~/.ssh/id_rsa
            from qs.deploy import SSH_KEY, SSH_USER
            assert call_kw["user"] == SSH_USER
            assert call_kw["connect_kwargs"]["key_filename"] == SSH_KEY

    def test_creates_wsgi_with_module_name(self):
        self._setup_db()
        with patch("subprocess.run") as mock_run, \
             patch("qs.deploy.Connection"), \
             patch("qs.deploy.Transfer"), \
             patch("qs.deploy.create_wsgi") as mock_wsgi:
            mock_run.side_effect = self._make_subprocess_side_effects()

            deploy("myapp")

            mock_wsgi.assert_called_once_with(name="myapp", port=8080)

    def test_hyphenated_project_converts_to_underscore_for_module(self):
        """Project 'my-app' should produce module name 'my_app'."""
        server_id = uuid.uuid4()
        App(id=uuid.uuid4(), name="my-app", port=9090, server=server_id).save()
        Server(id=server_id, hostname="deploy.example.com").save()

        with patch("subprocess.run") as mock_run, \
             patch("qs.deploy.Connection"), \
             patch("qs.deploy.Transfer"), \
             patch("qs.deploy.create_wsgi") as mock_wsgi:
            mock_run.side_effect = [
                MagicMock(stdout="v1.0.0\n"),
                MagicMock(stdout="my-app 1.0.0\n"),
            ]

            deploy("my-app")

            mock_wsgi.assert_called_once_with(name="my_app", port=9090)

    def test_uploads_tarball(self):
        self._setup_db()
        with patch("subprocess.run") as mock_run, \
             patch("qs.deploy.Connection") as MockConn, \
             patch("qs.deploy.Transfer") as MockTransfer, \
             patch("qs.deploy.create_wsgi"):
            mock_run.side_effect = self._make_subprocess_side_effects()
            mock_conn = MagicMock()
            MockConn.return_value = mock_conn
            mock_transfer = MagicMock()
            MockTransfer.return_value = mock_transfer

            deploy("myapp")

            mock_transfer.put.assert_called_once_with(
                "myapp-1.0.0.tgz",
                "apps/myapp/dist/myapp-1.0.0.tgz",
            )

    def test_runs_remote_deployment_commands(self):
        self._setup_db()
        with patch("subprocess.run") as mock_run, \
             patch("qs.deploy.Connection") as MockConn, \
             patch("qs.deploy.Transfer"), \
             patch("qs.deploy.create_wsgi"):
            mock_run.side_effect = self._make_subprocess_side_effects()
            mock_conn = MagicMock()
            MockConn.return_value = mock_conn

            deploy("myapp")

            remote_cmds = [str(c) for c in mock_conn.run.call_args_list]
            # Key deployment steps must be present
            assert any("stop" in c for c in remote_cmds)
            assert any("uv sync" in c for c in remote_cmds)
            assert any("start" in c for c in remote_cmds)

    def test_renders_all_four_template_files(self):
        self._setup_db()
        with patch("subprocess.run") as mock_run, \
             patch("qs.deploy.Connection"), \
             patch("qs.deploy.Transfer"), \
             patch("qs.deploy.create_wsgi"):
            mock_run.side_effect = self._make_subprocess_side_effects()

            deploy("myapp")

        written = {f.name for f in self.tmp.iterdir()}
        assert {"kill", "start", "stop", "uwsgi.ini"}.issubset(written)
