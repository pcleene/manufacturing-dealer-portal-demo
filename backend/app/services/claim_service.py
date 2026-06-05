"""
Claim service layer - Business logic for warranty claim operations.

Manufacturing Group Manufacturing OEMPartner Dealer Portal.
"""
from typing import Optional, Dict, List, Any
import logging
from datetime import datetime, timedelta

from app.config import settings
from app.search.query_builder import (
    build_claims_compound_operator,
    build_claim_autocomplete_query,
    CLAIMS_FACETS,
    CLAIMS_FACET_MAPPING
)
from app.search.pagination import (
    search_with_pagination,
    get_claims_projection
)
from app.search.vector_search import vector_search_claims

logger = logging.getLogger(__name__)


class ClaimService:
    """Service for warranty claim-related operations."""

    def __init__(self, db):
        self.db = db
        self.claims = db.warrantyClaims
        self.dealers = db.dealers

    async def search_claims(
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
        Search warranty claims using Atlas Search with faceting and pagination.

        Args:
            search_text: Optional text to search for (claim ID, customer name, etc.)
            filters: Dict of filters (status, vehicle_model, failure_category, etc.)
            limit: Number of results per page
            cursor: Pagination cursor
            direction: "next" or "prev"
            use_facets: Whether to include facets in response
            include_query: Include the MongoDB query in response (for debugging/demos)

        Returns:
            Dict with results, pagination, and optional facets
        """
        # Build compound operator
        compound_operator = build_claims_compound_operator(
            search_text=search_text,
            filters=filters
        )

        # Determine facets
        facets_definition = CLAIMS_FACETS if use_facets else None

        # Execute search with pagination
        result = await search_with_pagination(
            collection=self.claims,
            index_name=settings.claims_search_index,
            compound_operator=compound_operator,
            facets_definition=facets_definition,
            facet_mapping=CLAIMS_FACET_MAPPING if use_facets else None,
            limit=limit,
            cursor=cursor,
            direction=direction,
            projection=get_claims_projection(),
            include_query=include_query
        )

        return result

    async def vector_search_claims(
        self,
        query: str,
        filters: Dict[str, Any],
        limit: int,
        num_candidates: int,
        include_query: bool = False
    ) -> Dict[str, Any]:
        """
        Perform semantic search for warranty claims.

        Supports natural language queries like:
        - "Y15ZR engine claims last 3 months"
        - "rejected claims for fuel pump issues"
        - "high value claims from Selangor dealers"

        Args:
            query: Natural language query
            filters: Optional metadata filters
            limit: Number of results
            num_candidates: Number of candidates for vector search
            include_query: Include the MongoDB query in response (for debugging/demos)

        Returns:
            Dict with results and pagination
        """
        result = await vector_search_claims(
            collection=self.claims,
            query=query,
            filters=filters,
            limit=limit,
            num_candidates=num_candidates,
            include_query=include_query
        )

        return result

    async def get_claim_by_id(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single claim by claim ID.

        Args:
            claim_id: Warranty claim ID (e.g., "WC-2024-KL-00456")

        Returns:
            Claim document or None if not found
        """
        claim = await self.claims.find_one({"claimId": claim_id})
        return claim

    async def create_claim(
        self,
        dealer_id: str,
        claim_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new warranty claim (draft status).

        Args:
            dealer_id: Dealer ID submitting the claim
            claim_data: Claim data (vehicle, customer, failure, parts, labour)

        Returns:
            Created claim document
        """
        # Get dealer info
        dealer = await self.dealers.find_one({"dealerId": dealer_id})
        if not dealer:
            raise ValueError(f"Dealer not found: {dealer_id}")

        # Generate claim ID
        now = datetime.utcnow()
        region_code = dealer.get("region", "XX")[:2].upper()
        count = await self.claims.count_documents({
            "createdAt": {"$gte": datetime(now.year, 1, 1)}
        })
        claim_id = f"WC-{now.year}-{region_code}-{count + 1:05d}"

        # Calculate totals
        parts_total = sum(
            p.get("totalCost", 0)
            for p in claim_data.get("partsClaimed", [])
        )
        labour = claim_data.get("labourClaimed", {})
        labour_total = labour.get("totalLabourCost", 0) if labour else 0
        core_charge_total = sum(
            p.get("coreCharge", 0) or 0
            for p in claim_data.get("partsClaimed", [])
        )

        # Build claim document
        claim = {
            "claimId": claim_id,
            "status": "Draft",
            "statusHistory": [{
                "status": "Draft",
                "timestamp": now,
                "updatedBy": dealer_id,
                "notes": None
            }],
            "dealer": {
                "dealerId": dealer.get("dealerId"),
                "dealerName": dealer.get("name"),
                "region": dealer.get("region"),
                "contactPerson": dealer.get("personnel", [{}])[0].get("name", ""),
                "contactPhone": dealer.get("contact", {}).get("phone", "")
            },
            "vehicle": claim_data.get("vehicle"),
            "customer": claim_data.get("customer"),
            "failure": claim_data.get("failure"),
            "partsClaimed": claim_data.get("partsClaimed", []),
            "labourClaimed": claim_data.get("labourClaimed"),
            "totals": {
                "partsTotal": parts_total,
                "labourTotal": labour_total,
                "coreChargeTotal": core_charge_total,
                "taxAmount": 0,
                "claimTotal": parts_total + labour_total,
                "approvedAmount": None,
                "currency": "MYR"
            },
            "documents": [],
            "review": {
                "assignedTo": None,
                "assignedAt": None,
                "reviewNotes": [],
                "decision": None,
                "decisionDate": None,
                "rejectionReason": None
            },
            "payment": {
                "paymentStatus": None,
                "paymentMethod": None,
                "paymentReference": None,
                "paymentDate": None,
                "bankAccount": None
            },
            "searchText": self._build_search_text(claim_data, claim_id, dealer),
            "createdAt": now,
            "submittedAt": None,
            "updatedAt": now,
            "sla": {
                "targetResponseDays": 3,
                "targetResolutionDays": 7,
                "responseDeadline": None,
                "resolutionDeadline": None,
                "isOverdue": False
            }
        }

        result = await self.claims.insert_one(claim)
        claim["_id"] = result.inserted_id

        return claim

    def _build_search_text(
        self,
        claim_data: Dict[str, Any],
        claim_id: str,
        dealer: Dict[str, Any]
    ) -> str:
        """Build search text for full-text search optimization."""
        parts = [claim_id]

        vehicle = claim_data.get("vehicle", {})
        parts.extend([
            vehicle.get("modelCode", ""),
            vehicle.get("modelName", ""),
            vehicle.get("registrationNumber", "")
        ])

        customer = claim_data.get("customer", {})
        parts.append(customer.get("name", ""))

        failure = claim_data.get("failure", {})
        parts.extend([
            failure.get("category", ""),
            failure.get("subcategory", ""),
            failure.get("description", "")[:200] if failure.get("description") else ""
        ])

        parts.extend([
            dealer.get("name", ""),
            dealer.get("region", "")
        ])

        return " ".join(filter(None, parts))

    async def update_claim(
        self,
        claim_id: str,
        update_data: Dict[str, Any],
        updated_by: str
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing claim (only if in Draft status).

        Args:
            claim_id: Claim ID to update
            update_data: Fields to update
            updated_by: User ID making the update

        Returns:
            Updated claim document or None if not found/not updatable
        """
        # Check claim exists and is in Draft status
        existing = await self.claims.find_one({"claimId": claim_id})
        if not existing:
            return None
        if existing.get("status") != "Draft":
            raise ValueError(f"Cannot update claim in status: {existing.get('status')}")

        # Build update
        now = datetime.utcnow()
        update = {"$set": {"updatedAt": now}}

        # Update allowed fields
        allowed_fields = ["failure", "partsClaimed", "labourClaimed", "documents"]
        for field in allowed_fields:
            if field in update_data:
                update["$set"][field] = update_data[field]

        # Recalculate totals if parts or labour changed
        if "partsClaimed" in update_data or "labourClaimed" in update_data:
            parts = update_data.get("partsClaimed", existing.get("partsClaimed", []))
            labour = update_data.get("labourClaimed", existing.get("labourClaimed"))

            parts_total = sum(p.get("totalCost", 0) for p in parts)
            labour_total = labour.get("totalLabourCost", 0) if labour else 0
            core_charge_total = sum(p.get("coreCharge", 0) or 0 for p in parts)

            update["$set"]["totals.partsTotal"] = parts_total
            update["$set"]["totals.labourTotal"] = labour_total
            update["$set"]["totals.coreChargeTotal"] = core_charge_total
            update["$set"]["totals.claimTotal"] = parts_total + labour_total

        result = await self.claims.find_one_and_update(
            {"claimId": claim_id},
            update,
            return_document=True
        )

        return result

    async def submit_claim(
        self,
        claim_id: str,
        submitted_by: str
    ) -> Optional[Dict[str, Any]]:
        """
        Submit a draft claim for review.

        Args:
            claim_id: Claim ID to submit
            submitted_by: User ID submitting the claim

        Returns:
            Updated claim document or None if not found
        """
        existing = await self.claims.find_one({"claimId": claim_id})
        if not existing:
            return None
        if existing.get("status") != "Draft":
            raise ValueError(f"Cannot submit claim in status: {existing.get('status')}")

        now = datetime.utcnow()

        update = {
            "$set": {
                "status": "Submitted",
                "submittedAt": now,
                "updatedAt": now,
                "sla.responseDeadline": now + timedelta(days=3),
                "sla.resolutionDeadline": now + timedelta(days=7)
            },
            "$push": {
                "statusHistory": {
                    "status": "Submitted",
                    "timestamp": now,
                    "updatedBy": submitted_by,
                    "notes": None
                }
            }
        }

        result = await self.claims.find_one_and_update(
            {"claimId": claim_id},
            update,
            return_document=True
        )

        return result

    async def get_claims_by_dealer(
        self,
        dealer_id: str,
        status: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get claims for a specific dealer.

        Args:
            dealer_id: Dealer ID
            status: Optional list of statuses to filter by
            limit: Number of claims to return
            offset: Number of claims to skip

        Returns:
            List of claim documents
        """
        query = {"dealer.dealerId": dealer_id}
        if status:
            query["status"] = {"$in": status}

        cursor = self.claims.find(
            query,
            {
                "_id": 1,
                "claimId": 1,
                "status": 1,
                "vehicle": 1,
                "customer.name": 1,
                "failure.category": 1,
                "totals": 1,
                "submittedAt": 1,
                "createdAt": 1
            }
        ).sort("createdAt", -1).skip(offset).limit(limit)

        claims = await cursor.to_list(length=limit)
        return claims

    async def get_claim_statistics(
        self,
        dealer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get claim statistics for dashboard.

        Args:
            dealer_id: Optional dealer ID for dealer-specific stats

        Returns:
            Dict with claim statistics
        """
        match_stage = {}
        if dealer_id:
            match_stage["dealer.dealerId"] = dealer_id

        pipeline = [
            {"$match": match_stage} if match_stage else {"$match": {}},
            {
                "$facet": {
                    "totalClaims": [{"$count": "count"}],
                    "byStatus": [
                        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
                    ],
                    "totalValue": [
                        {"$group": {"_id": None, "total": {"$sum": "$totals.claimTotal"}}}
                    ],
                    "avgProcessingDays": [
                        {"$match": {"status": {"$in": ["Approved", "Rejected", "Paid"]}}},
                        {"$addFields": {
                            "processingDays": {
                                "$divide": [
                                    {"$subtract": ["$updatedAt", "$submittedAt"]},
                                    86400000  # ms to days
                                ]
                            }
                        }},
                        {"$group": {"_id": None, "avg": {"$avg": "$processingDays"}}}
                    ],
                    "thisMonthValue": [
                        {"$match": {
                            "submittedAt": {
                                "$gte": datetime(datetime.utcnow().year, datetime.utcnow().month, 1)
                            }
                        }},
                        {"$group": {"_id": None, "total": {"$sum": "$totals.claimTotal"}}}
                    ]
                }
            }
        ]

        cursor = await self.claims.aggregate(pipeline)
        result = await cursor.to_list(length=1)

        if not result:
            return {
                "totalClaims": 0,
                "statusCounts": {},
                "totalClaimValue": 0,
                "avgProcessingDays": 0,
                "claimsValueThisMonth": 0,
                "rejectionRate": 0
            }

        data = result[0]

        # Parse status counts
        status_counts = {
            item["_id"]: item["count"]
            for item in data.get("byStatus", [])
        }

        # Calculate rejection rate
        approved = status_counts.get("Approved", 0)
        rejected = status_counts.get("Rejected", 0)
        decided = approved + rejected
        rejection_rate = (rejected / decided * 100) if decided > 0 else 0

        return {
            "totalClaims": data["totalClaims"][0]["count"] if data.get("totalClaims") else 0,
            "statusCounts": {
                "pending": status_counts.get("Submitted", 0),
                "underReview": status_counts.get("Under Review", 0),
                "approved": approved,
                "rejected": rejected,
                "paid": status_counts.get("Paid", 0),
                "draft": status_counts.get("Draft", 0)
            },
            "totalClaimValue": data["totalValue"][0]["total"] if data.get("totalValue") else 0,
            "avgProcessingDays": round(data["avgProcessingDays"][0]["avg"], 1) if data.get("avgProcessingDays") else 0,
            "claimsValueThisMonth": data["thisMonthValue"][0]["total"] if data.get("thisMonthValue") else 0,
            "rejectionRate": round(rejection_rate, 1)
        }

    async def autocomplete_claims(
        self,
        query: str,
        field: str = "claimId",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get autocomplete suggestions for claims.

        Searches across all autocomplete-enabled fields (claimId, customer.name, 
        vehicle.registrationNumber) simultaneously for best results.

        Args:
            query: Partial search text
            field: Ignored - searches all fields
            limit: Maximum number of suggestions

        Returns:
            List of autocomplete suggestions
        """
        # Use compound query to search across ALL autocomplete fields
        pipeline = [
            {"$search": {
                "index": settings.claims_search_index,
                "compound": {
                    "should": [
                        {
                            "autocomplete": {
                                "query": query,
                                "path": "claimId",
                                "fuzzy": {"maxEdits": 1, "prefixLength": 2}
                            }
                        },
                        {
                            "autocomplete": {
                                "query": query,
                                "path": "customer.name",
                                "fuzzy": {"maxEdits": 1, "prefixLength": 2}
                            }
                        },
                        {
                            "autocomplete": {
                                "query": query,
                                "path": "vehicle.registrationNumber",
                                "fuzzy": {"maxEdits": 1, "prefixLength": 2}
                            }
                        }
                    ],
                    "minimumShouldMatch": 1
                }
            }},
            {"$limit": limit},
            {"$project": {
                "_id": 0,
                "claimId": 1,
                "customerName": "$customer.name",
                "vehicleModel": "$vehicle.modelName",
                "registrationNumber": "$vehicle.registrationNumber",
                "status": 1
            }}
        ]

        cursor = await self.claims.aggregate(pipeline)
        suggestions = await cursor.to_list(length=limit)

        return suggestions

    async def get_claim_trend(
        self,
        months: int = 12,
        dealer_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get monthly claims trend for charts.

        Args:
            months: Number of months to include
            dealer_id: Optional dealer ID for dealer-specific trend

        Returns:
            List of monthly trend data
        """
        start_date = datetime.utcnow() - timedelta(days=months * 30)

        match_stage = {"submittedAt": {"$gte": start_date}}
        if dealer_id:
            match_stage["dealer.dealerId"] = dealer_id

        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$submittedAt"},
                        "month": {"$month": "$submittedAt"}
                    },
                    "claimsCount": {"$sum": 1},
                    "totalValue": {"$sum": "$totals.claimTotal"},
                    "approvedCount": {
                        "$sum": {"$cond": [{"$eq": ["$status", "Approved"]}, 1, 0]}
                    },
                    "rejectedCount": {
                        "$sum": {"$cond": [{"$eq": ["$status", "Rejected"]}, 1, 0]}
                    }
                }
            },
            {"$sort": {"_id.year": 1, "_id.month": 1}},
            {
                "$project": {
                    "_id": 0,
                    "period": {
                        "$concat": [
                            {"$toString": "$_id.year"},
                            "-",
                            {"$cond": [
                                {"$lt": ["$_id.month", 10]},
                                {"$concat": ["0", {"$toString": "$_id.month"}]},
                                {"$toString": "$_id.month"}
                            ]}
                        ]
                    },
                    "claimsCount": 1,
                    "totalValue": 1,
                    "approvedCount": 1,
                    "rejectedCount": 1,
                    "approvalRate": {
                        "$multiply": [
                            {"$divide": [
                                "$approvedCount",
                                {"$add": ["$approvedCount", "$rejectedCount", 0.001]}
                            ]},
                            100
                        ]
                    }
                }
            }
        ]

        cursor = await self.claims.aggregate(pipeline)
        trend = await cursor.to_list(length=months)
        return trend
