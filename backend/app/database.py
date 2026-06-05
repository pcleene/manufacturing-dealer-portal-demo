"""
MongoDB database connection and management.
Uses PyMongo 4.5+ native async API.

Manufacturing Group Manufacturing OEMPartner Dealer Portal.
"""
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.asynchronous.collection import AsyncCollection
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages MongoDB Atlas connection lifecycle."""

    def __init__(self):
        self.client: Optional[AsyncMongoClient] = None
        self.database: Optional[AsyncDatabase] = None

    async def connect(self):
        """Establish connection to MongoDB Atlas."""
        try:
            logger.info(f"Connecting to MongoDB: {settings.mongodb_db_name}")

            self.client = AsyncMongoClient(
                settings.mongodb_url,
                maxPoolSize=settings.mongodb_max_pool_size,
                minPoolSize=settings.mongodb_min_pool_size,
            )

            self.database = self.client[settings.mongodb_db_name]

            # Verify connection
            await self.client.admin.command('ping')

            logger.info("Successfully connected to MongoDB Atlas")

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            logger.info("Disconnecting from MongoDB")
            await self.client.close()
            logger.info("MongoDB connection closed")

    def get_database(self) -> AsyncDatabase:
        """Get database instance."""
        if self.database is None:
            raise RuntimeError("Database not initialized. Call connect() first.")
        return self.database

    def get_collection(self, collection_name: str) -> AsyncCollection:
        """Get a specific collection."""
        db = self.get_database()
        return db[collection_name]


# Global database manager instance
db_manager = DatabaseManager()


async def get_database() -> AsyncDatabase:
    """
    Dependency function to get database instance.
    Use this in FastAPI route dependencies.
    """
    return db_manager.get_database()


# OEMPartner Dealer Portal Collections
async def get_products_collection():
    """Get products collection."""
    return db_manager.get_collection("products")


async def get_claims_collection():
    """Get warranty claims collection."""
    return db_manager.get_collection("warrantyClaims")


async def get_dealers_collection():
    """Get dealers collection."""
    return db_manager.get_collection("dealers")


# Materialized view collections
async def get_mv_product_stats():
    """Get product statistics materialized view."""
    return db_manager.get_collection("mv_product_stats")


async def get_mv_claim_stats():
    """Get claim statistics materialized view."""
    return db_manager.get_collection("mv_claim_stats")


async def get_mv_dealer_claim_stats():
    """Get dealer claim statistics materialized view."""
    return db_manager.get_collection("mv_dealer_claim_stats")


async def get_mv_claims_trend():
    """Get claims trend materialized view."""
    return db_manager.get_collection("mv_claims_trend")
