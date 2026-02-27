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
#    qs/__init__.py:18 runs ``conn = connect('opalstack')`` at import time.
#    qs/opalsync.py:47 and qs/new_app.py:61 also call connect().
#    By replacing the function here we guarantee every call goes through
#    mongomock regardless of import order.
# ---------------------------------------------------------------------------
_original_connect = mongoengine.connect


def _mock_connect(*args, **kwargs):
    """Wrapper that forces mongomock as the backend for all connections."""
    kwargs["mongo_client_class"] = mongomock.MongoClient
    alias = kwargs.get("alias", "default")
    # Disconnect any existing connection with this alias to avoid
    # mongoengine's "alias already exists" error on repeated connect().
    try:
        mongoengine.disconnect(alias=alias)
    except Exception:
        pass
    return _original_connect(*args, **kwargs)


mongoengine.connect = _mock_connect

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
