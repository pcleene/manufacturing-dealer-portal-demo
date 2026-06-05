"""
Main API router that aggregates all v1 endpoints.

Manufacturing Group Manufacturing OEMPartner Dealer Portal.
"""
from fastapi import APIRouter

from app.api.v1.routes import products, claims, dashboard

api_router = APIRouter()

# Include route modules
api_router.include_router(
    products.router,
    prefix="/products",
    tags=["Products"]
)

api_router.include_router(
    claims.router,
    prefix="/claims",
    tags=["Warranty Claims"]
)

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"]
)
