from mongoengine import Document, DynamicDocument, DictField, ListField, StringField, IntField, BooleanField, UUIDField, URLField

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
    # routes = ListField
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


def class_for(name):
    return {
    'Accounts': Account,
    'Addresses': Address,
    'Apps': App,
    'Certs': Cert,
    'Dnsrecords': Dnsrecord,
    'Domains': Domain,
    'Ips': Ip,
    'Mailusers': Mailuser,
    'Mariadbs': Mariadb,
    'Mariausers': Mariauser,
    'Notices': Notice,
    'OSUsers': OSUser,
    'OSVars': OSVar,
    'Psqldbs': Psqldb,
    'Psqlusers': Psqluser,
    'Quarantinedmails': Quarantinedmail,
    'Servers': Server,
    'Sites': Site,
    'Tokens': Token
    }[name]