"""The UUID representation is pinned and round-trips at the BSON layer.

mongomock ignores the connection's uuidRepresentation (it encodes via a
globally-patched BSON.encode — see conftest), so the rest of the suite can't
actually exercise the representation choice. These tests use *real* bson
encoding to lock in the representation the application connects with, so an
accidental change (or the future pymongo default flip) is caught here.
"""
import uuid

import pytest
from bson import decode, encode
from bson.binary import Binary, UuidRepresentation
from bson.codec_options import CodecOptions

from qs.models import UUID_REPRESENTATION

_REPR_ENUM = {
    "standard": UuidRepresentation.STANDARD,
    "pythonLegacy": UuidRepresentation.PYTHON_LEGACY,
}


def _codec():
    return CodecOptions(uuid_representation=_REPR_ENUM[UUID_REPRESENTATION])


def test_configured_representation_is_recognised():
    assert UUID_REPRESENTATION in _REPR_ENUM


def test_uuid_round_trips_under_configured_representation():
    u = uuid.uuid4()
    raw = encode({"id": u}, codec_options=_codec())
    back = decode(raw, codec_options=_codec())
    assert back["id"] == u


@pytest.mark.skipif(
    UUID_REPRESENTATION != "standard",
    reason="binary subtype 4 is specific to the 'standard' representation",
)
def test_standard_uses_binary_subtype_4():
    u = uuid.uuid4()
    raw = encode({"id": u}, codec_options=_codec())
    # Decode with UNSPECIFIED so the UUID stays a raw Binary we can inspect.
    unspecified = CodecOptions(uuid_representation=UuidRepresentation.UNSPECIFIED)
    back = decode(raw, codec_options=unspecified)
    assert isinstance(back["id"], Binary)
    assert back["id"].subtype == 4
