"""
Pydantic models for dashboard statistics and aggregated data.
Manufacturing Group Manufacturing OEMPartner Dealer Portal.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DashboardStats(BaseModel):
    """Base dashboard statistics model."""
    refreshed_at: datetime = Field(..., alias="refreshedAt")
    view_type: str = Field(..., alias="viewType")
    data_source: str = Field(..., alias="dataSource")

    model_config = {"populate_by_name": True}


# ============================================
# PRODUCT DASHBOARD STATISTICS
# ============================================

class ProductStats(DashboardStats):
    """Product catalog statistics."""
    total_products: int = Field(..., alias="totalProducts")
    by_category: List[Dict[str, Any]] = Field(..., alias="byCategory")
    by_status: List[Dict[str, Any]] = Field(..., alias="byStatus")
    low_stock_count: int = Field(..., alias="lowStockCount")
    new_this_quarter: int = Field(..., alias="newThisQuarter")
    by_subcategory: Optional[List[Dict[str, Any]]] = Field(None, alias="bySubcategory")
    top_searched: Optional[List[Dict[str, Any]]] = Field(None, alias="topSearched")

    model_config = {"populate_by_name": True}


class ProductDashboardStats(BaseModel):
    """Complete product dashboard statistics."""
    total_products: int = Field(..., alias="totalProducts")
    by_category: Dict[str, int] = Field(..., alias="byCategory")
    low_stock_alerts: int = Field(..., alias="lowStockAlerts")
    new_this_quarter: int = Field(..., alias="newThisQuarter")
    top_searched: Optional[List[Dict[str, Any]]] = Field(None, alias="topSearched")
    refreshed_at: datetime = Field(..., alias="refreshedAt")

    model_config = {"populate_by_name": True}


# ============================================
# WARRANTY CLAIMS DASHBOARD STATISTICS
# ============================================

class ClaimStatusCounts(BaseModel):
    """Claim counts by status."""
    pending: int = 0
    submitted: int = 0
    under_review: int = Field(0, alias="underReview")
    approved: int = 0
    rejected: int = 0
    paid: int = 0

    model_config = {"populate_by_name": True}


class WarrantyClaimStats(DashboardStats):
    """Warranty claim statistics (per dealer or global)."""
    dealer_id: Optional[str] = Field(None, alias="dealerId")
    dealer_name: Optional[str] = Field(None, alias="dealerName")
    total_claims: int = Field(..., alias="totalClaims")
    status_counts: ClaimStatusCounts = Field(..., alias="statusCounts")
    total_claim_value: float = Field(..., alias="totalClaimValue")
    total_approved_value: float = Field(..., alias="totalApprovedValue")
    avg_processing_days: float = Field(..., alias="avgProcessingDays")
    rejection_rate: float = Field(..., alias="rejectionRate")

    model_config = {"populate_by_name": True}


class ClaimsTrend(BaseModel):
    """Monthly claims trend data."""
    period: str  # YYYY-MM format
    claims_count: int = Field(..., alias="claimsCount")
    total_value: float = Field(..., alias="totalValue")
    approved_count: int = Field(..., alias="approvedCount")
    rejected_count: int = Field(..., alias="rejectedCount")
    approval_rate: float = Field(..., alias="approvalRate")

    model_config = {"populate_by_name": True}


class ClaimsByCategory(BaseModel):
    """Claims breakdown by failure category."""
    category: str
    count: int
    total_value: float = Field(..., alias="totalValue")
    approval_rate: float = Field(..., alias="approvalRate")

    model_config = {"populate_by_name": True}


class ClaimDashboardStats(BaseModel):
    """Complete warranty claims dashboard statistics for a dealer."""
    total_claims: int = Field(..., alias="totalClaims")
    status_counts: ClaimStatusCounts = Field(..., alias="statusCounts")
    avg_processing_days: float = Field(..., alias="avgProcessingDays")
    claims_value_this_month: float = Field(..., alias="claimsValueThisMonth")
    rejection_rate: float = Field(..., alias="rejectionRate")
    by_category: Optional[List[ClaimsByCategory]] = Field(None, alias="byCategory")
    trend: Optional[List[ClaimsTrend]] = None
    refreshed_at: datetime = Field(..., alias="refreshedAt")

    model_config = {"populate_by_name": True}


# ============================================
# COMBINED DASHBOARD RESPONSE
# ============================================

class DealerDashboardResponse(BaseModel):
    """Combined dashboard response for a dealer."""
    dealer_id: str = Field(..., alias="dealerId")
    dealer_name: str = Field(..., alias="dealerName")
    products: ProductDashboardStats
    claims: ClaimDashboardStats
    refreshed_at: datetime = Field(..., alias="refreshedAt")

    model_config = {"populate_by_name": True}


# ============================================
# MATERIALIZED VIEW REFRESH
# ============================================

class ViewRefreshRequest(BaseModel):
    """Request to refresh materialized views."""
    views: Optional[List[str]] = None  # Specific views or all
    force: bool = False  # Force refresh even if recent


class ViewRefreshResponse(BaseModel):
    """Response after refreshing materialized views."""
    refreshed_views: List[str] = Field(..., alias="refreshedViews")
    skipped_views: List[str] = Field(default_factory=list, alias="skippedViews")
    duration_ms: int = Field(..., alias="durationMs")
    message: str

    model_config = {"populate_by_name": True}
