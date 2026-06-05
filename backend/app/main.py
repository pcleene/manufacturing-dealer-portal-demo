"""
Manufacturing Group Manufacturing OEMPartner Dealer Portal - FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager
from typing import Any
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from bson import ObjectId

from app.config import settings
from app.database import db_manager
from app.api.v1.router import api_router


from datetime import datetime


class MongoJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles MongoDB ObjectId and datetime."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def custom_json_serializer(obj: Any) -> str:
    """Custom JSON serializer using MongoJSONEncoder."""
    return json.dumps(obj, cls=MongoJSONEncoder)


class MongoJSONResponse(JSONResponse):
    """Custom JSONResponse that handles MongoDB ObjectId."""
    def render(self, content: Any) -> bytes:
        return custom_json_serializer(content).encode("utf-8")

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting OEMPartner Dealer Portal API")
    logger.info(f"Environment: {'Development' if settings.debug else 'Production'}")

    # Connect to MongoDB
    await db_manager.connect()
    logger.info("Database connection established")

    yield

    # Shutdown
    logger.info("Shutting down OEMPartner Dealer Portal API")
    await db_manager.disconnect()
    logger.info("Database connection closed")


# Create FastAPI application with custom JSON response
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Dealer portal for Manufacturing Group Malaysia - OEMPartner motorcycle product catalog and warranty claims management",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    default_response_class=MongoJSONResponse
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "message": "OEMPartner Dealer Portal API",
        "version": settings.app_version,
        "status": "running",
        "docs": "/api/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Test database connection
        db = db_manager.get_database()
        await db.command('ping')

        return {
            "status": "healthy",
            "database": "connected",
            "version": settings.app_version
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
