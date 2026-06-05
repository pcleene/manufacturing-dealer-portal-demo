"""
Product API routes for the OEMPartner Dealer Portal.

Provides endpoints for searching, retrieving, and managing product catalog.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Any

from app.database import get_database
from app.services.product_service import ProductService
from app.config import settings
from app.models.products import ProductResponse, ProductSearchResponse
from app.models.search import VectorSearchRequest
from app.utils import serialize_doc, serialize_docs

router = APIRouter()


def get_product_service(db=Depends(get_database)) -> ProductService:
    """Dependency to get ProductService instance."""
    return ProductService(db)


@router.get("/search", response_model=None)
async def search_products(
    search_text: Optional[str] = Query(None, description="Text to search for"),
    category: Optional[List[str]] = Query(None, description="Filter by category"),
    subcategory: Optional[List[str]] = Query(None, description="Filter by subcategory"),
    model_series: Optional[List[str]] = Query(None, alias="modelSeries", description="Filter by compatible model"),
    model_year: Optional[List[int]] = Query(None, alias="modelYear", description="Filter by model year"),
    availability_status: Optional[List[str]] = Query(None, alias="availabilityStatus", description="Filter by stock status"),
    min_price: Optional[float] = Query(None, alias="minPrice", description="Minimum MSRP"),
    max_price: Optional[float] = Query(None, alias="maxPrice", description="Maximum MSRP"),
    warehouse_region: Optional[List[str]] = Query(None, alias="warehouseRegion", description="Filter by warehouse"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    direction: str = Query("next", regex="^(next|prev)$", description="Pagination direction"),
    use_facets: bool = Query(True, alias="useFacets", description="Include facets in response"),
    include_query: bool = Query(False, alias="includeQuery", description="Include MongoDB query in response (for demos)"),
    service: ProductService = Depends(get_product_service)
) -> dict:
    """
    Search products with full-text search, filters, and faceting.

    Supports fuzzy matching on product names and part numbers.
    """
    filters = {
        "category": category,
        "subcategory": subcategory,
        "model_series": model_series,
        "model_year": model_year,
        "availability_status": availability_status,
        "min_price": min_price,
        "max_price": max_price,
        "warehouse_region": warehouse_region
    }
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}

    result = await service.search_products(
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
async def semantic_search_products(
    request: VectorSearchRequest,
    service: ProductService = Depends(get_product_service)
) -> dict:
    """
    Semantic search for products using natural language.

    Example queries:
    - "motorcycle good for city commuting with good fuel economy"
    - "brake pads compatible with Y15ZR"
    - "accessories for long distance touring"
    """
    result = await service.vector_search_products(
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
async def autocomplete_products(
    q: str = Query(..., min_length=2, description="Search query"),
    field: str = Query("name", regex="^(name|partNumber)$", description="Field to autocomplete"),
    limit: int = Query(10, ge=1, le=20, description="Max suggestions"),
    service: ProductService = Depends(get_product_service)
) -> dict:
    """
    Get autocomplete suggestions for product search.

    Supports autocomplete on product name or part number.
    """
    suggestions = await service.autocomplete_products(
        query=q,
        field=field,
        limit=limit
    )

    return {"suggestions": suggestions, "query": q}


@router.get("/low-stock", response_model=None)
async def get_low_stock_products(
    limit: int = Query(50, ge=1, le=100, description="Max products to return"),
    service: ProductService = Depends(get_product_service)
) -> dict:
    """
    Get products with low stock levels.

    Returns products sorted by available quantity (ascending).
    """
    products = await service.get_low_stock_products(limit=limit)
    return {"products": serialize_docs(products), "count": len(products)}


@router.get("/categories", response_model=None)
async def get_product_categories(
    service: ProductService = Depends(get_product_service)
) -> dict:
    """
    Get all product categories with counts.
    """
    categories = await service.get_product_categories()
    return {"categories": serialize_docs(categories)}


@router.get("/by-model/{model_code}", response_model=None)
async def get_products_by_model(
    model_code: str,
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100, description="Max products"),
    offset: int = Query(0, ge=0, description="Skip count"),
    service: ProductService = Depends(get_product_service)
) -> dict:
    """
    Get products compatible with a specific vehicle model.

    Args:
        model_code: Vehicle model code (e.g., "Y15ZR", "LC135", "NVX")
    """
    products = await service.get_products_by_model(
        model_code=model_code.upper(),
        category=category,
        limit=limit,
        offset=offset
    )

    return {
        "modelCode": model_code.upper(),
        "products": serialize_docs(products),
        "count": len(products),
        "limit": limit,
        "offset": offset
    }


@router.get("/{part_number}", response_model=None)
async def get_product_by_part_number(
    part_number: str,
    service: ProductService = Depends(get_product_service)
) -> dict:
    """
    Get a single product by part number.

    Args:
        part_number: OEMPartner part number (e.g., "2PV-F5710-00")
    """
    product = await service.get_product_by_part_number(part_number)

    if not product:
        raise HTTPException(status_code=404, detail=f"Product not found: {part_number}")

    return {"product": serialize_doc(product)}


@router.get("/{part_number}/related", response_model=None)
async def get_related_products(
    part_number: str,
    limit: int = Query(10, ge=1, le=20, description="Max related products"),
    service: ProductService = Depends(get_product_service)
) -> dict:
    """
    Get related products (cross-sell, upsell, companions).
    """
    related = await service.get_related_products(part_number, limit=limit)

    return {
        "partNumber": part_number,
        "relatedProducts": serialize_docs(related),
        "count": len(related)
    }


@router.get("/{part_number}/supersession", response_model=None)
async def get_supersession_chain(
    part_number: str,
    service: ProductService = Depends(get_product_service)
) -> dict:
    """
    Get the supersession chain for a part number.

    Shows which parts this part replaces and what has replaced it.
    """
    chain = await service.get_supersession_chain(part_number)

    if not chain.get("current"):
        raise HTTPException(status_code=404, detail=f"Product not found: {part_number}")

    # Serialize the chain
    serialized_chain = {
        "current": serialize_doc(chain.get("current")),
        "replaces": serialize_docs(chain.get("replaces", [])),
        "replacedBy": serialize_doc(chain.get("replacedBy"))
    }

    return serialized_chain
