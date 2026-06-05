"""
Configuration settings for the Manufacturing Group Manufacturing OEMPartner Dealer Portal.
Uses Pydantic Settings for environment variable management.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "OEMPartner Dealer Portal"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8001

    # MongoDB Atlas
    mongodb_url: str = "mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<db>"
    mongodb_db_name: str = "OEMPartner_dealer_portal"
    mongodb_max_pool_size: int = 50
    mongodb_min_pool_size: int = 10

    # Atlas Search Indexes - Products
    products_search_index: str = "products_search_index"
    products_vector_index: str = "products_vector_index"

    # Atlas Search Indexes - Warranty Claims
    claims_search_index: str = "warrantyClaims_search_index"
    claims_vector_index: str = "warrantyClaims_vector_index"

    # Voyage AI API (for embeddings)
    voyage_api_key: Optional[str] = None
    voyage_model: str = "voyage-2"
    voyage_dimensions: int = 1024

    # Search Settings
    default_search_limit: int = 20
    max_search_limit: int = 100
    vector_num_candidates: int = 100

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174"
    ]

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Materialized Views Refresh Schedule (cron expressions)
    refresh_product_stats_cron: str = "*/15 * * * *"  # Every 15 minutes
    refresh_claim_stats_cron: str = "*/15 * * * *"  # Every 15 minutes
    refresh_claims_trend_cron: str = "0 * * * *"  # Hourly

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra env vars that aren't in the model
    )


# Create global settings instance
settings = Settings()
