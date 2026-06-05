"""
Dashboard endpoints for OEMPartner Dealer Portal.
Provides aggregated statistics from materialized views.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
import logging

from app.database import get_database
from app.services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_dashboard_service():
    """Dependency to get dashboard service instance."""
    db = await get_database()
    return DashboardService(db)


# ===========================
# PRODUCTS DASHBOARD ENDPOINTS
# ===========================

@router.get("/products/stats")
async def get_product_stats(
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get product catalog statistics for dashboard summary cards.

    Returns:
    - Total products in catalog
    - Products by category
    - Low stock alerts count
    - New products this quarter
    - Top searched products
    """
    try:
        stats = await service.get_product_stats()
        return stats

    except Exception as e:
        logger.error(f"Error retrieving product stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stats: {str(e)}")


# ==============================
# CLAIMS DASHBOARD ENDPOINTS
# ==============================

@router.get("/claims/stats")
async def get_claim_stats(
    dealer_id: Optional[str] = Query(None, alias="dealerId", description="Dealer ID for dealer-specific stats"),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get warranty claim statistics for dashboard summary cards.

    Returns:
    - Total claims submitted
    - Claims by status
    - Average processing time
    - Claims value this month
    - Rejection rate
    """
    try:
        stats = await service.get_claim_stats(dealer_id=dealer_id)
        return stats

    except Exception as e:
        logger.error(f"Error retrieving claim stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stats: {str(e)}")


@router.get("/claims/trend")
async def get_claims_trend(
    months: int = Query(12, ge=1, le=24, description="Number of months to retrieve"),
    dealer_id: Optional[str] = Query(None, alias="dealerId", description="Dealer ID for dealer-specific trend"),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get monthly claims trend for charts.

    Returns monthly data:
    - Claims count
    - Total value
    - Approved/Rejected counts
    - Approval rate
    """
    try:
        trend = await service.get_claims_trend(months=months, dealer_id=dealer_id)
        return {"trend": trend, "months": months}

    except Exception as e:
        logger.error(f"Error retrieving claims trend: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trend: {str(e)}")


# ====================================
# TOP DEALERS ENDPOINT
# ====================================

@router.get("/dealers/top")
async def get_top_dealers(
    limit: int = Query(10, ge=1, le=50, description="Number of top dealers to return"),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get top dealers by claim volume.

    Returns ranked dealer list with:
    - Total claims
    - Total claim value
    - Approval rate
    - SLA breached count
    """
    try:
        dealers = await service.get_top_dealers(limit=limit)
        return {"dealers": dealers, "limit": limit}

    except Exception as e:
        logger.error(f"Error retrieving top dealers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve top dealers: {str(e)}")


# ====================================
# COMBINED DEALER DASHBOARD
# ====================================

@router.get("/dealer/{dealer_id}")
async def get_dealer_dashboard(
    dealer_id: str,
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get complete dashboard data for a specific dealer.

    Combines:
    - Dealer information and metrics
    - Product catalog stats
    - Claim statistics (dealer-specific)
    - Claims trend (last 6 months)
    """
    try:
        dashboard = await service.get_dealer_dashboard(dealer_id=dealer_id)
        return dashboard

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving dealer dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dashboard: {str(e)}")


# ====================================
# MATERIALIZED VIEWS REFRESH ENDPOINT
# ====================================

@router.post("/refresh")
async def refresh_materialized_views(
    views: List[str] = Query(["all"], description="Views to refresh"),
    force: bool = Query(False, description="Force refresh bypassing cache"),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Manually refresh materialized views.

    Available views:
    - product_stats
    - claim_stats
    - claims_trend
    - all (default - refresh all views)
    """
    try:
        results = await service.refresh_views(views, force)
        return results

    except Exception as e:
        logger.error(f"Error refreshing materialized views: {e}")
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")
