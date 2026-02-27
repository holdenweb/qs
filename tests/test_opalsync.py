"""Tests for qs.opalsync — Opalstack state synchronisation."""
import uuid
from unittest.mock import MagicMock

import pytest

from qs.models import App, Server, class_for
from qs.opalsync import (
    generic_transfer,
    server_transfer,
    specials,
    object_type_names,
)


# ------------------------------------------------------------------
# generic_transfer()
# ------------------------------------------------------------------
class TestGenericTransfer:

    def test_drops_existing_data_and_saves_new(self):
        App(id=uuid.uuid4(), name="existing-app").save()
        assert App.objects.count() == 1

        mock_mgr = MagicMock()
        mock_mgr.list_all.return_value = [
            {"id": str(uuid.uuid4()), "name": "new-app-1", "type": "CUS"},
            {"id": str(uuid.uuid4()), "name": "new-app-2", "type": "CUS"},
        ]

        generic_transfer(mock_mgr, "Apps")

        assert App.objects.count() == 2
        assert App.objects.filter(name="existing-app").count() == 0

    def test_handles_empty_api_response(self):
        App(id=uuid.uuid4(), name="will-be-gone").save()

        mock_mgr = MagicMock()
        mock_mgr.list_all.return_value = []

        generic_transfer(mock_mgr, "Apps")

        assert App.objects.count() == 0


# ------------------------------------------------------------------
# server_transfer()
# ------------------------------------------------------------------
class TestServerTransfer:

    def test_saves_servers_from_nested_dict(self):
        """The Opalstack servers endpoint returns a dict keyed by
        server type (web_servers, imap_servers, etc.), each containing
        a list of server dicts."""
        mock_mgr = MagicMock()
        mock_mgr.list_all.return_value = {
            "web_servers": [
                {"id": str(uuid.uuid4()), "hostname": "web1.example.com", "type": "web"},
            ],
            "imap_servers": [
                {"id": str(uuid.uuid4()), "hostname": "imap1.example.com", "type": "imap"},
            ],
        }

        server_transfer(mock_mgr, "Servers")

        assert Server.objects.count() == 2

    def test_drops_existing_servers_first(self):
        Server(id=uuid.uuid4(), hostname="old.example.com").save()

        mock_mgr = MagicMock()
        mock_mgr.list_all.return_value = {
            "web_servers": [
                {"id": str(uuid.uuid4()), "hostname": "new.example.com", "type": "web"},
            ],
        }

        server_transfer(mock_mgr, "Servers")

        assert Server.objects.count() == 1
        assert Server.objects.first().hostname == "new.example.com"


# ------------------------------------------------------------------
# specials dict
# ------------------------------------------------------------------
class TestSpecials:

    def test_servers_use_special_transfer(self):
        assert specials["Servers"] is server_transfer

    def test_only_servers_are_special(self):
        assert list(specials.keys()) == ["Servers"]


# ------------------------------------------------------------------
# object_type_names
# ------------------------------------------------------------------
class TestObjectTypeNames:

    def test_all_names_resolve_via_class_for(self):
        for name in object_type_names:
            cls = class_for(name)
            assert cls is not None

    def test_expected_count(self):
        """Opalstack currently exposes 19 resource types."""
        assert len(object_type_names) == 19

    def test_includes_core_types(self):
        assert "Apps" in object_type_names
        assert "Servers" in object_type_names
        assert "Domains" in object_type_names
        assert "Sites" in object_type_names
