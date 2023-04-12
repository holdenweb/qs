from mongoengine import Document, DynamicDocument, DictField, ListField, StringField, IntField, BooleanField, UUIDField, URLField

class Application(Document):
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

