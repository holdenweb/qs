from mongoengine import (
    BooleanField,
    DictField,
    Document,
    DynamicDocument,
    IntField,
    ListField,
    StringField,
    URLField,
    UUIDField,
    connect,
)

# Name of the local MongoDB database that mirrors Opalstack state.
DB_NAME = "opalstack"

# UUID wire representation for the connection. The models are UUID-heavy, so
# this MUST be identical everywhere that touches the database (opalsync/new_app
# write, deploy reads) or UUID lookups silently miss. Pinning it explicitly
# also silences mongoengine's deprecation warning and is future-proof against
# pymongo changing the default to 'unspecified'. Change this in ONE place only.
UUID_REPRESENTATION = "standard"


def connect_db(**kwargs):
    """Connect to the qs MongoDB with an explicit, consistent UUID representation.

    All qs entry points use this rather than calling ``connect`` directly, so
    the database name and UUID representation can never drift between the write
    and read paths.
    """
    return connect(DB_NAME, uuidRepresentation=UUID_REPRESENTATION, **kwargs)


class App(Document):
    id = UUIDField(primary_key=True)
    state = StringField()
    ready = BooleanField()
    name = StringField(unique=True)
    server = UUIDField()
    osuser = UUIDField()
    type = StringField()
    port = IntField()
    installer_url = URLField(required=False)
    json = DictField()
    osuser_name = StringField()


class Domain(Document):
    id = UUIDField(primary_key=True)
    state = StringField()
    ready = BooleanField()
    name = StringField(unique=True)
    dkim_record = StringField()
    is_valid_hostname = BooleanField()
    dkim_privkey = StringField()
    dkim_pubkey = StringField()


class Site(DynamicDocument):
    id = UUIDField(primary_key=True)
    state = StringField()
    ready = BooleanField()
    name = StringField(unique=True)
    server = UUIDField()
    ip4 = UUIDField()
    ip6 = UUIDField(required=False)
    disabled = BooleanField()
    domains = ListField(UUIDField())
    #  routes = ListField
    generate_le = BooleanField()
    cert = UUIDField()
    redirect = BooleanField()


class Account(DynamicDocument):
    id = UUIDField(primary_key=True)


class Address(DynamicDocument):
    id = UUIDField(primary_key=True)


class Cert(DynamicDocument):
    id = UUIDField(primary_key=True)


class Dnsrecord(DynamicDocument):
    id = UUIDField(primary_key=True)


class Ip(DynamicDocument):
    id = UUIDField(primary_key=True)


class Mailuser(DynamicDocument):
    id = UUIDField(primary_key=True)


class Mariadb(DynamicDocument):
    id = UUIDField(primary_key=True)


class Mariauser(DynamicDocument):
    id = UUIDField(primary_key=True)


class Notice(DynamicDocument):
    id = UUIDField(primary_key=True)


class OSUser(DynamicDocument):
    id = UUIDField(primary_key=True)


class OSVar(DynamicDocument):
    id = UUIDField(primary_key=True)


class Psqldb(DynamicDocument):
    id = UUIDField(primary_key=True)


class Psqluser(DynamicDocument):
    id = UUIDField(primary_key=True)


class Quarantinedmail(DynamicDocument):
    id = UUIDField(primary_key=True)


class Server(DynamicDocument):
    id = UUIDField(primary_key=True)
    hostname = StringField()
    type = StringField()


class Token(DynamicDocument):
    name = StringField(primary_key=True)
    key = StringField()


# Single source of truth mapping Opalstack resource type names to their
# document classes. Both class_for() and the list of type names iterated
# by opalsync are derived from this, so they can never drift apart.
CLASS_MAP = {
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

# Type names in a stable order (dicts preserve insertion order).
TYPE_NAMES = tuple(CLASS_MAP)


def class_for(name):
    return CLASS_MAP[name]
