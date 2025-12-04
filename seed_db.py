import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId

load_dotenv()

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME", "emogo_db")


async def main():
    if not MONGODB_URI:
        print("MONGODB_URI not set. Please create a .env or set the environment variable.")
        return

    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    coll = db["records"]

    docs = [
        {
            "_id": ObjectId("69313e6a0af14e4d1806d0a4"),
            "user_id": "u1",
            "score": 87,
            "video_url": "https://example.com/demo3.mp4",
            "latitude": 25.0423,
            "longitude": 121.5648,
        },
        {
            "_id": ObjectId("69313e820af14e4d1806d0a6"),
            "user_id": "u2",
            "score": 75,
            "video_url": "https://example.com/demo2.mp4",
            "latitude": 25.0321,
            "longitude": 121.5487,
        },
    ]

    for doc in docs:
        oid = doc["_id"]
        # replace_one with upsert=True will insert if not exists, or replace existing document
        result = await coll.replace_one({"_id": oid}, doc, upsert=True)
        if result.upserted_id:
            print(f"Inserted doc with _id={result.upserted_id}")
        else:
            print(f"Replaced/updated doc with _id={oid}")

    # optional: print count
    count = await coll.count_documents({})
    print(f"Total documents in 'records': {count}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
