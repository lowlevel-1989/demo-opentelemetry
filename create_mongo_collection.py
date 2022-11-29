from pymongo import MongoClient


mongo_client = MongoClient("mongodb://some-mongo")
# Create DB
mongo_db = mongo_client["users_count"]
# Create collection
collection = mongo_db["users"]

initial_data = {
    "counter": 0,
}

x = collection.insert_one(initial_data)
