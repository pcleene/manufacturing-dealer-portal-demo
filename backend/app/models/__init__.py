"""
Pydantic models for data validation and serialization.

Manufacturing Group Manufacturing OEMPartner Dealer Portal.
"""
from .products import (
    CompatibleModel,
    Pricing,
    Warehouse,
    Inventory,
    Supersession,
    RelatedProduct,
    ProductImage,
    Product,
    ProductResponse,
    ProductSearchResponse,
    ProductSummary,
    AutocompleteResult
)

from .warranty_claims import (
    StatusHistoryEntry,
    DealerInfo,
    VehicleInfo,
    CustomerInfo,
    FailureDetails,
    PartClaimed,
    LabourClaimed,
    ClaimTotals,
    SupportingDocument,
    ReviewInfo,
    PaymentInfo,
    SLAInfo,
    WarrantyClaim,
    WarrantyClaimResponse,
    WarrantyClaimSearchResponse,
    ClaimSummary,
    CreateClaimRequest,
    UpdateClaimRequest
)

from .dealers import (
    DealerAddress,
    DealerContact,
    DealerPersonnel,
    DealerMetrics,
    PortalUser,
    Dealer,
    DealerResponse
)

from .search import (
    SearchRequest,
    VectorSearchRequest,
    SearchFilters,
    PaginationInfo,
    FacetBucket,
    Facet,
    SearchResponse
)

from .dashboard import (
    DashboardStats,
    ProductDashboardStats,
    ClaimDashboardStats
)

__all__ = [
    # Products
    "CompatibleModel",
    "Pricing",
    "Warehouse",
    "Inventory",
    "Supersession",
    "RelatedProduct",
    "ProductImage",
    "Product",
    "ProductResponse",
    "ProductSearchResponse",
    "ProductSummary",
    "AutocompleteResult",
    # Warranty Claims
    "StatusHistoryEntry",
    "DealerInfo",
    "VehicleInfo",
    "CustomerInfo",
    "FailureDetails",
    "PartClaimed",
    "LabourClaimed",
    "ClaimTotals",
    "SupportingDocument",
    "ReviewInfo",
    "PaymentInfo",
    "SLAInfo",
    "WarrantyClaim",
    "WarrantyClaimResponse",
    "WarrantyClaimSearchResponse",
    "ClaimSummary",
    "CreateClaimRequest",
    "UpdateClaimRequest",
    # Dealers
    "DealerAddress",
    "DealerContact",
    "DealerPersonnel",
    "DealerMetrics",
    "PortalUser",
    "Dealer",
    "DealerResponse",
    # Search
    "SearchRequest",
    "VectorSearchRequest",
    "SearchFilters",
    "PaginationInfo",
    "FacetBucket",
    "Facet",
    "SearchResponse",
    # Dashboard
    "DashboardStats",
    "ProductDashboardStats",
    "ClaimDashboardStats"
]
