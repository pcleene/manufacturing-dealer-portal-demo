"""
Product service layer - Business logic for product catalog operations.

Manufacturing Group Manufacturing OEMPartner Dealer Portal.
"""
from typing import Optional, Dict, List, Any
import logging

from app.config import settings
from app.search.query_builder import (
    build_products_compound_operator,
    build_product_autocomplete_query,
    PRODUCTS_FACETS,
    PRODUCTS_FACET_MAPPING
)
from app.search.pagination import (
    search_with_pagination,
    get_products_projection
)
from app.search.vector_search import vector_search_products

logger = logging.getLogger(__name__)


class ProductService:
    """Service for product-related operations."""

    def __init__(self, db):
        self.db = db
        self.products = db.products

    async def search_products(
        self,
        search_text: Optional[str],
        filters: Dict[str, Any],
        limit: int,
        cursor: Optional[str],
        direction: str,
        use_facets: bool,
        include_query: bool = False
    ) -> Dict[str, Any]:
        """
        Search products using Atlas Search with faceting and pagination.

        Args:
            search_text: Optional text to search for (product name, part number, description)
            filters: Dict of filters (category, subcategory, model_series, etc.)
            limit: Number of results per page
            cursor: Pagination cursor
            direction: "next" or "prev"
            use_facets: Whether to include facets in response
            include_query: Include the MongoDB query in response (for debugging/demos)

        Returns:
            Dict with results, pagination, and optional facets
        """
        # Build compound operator
        compound_operator = build_products_compound_operator(
            search_text=search_text,
            filters=filters
        )

        # Determine facets
        facets_definition = PRODUCTS_FACETS if use_facets else None

        # Execute search with pagination
        result = await search_with_pagination(
            collection=self.products,
            index_name=settings.products_search_index,
            compound_operator=compound_operator,
            facets_definition=facets_definition,
            facet_mapping=PRODUCTS_FACET_MAPPING if use_facets else None,
            limit=limit,
            cursor=cursor,
            direction=direction,
            projection=get_products_projection(),
            include_query=include_query
        )

        return result

    async def vector_search_products(
        self,
        query: str,
        filters: Dict[str, Any],
        limit: int,
        num_candidates: int,
        include_query: bool = False
    ) -> Dict[str, Any]:
        """
        Perform semantic search using vector embeddings.

        Supports natural language queries like:
        - "motorcycle good for city commuting with good fuel economy"
        - "brake pads compatible with Y15ZR"
        - "accessories for long distance touring"

        Args:
            query: Natural language query
            filters: Optional metadata filters
            limit: Number of results
            num_candidates: Number of candidates for vector search
            include_query: Include the MongoDB query in response (for debugging/demos)

        Returns:
            Dict with results and pagination
        """
        result = await vector_search_products(
            collection=self.products,
            query=query,
            filters=filters,
            limit=limit,
            num_candidates=num_candidates,
            include_query=include_query
        )

        return result

    async def get_product_by_part_number(self, part_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single product by part number.

        Args:
            part_number: OEMPartner part number (e.g., "2PV-F5710-00")

        Returns:
            Product document or None if not found
        """
        product = await self.products.find_one({"partNumber": part_number})
        return product

    async def get_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single product by SKU.

        Args:
            sku: Product SKU

        Returns:
            Product document or None if not found
        """
        product = await self.products.find_one({"sku": sku})
        return product

    async def get_related_products(
        self,
        part_number: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get related products (cross-sell, upsell, companions).

        Args:
            part_number: Source product part number
            limit: Maximum number of related products to return

        Returns:
            List of related product documents
        """
        # Get the source product
        product = await self.products.find_one(
            {"partNumber": part_number},
            {"relatedProducts": 1}
        )

        if not product or not product.get("relatedProducts"):
            return []

        # Get part numbers of related products
        related_part_numbers = [
            rp.get("partNumber")
            for rp in product.get("relatedProducts", [])
            if rp.get("partNumber")
        ][:limit]

        if not related_part_numbers:
            return []

        # Fetch related products
        cursor = self.products.find(
            {"partNumber": {"$in": related_part_numbers}},
            {
                "_id": 1,
                "partNumber": 1,
                "name": 1,
                "category": 1,
                "pricing": 1,
                "inventory": 1,
                "images": 1
            }
        )

        related = await cursor.to_list(length=limit)

        # Add relationship type from source product
        relationship_map = {
            rp.get("partNumber"): rp.get("type")
            for rp in product.get("relatedProducts", [])
        }

        for item in related:
            item["relationshipType"] = relationship_map.get(item.get("partNumber"))

        return related

    async def get_products_by_model(
        self,
        model_code: str,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get products compatible with a specific vehicle model.

        Args:
            model_code: Vehicle model code (e.g., "Y15ZR", "LC135")
            category: Optional category filter
            limit: Number of products to return
            offset: Number of products to skip

        Returns:
            List of compatible product documents
        """
        query = {"compatibleModels.modelCode": model_code}

        if category:
            query["category"] = category

        cursor = self.products.find(
            query,
            {
                "_id": 1,
                "partNumber": 1,
                "name": 1,
                "category": 1,
                "subcategory": 1,
                "pricing": 1,
                "inventory": 1,
                "images": 1,
                "compatibleModels": 1
            }
        ).skip(offset).limit(limit)

        products = await cursor.to_list(length=limit)
        return products

    async def autocomplete_products(
        self,
        query: str,
        field: str = "name",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get autocomplete suggestions for products.

        Args:
            query: Partial search text
            field: Field to autocomplete on ("name" or "partNumber")
            limit: Maximum number of suggestions

        Returns:
            List of autocomplete suggestions
        """
        # Build autocomplete pipeline
        autocomplete_query = build_product_autocomplete_query(query, field)

        pipeline = [
            {"$search": {
                "index": settings.products_search_index,
                **autocomplete_query
            }},
            {"$limit": limit},
            {"$project": {
                "_id": 0,
                "partNumber": 1,
                "name": 1,
                "category": 1,
                "text": f"${field}" if field == "name" else "$partNumber"
            }}
        ]

        cursor = await self.products.aggregate(pipeline)
        suggestions = await cursor.to_list(length=limit)

        return suggestions

    async def get_low_stock_products(
        self,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get products with low stock levels.

        Args:
            limit: Maximum number of products to return

        Returns:
            List of low-stock product documents
        """
        cursor = self.products.find(
            {"inventory.status": "Low Stock"},
            {
                "_id": 1,
                "partNumber": 1,
                "name": 1,
                "category": 1,
                "inventory": 1,
                "pricing": 1
            }
        ).sort("inventory.totalAvailable", 1).limit(limit)

        products = await cursor.to_list(length=limit)
        return products

    async def get_product_categories(self) -> List[Dict[str, Any]]:
        """
        Get all product categories with counts.

        Returns:
            List of category documents with counts
        """
        pipeline = [
            {"$group": {
                "_id": "$category",
                "count": {"$sum": 1},
                "subcategories": {"$addToSet": "$subcategory"}
            }},
            {"$sort": {"count": -1}}
        ]

        cursor = await self.products.aggregate(pipeline)
        categories = await cursor.to_list(length=50)
        return categories

    async def get_supersession_chain(
        self,
        part_number: str
    ) -> Dict[str, Any]:
        """
        Get the supersession chain for a part number.

        Shows which parts this part replaces and what has replaced it.

        Args:
            part_number: Product part number

        Returns:
            Dict with supersession information:
            - current: Current part info
            - replaces: Parts this part supersedes
            - replacedBy: Part that supersedes this one
        """
        product = await self.products.find_one(
            {"partNumber": part_number},
            {"partNumber": 1, "name": 1, "supersession": 1, "status": 1}
        )

        if not product:
            return {"current": None, "replaces": [], "replacedBy": None}

        result = {
            "current": {
                "partNumber": product.get("partNumber"),
                "name": product.get("name"),
                "status": product.get("status")
            },
            "replaces": [],
            "replacedBy": None
        }

        supersession = product.get("supersession", {})

        # Get parts this product replaces
        replaces_part_numbers = supersession.get("replacesPartNumbers", [])
        if replaces_part_numbers:
            cursor = self.products.find(
                {"partNumber": {"$in": replaces_part_numbers}},
                {"partNumber": 1, "name": 1, "status": 1}
            )
            result["replaces"] = await cursor.to_list(length=len(replaces_part_numbers))

        # Get part that replaced this one
        replaced_by = supersession.get("replacedByPartNumber")
        if replaced_by:
            replacement = await self.products.find_one(
                {"partNumber": replaced_by},
                {"partNumber": 1, "name": 1, "status": 1}
            )
            result["replacedBy"] = replacement

        return result
