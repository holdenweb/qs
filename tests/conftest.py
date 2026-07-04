"""
Shared test configuration and fixtures.

IMPORTANT: The module-level code here runs before any test file is collected,
which means before any ``import qs`` triggers the package __init__.py.
We exploit this to redirect mongoengine.connect through mongomock so that
no real MongoDB instance is required for testing.
"""
import os

import bson
import mongoengine
import mongomock
import pytest
from bson.binary import UuidRepresentation
from bson.codec_options import CodecOptions

# ---------------------------------------------------------------------------
# 1. Patch mongoengine.connect BEFORE any qs module is imported.
#
#    qs modules do ``from mongoengine import connect`` (via qs.models.connect_db),
#    which binds to whatever ``mongoengine.connect`` is AT IMPORT TIME. Replacing
#    it here — before importing qs below — guarantees every connection goes
#    through mongomock, regardless of import order.
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

# Now it is safe to import qs: its ``from mongoengine import connect`` binds to
# the patched function above. We pull in the single source of truth for the
# UUID representation so tests encode UUIDs exactly as the application connects.
from qs.models import UUID_REPRESENTATION, connect_db  # noqa: E402

# ---------------------------------------------------------------------------
# 2. Fix pymongo 4.x / mongomock UUID compatibility.
#
#    mongomock ignores the connection's uuidRepresentation and calls
#    BSON.encode() without codec_options, so the default UNSPECIFIED is used,
#    which refuses native uuid.UUID objects. We monkey-patch BSON.encode to use
#    the SAME representation the application connects with, keeping test and
#    production encoding provably consistent.
# ---------------------------------------------------------------------------
_REPR_ENUM = {
    "standard": UuidRepresentation.STANDARD,
    "pythonLegacy": UuidRepresentation.PYTHON_LEGACY,
}
_app_codec = CodecOptions(uuid_representation=_REPR_ENUM[UUID_REPRESENTATION])
_original_bson_encode = bson.BSON.encode.__func__


@classmethod
def _patched_bson_encode(cls, document, check_keys=False, codec_options=_app_codec):
    return _original_bson_encode(cls, document, check_keys, codec_options)


bson.BSON.encode = _patched_bson_encode

# Eagerly create the initial connection via the application's own helper so
# tests that save data before calling deploy()/main() share the same database.
connect_db()

# ---------------------------------------------------------------------------
# 3. Set a fake OPALSTACK_TOKEN so that module-level guards in
#    opalsync.py and new_app.py don't call sys.exit() on import.
# ---------------------------------------------------------------------------
os.environ.setdefault("OPALSTACK_TOKEN", "test-token-for-testing")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _clean_db():
    """Drop every collection after each test for isolation."""
    yield
    from qs.models import CLASS_MAP

    for cls in CLASS_MAP.values():
        try:
            cls.drop_collection()
        except Exception:
            pass
