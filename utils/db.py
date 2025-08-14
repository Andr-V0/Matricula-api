from pymongo import MongoClient
import os
from dotenv import load_dotenv
import certifi

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"), tlsCAFile=certifi.where())
db = client[os.getenv("DATABASE_NAME")]