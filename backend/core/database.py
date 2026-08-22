import logging
from typing import Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from pymongo.database import Database

from backend.core.config import settings

logger = logging.getLogger("aerix.db")

class MongoDBManager:
    """Manages asynchronous (Motor) and synchronous (PyMongo) connections to MongoDB."""
    
    def __init__(self):
        self._async_client: Optional[AsyncIOMotorClient] = None
        self._sync_client: Optional[MongoClient] = None
        self._connected: bool = False

    def connect(self) -> bool:
        """Establish connection to MongoDB"""
        try:
            # Sync client for immediate verification & background worker use
            self._sync_client = MongoClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=2500,
                connectTimeoutMS=2500
            )
            # Trigger server selection
            self._sync_client.admin.command("ping")

            # Async client for FastAPI coroutines
            self._async_client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=2500
            )
            self._connected = True
            logger.info("Successfully connected to MongoDB [%s / %s]",
                        settings.mask_url(settings.MONGODB_URL), settings.MONGODB_DB_NAME)
            return True
        except Exception as e:
            self._connected = False
            logger.warning("MongoDB connection failed (%s). Operating in local file cache mode.", e)
            return False

    def close(self):
        """Close MongoDB connections"""
        if self._async_client:
            self._async_client.close()
        if self._sync_client:
            self._sync_client.close()
        self._connected = False
        logger.info("MongoDB connection closed.")

    @property
    def is_connected(self) -> bool:
        return self._connected

    def get_async_db(self) -> Optional[AsyncIOMotorDatabase]:
        """Returns the async Motor database instance, or None if disconnected."""
        if not self._connected or not self._async_client:
            return None
        return self._async_client[settings.MONGODB_DB_NAME]

    def get_sync_db(self) -> Optional[Database]:
        """Returns the synchronous PyMongo database instance, or None if disconnected."""
        if not self._connected or not self._sync_client:
            return None
        return self._sync_client[settings.MONGODB_DB_NAME]


# Singleton instance
mongo_manager = MongoDBManager()


def get_db() -> Optional[AsyncIOMotorDatabase]:
    """FastAPI dependency for accessing the async database"""
    return mongo_manager.get_async_db()
