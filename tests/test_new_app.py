"""Tests for qs.new_app — creating new Opalstack applications."""
import uuid
from unittest.mock import MagicMock

import pytest

from qs.models import App
from qs.new_app import build, create_app


# ------------------------------------------------------------------
# build() — CLI argument handling
# ------------------------------------------------------------------
class TestBuild:

    def test_exits_with_usage_on_no_app_name(self):
        with pytest.raises(SystemExit):
            build(["new_app"])  # program name only

    def test_exits_with_usage_on_too_many_args(self):
        with pytest.raises(SystemExit):
            build(["new_app", "app1", "app2"])


# ------------------------------------------------------------------
# create_app()
# ------------------------------------------------------------------
class TestCreateApp:

    def test_calls_api_with_correct_args(self):
        mock_mgr = MagicMock()
        manager_id = str(uuid.uuid4())
        mock_mgr.create_one.return_value = {
            "id": str(uuid.uuid4()),
            "name": "test-app",
            "port": 12345,
            "type": "CUS",
            "osuser": manager_id,
        }

        create_app(mock_mgr, "test-app", manager_id)

        mock_mgr.create_one.assert_called_once_with(
            dict(name="test-app", osuser=manager_id, type="CUS")
        )

    def test_saves_app_to_database(self):
        mock_mgr = MagicMock()
        app_id = str(uuid.uuid4())
        manager_id = str(uuid.uuid4())
        mock_mgr.create_one.return_value = {
            "id": app_id,
            "name": "saved-app",
            "port": 54321,
            "type": "CUS",
            "osuser": manager_id,
        }

        create_app(mock_mgr, "saved-app", manager_id)

        assert App.objects.count() == 1
        saved = App.objects.first()
        assert saved.name == "saved-app"
        assert saved.port == 54321

    def test_returns_object_dict_with_app_data(self):
        mock_mgr = MagicMock()
        manager_id = str(uuid.uuid4())
        mock_mgr.create_one.return_value = {
            "id": str(uuid.uuid4()),
            "name": "result-app",
            "port": 11111,
            "type": "CUS",
            "osuser": manager_id,
        }

        result = create_app(mock_mgr, "result-app", manager_id)

        assert result.name == "result-app"
        assert result.port == 11111
