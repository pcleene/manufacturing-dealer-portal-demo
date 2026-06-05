"""
Cursor-based pagination utilities for Atlas Search.

Manufacturing Group Manufacturing OEMPartner Dealer Portal.
This module provides utilities for efficient cursor-based pagination
using Atlas Search's searchSequenceToken feature.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
import json

from bson import ObjectId

from app.search.query_builder import (
    PRODUCTS_FACETS,
    CLAIMS_FACETS,
    PRODUCTS_FACET_MAPPING,
    CLAIMS_FACET_MAPPING
)

logger = logging.getLogger(__name__)


def format_pipeline_as_python(pipeline: List[Dict[str, Any]], collection_name: str = "collection") -> str:
    """
    Format an aggregation pipeline as readable Python code.
    
    Args:
        pipeline: MongoDB aggregation pipeline
        collection_name: Name of the collection for the code snippet
    
    Returns:
        Python code string representing the pipeline
    """
    def format_value(val: Any, indent: int = 0) -> str:
        """Recursively format a value with proper indentation."""
        spaces = "    " * indent
        
        if val is None:
            return "None"
        elif isinstance(val, bool):
            return str(val)
        elif isinstance(val, str):
            # Handle special MongoDB operators
            if val.startswith("$"):
                return f'"{val}"'
            return f'"{val}"'
        elif isinstance(val, (int, float)):
            return str(val)
        elif isinstance(val, dict):
            if not val:
                return "{}"
            items = []
            for k, v in val.items():
                formatted_v = format_value(v, indent + 1)
                items.append(f'"{k}": {formatted_v}')
            inner = ",\n".join(f"{spaces}    {item}" for item in items)
            return f"{{\n{inner}\n{spaces}}}"
        elif isinstance(val, list):
            if not val:
                return "[]"
            if all(isinstance(x, (str, int, float)) for x in val):
                # Simple list on one line
                formatted = ", ".join(format_value(x, 0) for x in val)
                return f"[{formatted}]"
            items = [format_value(x, indent + 1) for x in val]
            inner = ",\n".join(f"{spaces}    {item}" for item in items)
            return f"[\n{inner}\n{spaces}]"
        else:
            return repr(val)
    
    # Format the pipeline
    formatted_stages = []
    for stage in pipeline:
        formatted_stages.append(format_value(stage, 1))
    
    stages_str = ",\n".join(f"    {stage}" for stage in formatted_stages)
    
    return f"""# MongoDB Aggregation Pipeline
# Collection: {collection_name}

pipeline = [
{stages_str}
]

# Execute with:
# results = db.{collection_name}.aggregate(pipeline)"""


def serialize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively convert MongoDB document to JSON-serializable format.
    Converts ObjectId to string and datetime to ISO format string.
    """
    if doc is None:
        return None
    
    result = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = serialize_document(value)
        elif isinstance(value, list):
            result[key] = [
                serialize_document(item) if isinstance(item, dict)
                else str(item) if isinstance(item, ObjectId)
                else item.isoformat() if isinstance(item, datetime)
                else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def build_search_command(
    index_name: str,
    compound_operator: Dict[str, Any],
    facets: Optional[Dict[str, Any]] = None,
    cursor: Optional[str] = None,
    direction: str = "next",
    limit: int = 20,
    sort: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    Build Atlas Search command with pagination support.

    Args:
        index_name: Name of the Atlas Search index
        compound_operator: Compound operator for filtering/searching
        facets: Facet definitions (optional)
        cursor: Pagination cursor (searchSequenceToken from previous results)
        direction: "next" or "prev"
        limit: Number of results to return
        sort: Sort specification (must include _id for deterministic ordering)

    Returns:
        Complete $search command
    """
    # Default sort: by updatedAt descending, then _id for deterministic ordering
    if sort is None:
        sort = {"updatedAt": -1, "_id": 1}

    # Build base search command
    search_cmd: Dict[str, Any] = {
        "index": index_name,
        "sort": sort,
        "count": {"type": "total"}
    }

    # Add compound operator or facet
    if facets:
        # Use facet operator for faceted search
        # When compound_operator is empty, use a match-all exists query
        if compound_operator:
            search_cmd["facet"] = {
                "operator": {
                    "compound": compound_operator
                },
                "facets": facets
            }
        else:
            # Match all documents when no search criteria
            search_cmd["facet"] = {
                "operator": {
                    "exists": {
                        "path": "_id"  # Every document has an _id
                    }
                },
                "facets": facets
            }
    else:
        # Use compound operator directly (no faceting)
        if compound_operator:
            search_cmd["compound"] = compound_operator
        else:
            # Match all documents when no search criteria
            search_cmd["exists"] = {
                "path": "_id"
            }

    # Add pagination cursor (CRITICAL: at top level, not inside compound!)
    if cursor:
        if direction == "next":
            search_cmd["searchAfter"] = cursor
        elif direction == "prev":
            search_cmd["searchBefore"] = cursor
        else:
            raise ValueError(f"Invalid direction: {direction}. Must be 'next' or 'prev'")

    return search_cmd


def build_aggregation_pipeline(
    search_cmd: Dict[str, Any],
    limit: int,
    projection: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Build aggregation pipeline for Atlas Search with pagination.

    Args:
        search_cmd: Complete $search command
        limit: Number of results to fetch
        projection: Optional field projection

    Returns:
        Aggregation pipeline
    """
    pipeline = [
        # Stage 1: $search
        {"$search": search_cmd},

        # Stage 2: Add search metadata BEFORE $limit
        # CRITICAL: This must come before $limit to get pagination tokens
        {
            "$addFields": {
                "searchScore": {"$meta": "searchScore"},
                "paginationToken": {"$meta": "searchSequenceToken"}
            }
        },

        # Stage 3: Fetch limit + 1 to determine if more results exist
        {"$limit": limit + 1},

        # Stage 4: Use $facet to separate results from metadata
        {
            "$facet": {
                "results": [
                    {"$project": projection} if projection else {"$project": {}}
                ],
                "metadata": [
                    {"$replaceWith": "$$SEARCH_META"},
                    {"$limit": 1}
                ]
            }
        }
    ]

    return pipeline


async def execute_paginated_search(
    collection,
    search_cmd: Dict[str, Any],
    limit: int,
    projection: Optional[Dict[str, Any]] = None,
    direction: str = "next",
    facet_mapping: Optional[Dict[str, Dict[str, str]]] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], Optional[List[Dict[str, Any]]]]:
    """
    Execute a paginated Atlas Search query.

    Args:
        collection: MongoDB collection
        search_cmd: Complete $search command
        limit: Number of results per page
        projection: Optional field projection
        direction: "next" or "prev"
        facet_mapping: Mapping for parsing facet results

    Returns:
        Tuple of (results, pagination_info, facets)
        - results: List of documents
        - pagination_info: Dict with pagination metadata
        - facets: Optional list of facets (if faceted search)
    """
    # Build pipeline
    pipeline = build_aggregation_pipeline(search_cmd, limit, projection)

    # Execute aggregation (in async pymongo, aggregate() returns a coroutine)
    cursor = await collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)

    if not result:
        # No results - return format matching frontend SearchResponse.pagination
        return [], {
            "limit": limit,
            "hasMore": False,
            "nextCursor": None,
            "prevCursor": None,
            "totalCount": 0,
            "currentPageSize": 0
        }, None

    # Extract results and metadata
    results_list = result[0].get("results", [])
    metadata_list = result[0].get("metadata", [])
    metadata = metadata_list[0] if metadata_list else {}

    # Serialize documents to JSON-compatible format (convert ObjectId, datetime)
    results_list = [serialize_document(doc) for doc in results_list]

    # Parse facets if present and mapping provided
    facets = None
    facet_data = metadata.get("facet", {})
    if facet_data and facet_mapping:
        facets = parse_facets(facet_data, facet_mapping)

    # Determine pagination state
    has_more = len(results_list) > limit

    # Remove the extra document if we fetched limit + 1
    if has_more:
        results_list = results_list[:limit]

    # Extract cursors from first and last documents
    first_cursor = results_list[0].get("paginationToken") if results_list else None
    last_cursor = results_list[-1].get("paginationToken") if results_list else None

    # Determine next and previous cursors based on direction
    if direction == "next":
        next_cursor = last_cursor if has_more else None
        prev_cursor = first_cursor  # Can navigate back
    else:  # direction == "prev"
        next_cursor = last_cursor  # Can navigate forward
        prev_cursor = first_cursor if results_list else None

    # Get total count (lower bound estimate from Atlas Search)
    total_count = metadata.get("count", {}).get("lowerBound")

    # Fallback: If count not available, estimate from facet bucket totals
    if total_count is None and facet_data:
        for facet_name, facet_info in facet_data.items():
            buckets = facet_info.get("buckets", [])
            if buckets:
                total_count = sum(bucket.get("count", 0) for bucket in buckets)
                break

    pagination_info = {
        "limit": limit,
        "hasMore": has_more,
        "nextCursor": next_cursor,
        "prevCursor": prev_cursor,
        "totalCount": total_count,
        "currentPageSize": len(results_list)
    }

    return results_list, pagination_info, facets


def parse_facets(
    facet_data: Dict[str, Any],
    facet_mapping: Dict[str, Dict[str, str]]
) -> List[Dict[str, Any]]:
    """
    Parse facet results into UI-friendly format.

    Args:
        facet_data: Raw facet data from $$SEARCH_META
        facet_mapping: Mapping of facet keys to labels

    Returns:
        List of facets with buckets:
        [
            {
                "field": "Category",
                "fieldKey": "category",
                "buckets": [
                    {"value": "Parts", "count": 60},
                    {"value": "Accessories", "count": 15},
                    ...
                ]
            },
            ...
        ]
    """
    facets = []

    for facet_key, config in facet_mapping.items():
        if facet_key in facet_data and "buckets" in facet_data[facet_key]:
            buckets = [
                {"value": bucket["_id"], "count": bucket["count"]}
                for bucket in facet_data[facet_key]["buckets"]
            ]

            facets.append({
                "field": config["label"],
                "fieldKey": config["key"],
                "buckets": buckets
            })

    return facets


def get_products_projection() -> Dict[str, Any]:
    """
    Get projection for product search results.

    Returns:
        Projection dict for $project stage
    """
    return {
        "_id": 1,
        "partNumber": 1,
        "sku": 1,
        "name": 1,
        "description": 1,
        "category": 1,
        "subcategory": 1,
        "productType": 1,
        "compatibleModels": 1,
        "pricing": 1,
        "inventory": 1,
        "specifications": 1,
        "supersession": 1,
        "relatedProducts": 1,
        "images": 1,
        "status": 1,
        "createdAt": 1,
        "updatedAt": 1,
        "searchScore": 1,
        "paginationToken": 1
    }


def get_claims_projection() -> Dict[str, Any]:
    """
    Get projection for warranty claims search results.

    Returns:
        Projection dict for $project stage
    """
    return {
        "_id": 1,
        "claimId": 1,
        "status": 1,
        "statusHistory": 1,
        "dealer": 1,
        "vehicle": 1,
        "customer": 1,
        "failure": 1,
        "partsClaimed": 1,
        "labourClaimed": 1,
        "totals": 1,
        "supportingDocuments": 1,
        "review": 1,
        "payment": 1,
        "createdAt": 1,
        "submittedAt": 1,
        "updatedAt": 1,
        "sla": 1,
        "searchScore": 1,
        "paginationToken": 1
    }


async def search_with_pagination(
    collection,
    index_name: str,
    compound_operator: Dict[str, Any],
    facets_definition: Optional[Dict[str, Any]] = None,
    facet_mapping: Optional[Dict[str, Dict[str, str]]] = None,
    limit: int = 20,
    cursor: Optional[str] = None,
    direction: str = "next",
    projection: Optional[Dict[str, Any]] = None,
    sort: Optional[Dict[str, int]] = None,
    include_query: bool = False
) -> Dict[str, Any]:
    """
    High-level function to execute paginated search with faceting.

    Args:
        collection: MongoDB collection
        index_name: Atlas Search index name
        compound_operator: Compound operator for search/filtering
        facets_definition: Facet definitions (None to disable faceting)
        facet_mapping: Mapping for parsing facet results
        limit: Number of results per page
        cursor: Pagination cursor
        direction: "next" or "prev"
        projection: Field projection
        sort: Sort specification
        include_query: Include the MongoDB query in response (for debugging/demos)

    Returns:
        Dict with results, pagination, and optional facets
    """
    # Build search command
    search_cmd = build_search_command(
        index_name=index_name,
        compound_operator=compound_operator,
        facets=facets_definition,
        cursor=cursor,
        direction=direction,
        limit=limit,
        sort=sort
    )

    # Execute search with facet mapping
    results, pagination_info, facets = await execute_paginated_search(
        collection=collection,
        search_cmd=search_cmd,
        limit=limit,
        projection=projection,
        direction=direction,
        facet_mapping=facet_mapping
    )

    response = {
        "results": results,
        "pagination": pagination_info,
        "facets": facets
    }
    
    # Include query if requested (useful for demos)
    if include_query:
        # Build the full pipeline for display
        pipeline = build_aggregation_pipeline(search_cmd, limit, projection)
        collection_name = collection.name if hasattr(collection, 'name') else 'collection'
        response["debugQuery"] = format_pipeline_as_python(pipeline, collection_name)

    return response
