"""
Warranty Claims API routes for the OEMPartner Dealer Portal.

Provides endpoints for searching, creating, and managing warranty claims.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Optional, List

from app.database import get_database
from app.services.claim_service import ClaimService
from app.models.search import VectorSearchRequest
from app.models.warranty_claims import CreateClaimRequest, UpdateClaimRequest
from app.utils import serialize_doc, serialize_docs

router = APIRouter()


def get_claim_service(db=Depends(get_database)) -> ClaimService:
    """Dependency to get ClaimService instance."""
    return ClaimService(db)


@router.get("/search", response_model=None)
async def search_claims(
    search_text: Optional[str] = Query(None, description="Text to search for"),
    status: Optional[List[str]] = Query(None, description="Filter by status"),
    date_from: Optional[str] = Query(None, alias="dateFrom", description="Filter from date (ISO format)"),
    date_to: Optional[str] = Query(None, alias="dateTo", description="Filter to date (ISO format)"),
    vehicle_model: Optional[List[str]] = Query(None, alias="vehicleModel", description="Filter by vehicle model"),
    claim_type: Optional[List[str]] = Query(None, alias="claimType", description="Filter by claim type"),
    failure_category: Optional[List[str]] = Query(None, alias="failureCategory", description="Filter by failure category"),
    min_amount: Optional[float] = Query(None, alias="minAmount", description="Minimum claim amount"),
    max_amount: Optional[float] = Query(None, alias="maxAmount", description="Maximum claim amount"),
    dealer_id: Optional[str] = Query(None, alias="dealerId", description="Filter by dealer ID"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    direction: str = Query("next", regex="^(next|prev)$", description="Pagination direction"),
    use_facets: bool = Query(True, alias="useFacets", description="Include facets in response"),
    include_query: bool = Query(False, alias="includeQuery", description="Include MongoDB query in response (for demos)"),
    service: ClaimService = Depends(get_claim_service)
) -> dict:
    """
    Search warranty claims with full-text search, filters, and faceting.
    """
    filters = {
        "status": status,
        "date_from": date_from,
        "date_to": date_to,
        "vehicle_model": vehicle_model,
        "claim_type": claim_type,
        "failure_category": failure_category,
        "min_amount": min_amount,
        "max_amount": max_amount,
        "dealer_id": dealer_id
    }
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}

    result = await service.search_claims(
        search_text=search_text,
        filters=filters,
        limit=limit,
        cursor=cursor,
        direction=direction,
        use_facets=use_facets,
        include_query=include_query
    )

    return result


@router.post("/search/semantic", response_model=None)
async def semantic_search_claims(
    request: VectorSearchRequest,
    service: ClaimService = Depends(get_claim_service)
) -> dict:
    """
    Semantic search for warranty claims using natural language.

    Example queries:
    - "Y15ZR engine claims last 3 months"
    - "rejected claims for fuel pump issues"
    - "high value claims from Selangor dealers"
    """
    result = await service.vector_search_claims(
        query=request.query,
        filters=request.filters or {},
        limit=request.limit,
        num_candidates=request.num_candidates,
        include_query=request.include_query
    )

    # Serialize MongoDB documents for JSON response
    result["results"] = serialize_docs(result.get("results", []))

    return result


@router.get("/autocomplete", response_model=None)
async def autocomplete_claims(
    q: str = Query(..., min_length=2, description="Search query"),
    field: str = Query("claimId", regex="^(claimId|customerName|registration)$", description="Field to autocomplete"),
    limit: int = Query(10, ge=1, le=20, description="Max suggestions"),
    service: ClaimService = Depends(get_claim_service)
) -> dict:
    """
    Get autocomplete suggestions for warranty claims.
    
    Supports autocomplete on:
    - claimId: Claim ID (e.g., "WC-2024-KL-00456")
    - customerName: Customer name
    - registration: Vehicle registration number
    """
    suggestions = await service.autocomplete_claims(query=q, field=field, limit=limit)
    return {"suggestions": suggestions}


@router.post("", response_model=None)
async def create_claim(
    dealer_id: str = Query(..., alias="dealerId", description="Dealer ID creating the claim"),
    request: CreateClaimRequest = Body(...),
    service: ClaimService = Depends(get_claim_service)
) -> dict:
    """
    Create a new warranty claim (draft status).

    The claim will be created in Draft status. Use the submit endpoint to submit for review.
    """
    try:
        claim = await service.create_claim(
            dealer_id=dealer_id,
            claim_data=request.model_dump(by_alias=True)
        )
        return {"claim": serialize_doc(claim), "message": "Claim created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/by-dealer/{dealer_id}", response_model=None)
async def get_claims_by_dealer(
    dealer_id: str,
    status: Optional[List[str]] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Max claims"),
    offset: int = Query(0, ge=0, description="Skip count"),
    service: ClaimService = Depends(get_claim_service)
) -> dict:
    """
    Get warranty claims for a specific dealer.
    """
    claims = await service.get_claims_by_dealer(
        dealer_id=dealer_id,
        status=status,
        limit=limit,
        offset=offset
    )

    return {
        "dealerId": dealer_id,
        "claims": serialize_docs(claims),
        "count": len(claims),
        "limit": limit,
        "offset": offset
    }


@router.get("/statistics", response_model=None)
async def get_claim_statistics(
    dealer_id: Optional[str] = Query(None, alias="dealerId", description="Dealer ID for dealer-specific stats"),
    service: ClaimService = Depends(get_claim_service)
) -> dict:
    """
    Get warranty claim statistics for dashboard.

    Returns:
    - Total claims count
    - Claims by status
    - Average processing time
    - Claims value this month
    - Rejection rate
    """
    stats = await service.get_claim_statistics(dealer_id=dealer_id)
    return stats


@router.get("/trend", response_model=None)
async def get_claim_trend(
    months: int = Query(12, ge=1, le=24, description="Number of months"),
    dealer_id: Optional[str] = Query(None, alias="dealerId", description="Dealer ID for dealer-specific trend"),
    service: ClaimService = Depends(get_claim_service)
) -> dict:
    """
    Get monthly claims trend for charts.
    """
    trend = await service.get_claim_trend(months=months, dealer_id=dealer_id)
    return {"trend": serialize_docs(trend), "months": months}


@router.get("/{claim_id}", response_model=None)
async def get_claim_by_id(
    claim_id: str,
    service: ClaimService = Depends(get_claim_service)
) -> dict:
    """
    Get a single warranty claim by claim ID.

    Args:
        claim_id: Warranty claim ID (e.g., "WC-2024-KL-00456")
    """
    claim = await service.get_claim_by_id(claim_id)

    if not claim:
        raise HTTPException(status_code=404, detail=f"Claim not found: {claim_id}")

    return {"claim": serialize_doc(claim)}


@router.put("/{claim_id}", response_model=None)
async def update_claim(
    claim_id: str,
    updated_by: str = Query(..., alias="updatedBy", description="User ID making the update"),
    request: UpdateClaimRequest = Body(...),
    service: ClaimService = Depends(get_claim_service)
) -> dict:
    """
    Update an existing warranty claim.

    Only claims in Draft status can be updated.
    """
    try:
        claim = await service.update_claim(
            claim_id=claim_id,
            update_data=request.model_dump(by_alias=True, exclude_none=True),
            updated_by=updated_by
        )

        if not claim:
            raise HTTPException(status_code=404, detail=f"Claim not found: {claim_id}")

        return {"claim": serialize_doc(claim), "message": "Claim updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{claim_id}/submit", response_model=None)
async def submit_claim(
    claim_id: str,
    submitted_by: str = Query(..., alias="submittedBy", description="User ID submitting the claim"),
    service: ClaimService = Depends(get_claim_service)
) -> dict:
    """
    Submit a draft claim for review.

    Changes status from Draft to Submitted and starts SLA timers.
    """
    try:
        claim = await service.submit_claim(
            claim_id=claim_id,
            submitted_by=submitted_by
        )

        if not claim:
            raise HTTPException(status_code=404, detail=f"Claim not found: {claim_id}")

        return {"claim": serialize_doc(claim), "message": "Claim submitted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
