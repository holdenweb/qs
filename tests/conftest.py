"""
Shared test configuration and fixtures.

IMPORTANT: The module-level code here runs before any test file is collected,
which means before any ``import qs`` triggers the package __init__.py.
We exploit this to redirect mongoengine.connect through mongomock so that
no real MongoDB instance is required for testing.
"""
import os
import uuid

import bson
from bson.binary import UuidRepresentation
from bson.codec_options import CodecOptions
import mongomock
import mongoengine
import pytest

# ---------------------------------------------------------------------------
# 0. Fix pymongo 4.x / mongomock UUID compatibility.
#
#    mongomock calls BSON.encode() without codec_options, so the default
#    UuidRepresentation.UNSPECIFIED is used, which refuses native uuid.UUID
#    objects.  We monkey-patch BSON.encode to default to STANDARD instead.
# ---------------------------------------------------------------------------
_standard_codec = CodecOptions(uuid_representation=UuidRepresentation.STANDARD)
_original_bson_encode = bson.BSON.encode.__func__


@classmethod
def _patched_bson_encode(cls, document, check_keys=False, codec_options=_standard_codec):
    return _original_bson_encode(cls, document, check_keys, codec_options)


bson.BSON.encode = _patched_bson_encode

# ---------------------------------------------------------------------------
# 1. Patch mongoengine.connect BEFORE any qs module is imported.
#
#    qs/deploy.py calls ``connect('opalstack')`` inside deploy().
#    qs/opalsync.py and qs/new_app.py also call connect().
#    By replacing the function here we guarantee every call goes through
#    mongomock regardless of import order.
# ---------------------------------------------------------------------------
_original_connect = mongoengine.connect


def _mock_connect(*args, **kwargs):
    """Wrapper that forces mongomock as the backend for all connections.

    If a connection with the requested alias already exists we return it
    as-is so that in-memory data is preserved (mongomock databases live
    only as long as the client object).
    """
    kwargs["mongo_client_class"] = mongomock.MongoClient
    alias = kwargs.get("alias", "default")
    # Reuse an existing connection to keep in-memory data intact.
    try:
        return _original_connect(*args, **kwargs)
    except Exception:
        # "alias already exists" — return the existing connection.
        from mongoengine.connection import _connections
        return _connections.get(alias)


mongoengine.connect = _mock_connect

# Eagerly create the initial mongomock connection so that tests which
# save data before calling deploy()/main() share the same database.
_mock_connect("opalstack")

# ---------------------------------------------------------------------------
# 2. Set a fake OPALSTACK_TOKEN so that module-level guards in
#    opalsync.py and new_app.py don't call sys.exit() on import.
# ---------------------------------------------------------------------------
os.environ.setdefault("OPALSTACK_TOKEN", "test-token-for-testing")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
ALL_TYPE_NAMES = [
    "Accounts", "Addresses", "Apps", "Certs", "Dnsrecords",
    "Domains", "Ips", "Mailusers", "Mariadbs", "Mariausers",
    "Notices", "OSUsers", "OSVars", "Psqldbs", "Psqlusers",
    "Quarantinedmails", "Servers", "Sites", "Tokens",
]


@pytest.fixture(autouse=True)
def _clean_db():
    """Drop every collection after each test for isolation."""
    yield
    from qs.models import class_for

    for name in ALL_TYPE_NAMES:
        try:
            class_for(name).drop_collection()
        except Exception:
            pass
