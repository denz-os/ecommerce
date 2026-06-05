"""
config/database.py
──────────────────
Single async MongoDB client shared across the whole app.
Motor wraps PyMongo with asyncio support so FastAPI never blocks.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str
    MONGO_DB: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_MB: int = 5

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# ── Motor client ──────────────────────────────────────────────
client: AsyncIOMotorClient = None


async def connect_db():
    """Called on app startup — creates the Motor client."""
    global client
    client = AsyncIOMotorClient(settings.MONGO_URI)
    print(f"✅ MongoDB connected → {settings.MONGO_DB}")


async def close_db():
    """Called on app shutdown — closes the Motor client."""
    global client
    if client:
        client.close()
        print("🛑 MongoDB connection closed")


def get_db():
    """Returns the database object. Used as a FastAPI dependency."""
    return client[settings.MONGO_DB]