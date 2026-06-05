"""
Atlas Search query builder for Products and Warranty Claims.

Manufacturing Group Manufacturing OEMPartner Dealer Portal.
This module provides utilities to build compound Atlas Search queries
with proper filtering, faceting, and scoring.
"""
from typing import Optional, Dict, Any, List


# ============================================
# REUSABLE QUERY BUILDING FUNCTIONS
# ============================================

def build_text_search_clause(
    search_text: str,
    paths: List[str],
    fuzzy: bool = False
) -> Dict[str, Any]:
    """
    Build a text search clause for compound operator.

    Args:
        search_text: Text to search for
        paths: Field paths to search in
        fuzzy: Enable fuzzy matching

    Returns:
        Text search clause
    """
    clause = {
        "text": {
            "query": search_text,
            "path": paths
        }
    }

    if fuzzy:
        clause["text"]["fuzzy"] = {
            "maxEdits": 1,
            "prefixLength": 2
        }

    return clause


def build_autocomplete_clause(
    search_text: str,
    path: str,
    fuzzy: bool = True
) -> Dict[str, Any]:
    """
    Build an autocomplete search clause.

    Args:
        search_text: Text to autocomplete
        path: Field path with autocomplete index
        fuzzy: Enable fuzzy matching

    Returns:
        Autocomplete search clause
    """
    clause = {
        "autocomplete": {
            "query": search_text,
            "path": path
        }
    }

    if fuzzy:
        clause["autocomplete"]["fuzzy"] = {
            "maxEdits": 1,
            "prefixLength": 2
        }

    return clause


def build_filter_clause(
    path: str,
    values: List[Any],
    operator: str = "in"
) -> Dict[str, Any]:
    """
    Build a filter clause for multi-select filters.

    Args:
        path: Field path to filter on
        values: List of values to match
        operator: Filter operator ("in", "equals", etc.)

    Returns:
        Filter clause
    """
    if operator == "in":
        return {
            "in": {
                "path": path,
                "value": values
            }
        }
    elif operator == "equals":
        return {
            "equals": {
                "path": path,
                "value": values[0] if values else None
            }
        }
    else:
        raise ValueError(f"Unsupported operator: {operator}")


def build_range_clause(
    path: str,
    min_value: Optional[Any] = None,
    max_value: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Build a range filter clause for numbers or dates.

    Args:
        path: Field path to filter on
        min_value: Minimum value (inclusive)
        max_value: Maximum value (inclusive)

    Returns:
        Range filter clause
    """
    range_clause = {
        "range": {
            "path": path
        }
    }

    if min_value is not None:
        range_clause["range"]["gte"] = min_value

    if max_value is not None:
        range_clause["range"]["lte"] = max_value

    return range_clause


# ============================================
# PRODUCTS SEARCH CONFIGURATION
# ============================================

# Filter mappings for products (filter_key -> MongoDB path)
PRODUCT_FILTER_MAPPING = {
    "category": "category",
    "subcategory": "subcategory",
    "availability_status": "inventory.status",
    "model_series": "compatibleModels.modelCode",
    "warehouse_region": "inventory.warehouses.code",
}

# Facet definitions for Products
PRODUCTS_FACETS = {
    "categoryFacet": {
        "type": "string",
        "path": "category",
        "numBuckets": 15
    },
    "subcategoryFacet": {
        "type": "string",
        "path": "subcategory",
        "numBuckets": 25
    },
    "statusFacet": {
        "type": "string",
        "path": "inventory.status",
        "numBuckets": 5
    },
    "modelSeriesFacet": {
        "type": "string",
        "path": "compatibleModels.modelCode",
        "numBuckets": 15
    },
    "priceRangeFacet": {
        "type": "number",
        "path": "pricing.msrp",
        "boundaries": [0, 50, 100, 200, 500, 1000, 5000],
        "default": "other"
    }
}

# Facet field mapping for parsing results
PRODUCTS_FACET_MAPPING = {
    "categoryFacet": {
        "label": "Category",
        "key": "category"
    },
    "subcategoryFacet": {
        "label": "Subcategory",
        "key": "subcategory"
    },
    "statusFacet": {
        "label": "Availability",
        "key": "inventory.status"
    },
    "modelSeriesFacet": {
        "label": "Model Series",
        "key": "compatibleModels.modelCode"
    },
    "priceRangeFacet": {
        "label": "Price Range (MYR)",
        "key": "pricing.msrp"
    }
}


def build_products_autocomplete_operator(search_text: str) -> Dict[str, Any]:
    """
    Build a lightweight compound operator for autocomplete suggestions.
    
    This uses only autocomplete and text search - no filters, optimized for speed.

    Args:
        search_text: Text to autocomplete

    Returns:
        Compound operator for Atlas Search autocomplete
    """
    return {
        "should": [
            # Primary: autocomplete on product name (prefix matching)
            {
                "autocomplete": {
                    "query": search_text,
                    "path": "name",
                    "fuzzy": {
                        "maxEdits": 1,
                        "prefixLength": 2
                    }
                }
            },
            # Match on part number (exact prefix)
            {
                "text": {
                    "query": search_text,
                    "path": "partNumber"
                }
            },
            # Match on SKU
            {
                "text": {
                    "query": search_text,
                    "path": "sku"
                }
            }
        ],
        "minimumShouldMatch": 1
    }


def build_products_compound_operator(
    search_text: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build compound operator for product search.

    Args:
        search_text: Optional text to search for
        filters: Optional filters dict with keys:
            - category: List[str]
            - subcategory: List[str]
            - model_series: List[str]
            - model_year: List[int]
            - availability_status: List[str]
            - min_price: float
            - max_price: float
            - warehouse_region: List[str]

    Returns:
        Compound operator for Atlas Search
    """
    compound = {
        "must": [],
        "should": [],
        "filter": []
    }

    # Add text search if provided
    if search_text:
        # Use autocomplete for partial matching (prefix search)
        compound["should"].append({
            "autocomplete": {
                "query": search_text,
                "path": "name",
                "fuzzy": {
                    "maxEdits": 1,
                    "prefixLength": 2
                }
            }
        })

        # Also search on IDs using text search
        compound["should"].append(
            build_text_search_clause(
                search_text,
                ["partNumber", "sku"],
                fuzzy=False
            )
        )

        # Standard text search on name, description as fallback
        compound["should"].append(
            build_text_search_clause(
                search_text,
                ["name", "description", "searchText"],
                fuzzy=True
            )
        )

        # Require at least one should clause to match
        compound["minimumShouldMatch"] = 1

    # Apply list-based filters using loop
    if filters:
        for filter_key, mongo_path in PRODUCT_FILTER_MAPPING.items():
            if filters.get(filter_key):
                compound["filter"].append(
                    build_filter_clause(mongo_path, filters[filter_key])
                )

        # Handle model year filter (special case - check yearStart and yearEnd)
        if filters.get("model_year"):
            years = filters["model_year"]
            year_conditions = []
            for year in years:
                year_conditions.append({
                    "compound": {
                        "must": [
                            {"range": {"path": "compatibleModels.yearStart", "lte": year}},
                            {"range": {"path": "compatibleModels.yearEnd", "gte": year}}
                        ]
                    }
                })
            if year_conditions:
                compound["filter"].append({
                    "compound": {
                        "should": year_conditions,
                        "minimumShouldMatch": 1
                    }
                })

        # Handle range filter for price
        if filters.get("min_price") is not None or filters.get("max_price") is not None:
            compound["filter"].append(
                build_range_clause(
                    "pricing.msrp",
                    filters.get("min_price"),
                    filters.get("max_price")
                )
            )

    # Remove empty arrays (but keep minimumShouldMatch)
    compound = {k: v for k, v in compound.items() if v or k == "minimumShouldMatch"}

    # If compound is empty, return empty (caller will use match-all)
    if not compound or (len(compound) == 1 and "minimumShouldMatch" in compound):
        return {}

    return compound


# ============================================
# WARRANTY CLAIMS SEARCH CONFIGURATION
# ============================================

# Filter mappings for claims (filter_key -> MongoDB path)
CLAIM_FILTER_MAPPING = {
    "status": "status",
    "vehicle_model": "vehicle.modelCode",
    "failure_category": "failure.category",
    "dealer_region": "dealer.region",
}

# Facet definitions for Warranty Claims
CLAIMS_FACETS = {
    "statusFacet": {
        "type": "string",
        "path": "status",
        "numBuckets": 10
    },
    "vehicleModelFacet": {
        "type": "string",
        "path": "vehicle.modelCode",
        "numBuckets": 15
    },
    "failureCategoryFacet": {
        "type": "string",
        "path": "failure.category",
        "numBuckets": 15
    },
    "dealerRegionFacet": {
        "type": "string",
        "path": "dealer.region",
        "numBuckets": 20
    },
    "claimAmountFacet": {
        "type": "number",
        "path": "totals.claimTotal",
        "boundaries": [0, 100, 250, 500, 1000, 2000, 5000],
        "default": "other"
    }
}

# Facet field mapping for parsing results
CLAIMS_FACET_MAPPING = {
    "statusFacet": {
        "label": "Status",
        "key": "status"
    },
    "vehicleModelFacet": {
        "label": "Vehicle Model",
        "key": "vehicle.modelCode"
    },
    "failureCategoryFacet": {
        "label": "Failure Category",
        "key": "failure.category"
    },
    "dealerRegionFacet": {
        "label": "Region",
        "key": "dealer.region"
    },
    "claimAmountFacet": {
        "label": "Claim Amount (MYR)",
        "key": "totals.claimTotal"
    }
}


def build_claims_autocomplete_operator(search_text: str) -> Dict[str, Any]:
    """
    Build a lightweight compound operator for autocomplete suggestions.
    
    This uses only autocomplete and text search - no filters, optimized for speed.

    Args:
        search_text: Text to autocomplete

    Returns:
        Compound operator for Atlas Search autocomplete
    """
    return {
        "should": [
            # Primary: autocomplete on claim ID (prefix matching)
            {
                "autocomplete": {
                    "query": search_text,
                    "path": "claimId",
                    "fuzzy": {
                        "maxEdits": 1,
                        "prefixLength": 2
                    }
                }
            },
            # Match on customer name
            {
                "autocomplete": {
                    "query": search_text,
                    "path": "customer.name",
                    "fuzzy": {
                        "maxEdits": 1,
                        "prefixLength": 2
                    }
                }
            },
            # Match on vehicle registration
            {
                "autocomplete": {
                    "query": search_text,
                    "path": "vehicle.registrationNumber",
                    "fuzzy": {
                        "maxEdits": 1,
                        "prefixLength": 2
                    }
                }
            }
        ],
        "minimumShouldMatch": 1
    }


def build_claims_compound_operator(
    search_text: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build compound operator for warranty claims search.

    Args:
        search_text: Optional text to search for
        filters: Optional filters dict with keys:
            - status: List[str]
            - date_from: str (ISO date)
            - date_to: str (ISO date)
            - vehicle_model: List[str]
            - failure_category: List[str]
            - min_amount: float
            - max_amount: float
            - dealer_id: str
            - dealer_region: List[str]

    Returns:
        Compound operator for Atlas Search
    """
    compound = {
        "must": [],
        "should": [],
        "filter": []
    }

    # Add text search if provided
    if search_text:
        # Use autocomplete for partial matching on claim ID
        compound["should"].append({
            "autocomplete": {
                "query": search_text,
                "path": "claimId",
                "fuzzy": {
                    "maxEdits": 1,
                    "prefixLength": 2
                }
            }
        })

        # Autocomplete on customer name
        compound["should"].append({
            "autocomplete": {
                "query": search_text,
                "path": "customer.name",
                "fuzzy": {
                    "maxEdits": 1,
                    "prefixLength": 2
                }
            }
        })

        # Text search on vehicle registration and other IDs
        compound["should"].append(
            build_text_search_clause(
                search_text,
                ["vehicle.registrationNumber", "vehicle.engineNumber", "vehicle.frameNumber"],
                fuzzy=False
            )
        )

        # Standard text search on description fields as fallback
        compound["should"].append(
            build_text_search_clause(
                search_text,
                ["searchText", "failure.description", "dealer.name"],
                fuzzy=True
            )
        )

        # Require at least one should clause to match
        compound["minimumShouldMatch"] = 1

    # Apply list-based filters using loop
    if filters:
        for filter_key, mongo_path in CLAIM_FILTER_MAPPING.items():
            filter_value = filters.get(filter_key)
            if filter_value:
                if isinstance(filter_value, list):
                    compound["filter"].append(
                        build_filter_clause(mongo_path, filter_value)
                    )
                else:
                    # Single value filter (e.g., dealer_id)
                    compound["filter"].append({
                        "equals": {
                            "path": mongo_path,
                            "value": filter_value
                        }
                    })

        # Handle dealer_id separately (single value, not in mapping)
        if filters.get("dealer_id"):
            compound["filter"].append({
                "equals": {
                    "path": "dealer.dealerId",
                    "value": filters["dealer_id"]
                }
            })

        # Handle date range filter
        if filters.get("date_from") or filters.get("date_to"):
            from datetime import datetime
            date_filter = {"range": {"path": "submittedAt"}}
            if filters.get("date_from"):
                date_filter["range"]["gte"] = datetime.fromisoformat(filters["date_from"])
            if filters.get("date_to"):
                date_filter["range"]["lte"] = datetime.fromisoformat(filters["date_to"])
            compound["filter"].append(date_filter)

        # Handle range filter for claim amount
        if filters.get("min_amount") is not None or filters.get("max_amount") is not None:
            compound["filter"].append(
                build_range_clause(
                    "totals.claimTotal",
                    filters.get("min_amount"),
                    filters.get("max_amount")
                )
            )

        # Handle SLA breached filter (boolean)
        if filters.get("sla_breached") is not None:
            compound["filter"].append({
                "equals": {
                    "path": "sla.slaBreached",
                    "value": filters["sla_breached"]
                }
            })

    # Remove empty arrays (but keep minimumShouldMatch)
    compound = {k: v for k, v in compound.items() if v or k == "minimumShouldMatch"}

    # If compound is empty, return empty (caller will use match-all)
    if not compound or (len(compound) == 1 and "minimumShouldMatch" in compound):
        return {}

    return compound


# ============================================
# AUTOCOMPLETE SEARCH (Lightweight)
# ============================================

def build_product_autocomplete_query(
    query: str,
    field: str = "name"
) -> Dict[str, Any]:
    """
    Build autocomplete query for products.

    Args:
        query: Search text
        field: Field to autocomplete on (name or partNumber)

    Returns:
        Autocomplete search command
    """
    path = "name" if field == "name" else "partNumber"

    return {
        "autocomplete": {
            "query": query,
            "path": path,
            "fuzzy": {
                "maxEdits": 1,
                "prefixLength": 2
            }
        }
    }


def build_claim_autocomplete_query(
    query: str,
    field: str = "claimId"
) -> Dict[str, Any]:
    """
    Build autocomplete query for claims.

    Args:
        query: Search text
        field: Field to autocomplete on (claimId, customerName, registration)

    Returns:
        Autocomplete search command
    """
    path_map = {
        "claimId": "claimId",
        "customerName": "customer.name",
        "registration": "vehicle.registrationNumber"
    }
    path = path_map.get(field, "claimId")

    return {
        "autocomplete": {
            "query": query,
            "path": path,
            "fuzzy": {
                "maxEdits": 1,
                "prefixLength": 2
            }
        }
    }
