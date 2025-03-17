import pymongo

connection_string = 'mongodb+srv://Rohan:4GnQQJKXvJ06BTEx@cluster0.zom7w.mongodb.net/'
client = pymongo.MongoClient(connection_string)
db = client['customer']
collection = db['users']
