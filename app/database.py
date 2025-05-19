"""
Database connection and operations for the Redfin Median Price API.
"""

import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

# MongoDB configuration
MONGODB_URL = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")


async def connect_to_mongo():
    """Initialize the MongoDB connection."""
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        await collection.create_index([("state", 1), ("city", 1)])
        print("Connected to MongoDB")
        return client, collection
    except Exception as e:
        print("MongoDB_URL:", MONGODB_URL)
        print(f"Failed to connect to MongoDB: {e}")
        return None, None
        

async def close_mongo_connection(client):
    """Close the MongoDB connection."""
    if client:
        client.close()
        print("MongoDB connection closed")
        