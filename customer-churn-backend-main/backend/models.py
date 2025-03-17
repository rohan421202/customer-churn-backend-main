from mongoengine import *

class User(Document):
    user_id = IntField()
    username =  StringField(max_length=100)
    email = StringField()
    password = StringField()