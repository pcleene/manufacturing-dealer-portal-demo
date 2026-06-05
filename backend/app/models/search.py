"""
Pydantic models for search requests and responses.
Manufacturing Group Manufacturing OEMPartner Dealer Portal.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class SearchRequest(BaseModel):
    """Text search request model."""
    search_text: Optional[str] = Field(None, alias="searchText")
    filters: Optional[Dict[str, Any]] = None
    limit: int = 20
    cursor: Optional[str] = None
    direction: str = "next"  # "next" or "prev"
    use_facets: bool = True

    model_config = {"populate_by_name": True}


class VectorSearchRequest(BaseModel):
    """Natural language vector search request."""
    query: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = 20
    num_candidates: int = 100
    include_query: bool = Field(False, alias="includeQuery", description="Include MongoDB query in response (for demos)")

    model_config = {"populate_by_name": True}


class SearchFilters(BaseModel):
    """Generic search filters base class."""
    model_config = {"populate_by_name": True}


class ProductSearchFilters(SearchFilters):
    """Search filters for products."""
    category: Optional[List[str]] = None
    subcategory: Optional[List[str]] = None
    model_series: Optional[List[str]] = Field(None, alias="modelSeries")
    model_year: Optional[List[int]] = Field(None, alias="modelYear")
    availability_status: Optional[List[str]] = Field(None, alias="availabilityStatus")
    min_price: Optional[float] = Field(None, alias="minPrice")
    max_price: Optional[float] = Field(None, alias="maxPrice")
    warehouse_region: Optional[List[str]] = Field(None, alias="warehouseRegion")


class ClaimSearchFilters(SearchFilters):
    """Search filters for warranty claims."""
    status: Optional[List[str]] = None
    date_from: Optional[str] = Field(None, alias="dateFrom")  # ISO date string
    date_to: Optional[str] = Field(None, alias="dateTo")
    vehicle_model: Optional[List[str]] = Field(None, alias="vehicleModel")
    claim_type: Optional[List[str]] = Field(None, alias="claimType")  # Parts, Labour, Parts + Labour
    failure_category: Optional[List[str]] = Field(None, alias="failureCategory")
    min_amount: Optional[float] = Field(None, alias="minAmount")
    max_amount: Optional[float] = Field(None, alias="maxAmount")
    dealer_id: Optional[str] = Field(None, alias="dealerId")


class PaginationInfo(BaseModel):
    """Pagination information in search results."""
    limit: int
    has_more: bool = Field(..., alias="hasMore")
    next_cursor: Optional[str] = Field(None, alias="nextCursor")
    prev_cursor: Optional[str] = Field(None, alias="prevCursor")
    total_count: Optional[int] = Field(None, alias="totalCount")
    current_page_size: int = Field(..., alias="currentPageSize")

    model_config = {"populate_by_name": True}


class FacetBucket(BaseModel):
    """Individual facet bucket with value and count."""
    value: str
    count: int


class Facet(BaseModel):
    """Facet definition for filtering UI."""
    field: str
    field_key: str = Field(..., alias="fieldKey")
    buckets: List[FacetBucket]

    model_config = {"populate_by_name": True}


class SearchResponse(BaseModel):
    """Generic search response."""
    results: List[Any]
    pagination: PaginationInfo
    facets: Optional[List[Facet]] = None
    query: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None

    model_config = {"populate_by_name": True}


class AutocompleteRequest(BaseModel):
    """Autocomplete request model."""
    query: str
    field: str = "name"  # name, partNumber
    limit: int = 10


class AutocompleteResponse(BaseModel):
    """Autocomplete response model."""
    suggestions: List[Dict[str, Any]]
    query: str
