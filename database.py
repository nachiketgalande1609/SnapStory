from pymongo import MongoClient
from config import MONGO_URI

# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client['SnapStory']