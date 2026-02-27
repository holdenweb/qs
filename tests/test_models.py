"""Tests for qs.models — document models and the class_for factory."""
import uuid

import pytest
from mongoengine.errors import NotUniqueError

from qs.models import (
    class_for,
    Account, Address, App, Cert, Dnsrecord, Domain,
    Ip, Mailuser, Mariadb, Mariauser, Notice,
    OSUser, OSVar, Psqldb, Psqluser, Quarantinedmail,
    Server, Site, Token,
)


# ------------------------------------------------------------------
# class_for()
# ------------------------------------------------------------------
class TestClassFor:
    """The factory must return the correct Document class for every
    Opalstack resource type name, and raise KeyError for unknowns."""

    ALL_MAPPINGS = {
        "Accounts": Account,
        "Addresses": Address,
        "Apps": App,
        "Certs": Cert,
        "Dnsrecords": Dnsrecord,
        "Domains": Domain,
        "Ips": Ip,
        "Mailusers": Mailuser,
        "Mariadbs": Mariadb,
        "Mariausers": Mariauser,
        "Notices": Notice,
        "OSUsers": OSUser,
        "OSVars": OSVar,
        "Psqldbs": Psqldb,
        "Psqlusers": Psqluser,
        "Quarantinedmails": Quarantinedmail,
        "Servers": Server,
        "Sites": Site,
        "Tokens": Token,
    }

    @pytest.mark.parametrize("name,expected_class", ALL_MAPPINGS.items())
    def test_returns_correct_class(self, name, expected_class):
        assert class_for(name) is expected_class

    def test_unknown_name_raises_key_error(self):
        with pytest.raises(KeyError):
            class_for("NonExistent")

    def test_mapping_is_consistent_with_opalsync_type_names(self):
        """Every name that opalsync iterates over must be resolvable."""
        from qs.opalsync import object_type_names

        for name in object_type_names:
            cls = class_for(name)
            assert cls is not None


# ------------------------------------------------------------------
# App model
# ------------------------------------------------------------------
class TestAppModel:

    def test_create_and_retrieve(self):
        app_id = uuid.uuid4()
        server_id = uuid.uuid4()
        App(
            id=app_id, name="test-app", port=12345,
            server=server_id, state="ready", ready=True, type="CUS",
        ).save()

        retrieved = App.objects.get(name="test-app")
        assert retrieved.port == 12345
        assert retrieved.id == app_id
        assert retrieved.server == server_id

    def test_name_uniqueness(self):
        App(id=uuid.uuid4(), name="unique-app").save()
        with pytest.raises(NotUniqueError):
            App(id=uuid.uuid4(), name="unique-app").save()

    def test_does_not_exist_exception(self):
        with pytest.raises(App.DoesNotExist):
            App.objects.get(name="no-such-app")


# ------------------------------------------------------------------
# Server model
# ------------------------------------------------------------------
class TestServerModel:

    def test_create_and_retrieve(self):
        server_id = uuid.uuid4()
        Server(id=server_id, hostname="opal5.opalstack.com", type="web").save()

        retrieved = Server.objects.get(id=server_id)
        assert retrieved.hostname == "opal5.opalstack.com"

    def test_does_not_exist_exception(self):
        with pytest.raises(Server.DoesNotExist):
            Server.objects.get(id=uuid.uuid4())


# ------------------------------------------------------------------
# Domain model
# ------------------------------------------------------------------
class TestDomainModel:

    def test_create_and_retrieve(self):
        domain_id = uuid.uuid4()
        Domain(id=domain_id, name="example.com", state="ready", ready=True).save()

        retrieved = Domain.objects.get(name="example.com")
        assert retrieved.id == domain_id

    def test_name_uniqueness(self):
        Domain(id=uuid.uuid4(), name="dup.com").save()
        with pytest.raises(NotUniqueError):
            Domain(id=uuid.uuid4(), name="dup.com").save()
