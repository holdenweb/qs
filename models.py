from mongoengine import Document, DictField, StringField, IntField, BooleanField, UUIDField, URLField

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
