import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

_client = None

def get_db():
    global _client
    if _client is None:
        _client = MongoClient(os.getenv("MONGO_URI"))
    return _client[os.getenv("DB_NAME", "chatbot_db")]

def save_conversation(user_input: str, bot_response: str):
    db = get_db()
    db.conversations.insert_one({
        "user": user_input,
        "bot": bot_response,
        "timestamp": datetime.utcnow(),
    })
