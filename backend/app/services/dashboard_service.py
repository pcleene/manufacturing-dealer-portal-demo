"""
Dashboard service layer - Business logic for dashboard operations.

Manufacturing Group Manufacturing OEMPartner Dealer Portal.
Queries materialized views for fast dashboard responses.
"""
from typing import Dict, Any, List, Optional
import logging
import time
from datetime import datetime

from app.aggregations import (
    refresh_product_stats,
    refresh_product_core_stats,
    refresh_product_analytics,
    refresh_claim_stats,
    refresh_claim_core_stats,
    refresh_claim_analytics,
    refresh_dealer_claim_stats,
    refresh_claims_trend,
    refresh_all_views
)

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for dashboard statistics from materialized views."""

    def __init__(self, db):
        self.db = db

    # ===========================
    # PRODUCT DASHBOARD METHODS
    # ===========================

    async def get_product_stats(self) -> Dict[str, Any]:
        """
        Get product catalog statistics for dashboard.

        Reads from both product_core_stats and product_analytics documents
        and merges them into a single response.

        Returns data matching frontend ProductDashboardStats interface:
        - totalProducts: number
        - byCategory: Array<{ _id: string, count: number }>
        - byAvailabilityStatus: Array<{ _id: string, count: number }>
        - lowStockAlerts: number
        - outOfStock: number
        - newThisQuarter: number
        - inventoryValue?: { totalValue, avgUnitPrice, totalUnits }
        - refreshedAt?: string
        """
        # Fetch both core and analytics documents
        core_stats = await self.db.mv_product_stats.find_one({"_id": "product_core_stats"})
        analytics = await self.db.mv_product_stats.find_one({"_id": "product_analytics"})

        if not core_stats:
            # Fallback: compute stats directly if MV doesn't exist
            return await self._compute_product_stats_direct()

        # byCategory and byAvailabilityStatus come from core stats
        by_category = core_stats.get("byCategory", [])
        by_availability = core_stats.get("byAvailabilityStatus", [])

        # inventoryValue comes from analytics (if available)
        inventory_value = None
        if analytics:
            inv = analytics.get("inventoryValue")
            if inv:
                inventory_value = {
                    "totalValue": inv.get("totalValue", 0),
                    "avgUnitPrice": inv.get("avgUnitPrice", 0),
                    "totalUnits": inv.get("totalUnits", 0)
                }

        return {
            "totalProducts": core_stats.get("totalCount", 0),
            "byCategory": by_category,
            "byAvailabilityStatus": by_availability,
            "lowStockAlerts": core_stats.get("lowStockAlerts", 0),
            "outOfStock": core_stats.get("outOfStock", 0),
            "newThisQuarter": core_stats.get("newThisQuarter", 0),
            "inventoryValue": inventory_value,
            "refreshedAt": core_stats.get("refreshedAt")
        }

    async def _compute_product_stats_direct(self) -> Dict[str, Any]:
        """Compute product stats directly (fallback if MV doesn't exist)."""
        pipeline = [
            {
                "$facet": {
                    "totalProducts": [{"$count": "count"}],
                    "byCategory": [
                        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
                    ],
                    "byAvailability": [
                        {"$group": {"_id": "$inventory.status", "count": {"$sum": 1}}}
                    ],
                    "lowStock": [
                        {"$match": {"inventory.status": "Low Stock"}},
                        {"$count": "count"}
                    ],
                    "outOfStock": [
                        {"$match": {"inventory.status": "Out of Stock"}},
                        {"$count": "count"}
                    ],
                    "newThisQuarter": [
                        {"$match": {"createdAt": {"$gte": self._get_quarter_start()}}},
                        {"$count": "count"}
                    ],
                    "inventoryValue": [
                        {"$group": {
                            "_id": None,
                            "totalValue": {"$sum": {"$multiply": ["$pricing.msrp", "$inventory.totalQuantity"]}},
                            "totalUnits": {"$sum": "$inventory.totalQuantity"},
                            "avgUnitPrice": {"$avg": "$pricing.msrp"}
                        }}
                    ]
                }
            }
        ]

        cursor = await self.db.products.aggregate(pipeline)
        result = await cursor.to_list(length=1)

        if not result:
            return {
                "totalProducts": 0,
                "byCategory": [],
                "byAvailabilityStatus": [],
                "lowStockAlerts": 0,
                "outOfStock": 0,
                "newThisQuarter": 0,
                "refreshedAt": datetime.utcnow()
            }

        data = result[0]

        # byCategory as array
        by_category = [
            {"_id": item["_id"], "count": item["count"]}
            for item in data.get("byCategory", [])
            if item.get("_id")
        ]

        # byAvailabilityStatus as array
        by_availability = [
            {"_id": item["_id"], "count": item["count"]}
            for item in data.get("byAvailability", [])
            if item.get("_id")
        ]

        # inventoryValue
        inv_data = data.get("inventoryValue", [{}])[0] if data.get("inventoryValue") else {}
        inventory_value = {
            "totalValue": inv_data.get("totalValue", 0),
            "totalUnits": inv_data.get("totalUnits", 0),
            "avgUnitPrice": inv_data.get("avgUnitPrice", 0)
        } if inv_data else None

        return {
            "totalProducts": data["totalProducts"][0]["count"] if data.get("totalProducts") else 0,
            "byCategory": by_category,
            "byAvailabilityStatus": by_availability,
            "lowStockAlerts": data["lowStock"][0]["count"] if data.get("lowStock") else 0,
            "outOfStock": data["outOfStock"][0]["count"] if data.get("outOfStock") else 0,
            "newThisQuarter": data["newThisQuarter"][0]["count"] if data.get("newThisQuarter") else 0,
            "inventoryValue": inventory_value,
            "refreshedAt": datetime.utcnow()
        }

    def _get_quarter_start(self) -> datetime:
        """Get the start date of the current quarter."""
        now = datetime.utcnow()
        quarter = (now.month - 1) // 3
        return datetime(now.year, quarter * 3 + 1, 1)

    # ==============================
    # CLAIM DASHBOARD METHODS
    # ==============================

    async def get_claim_stats(
        self,
        dealer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get warranty claim statistics for dashboard.

        Reads from both claim_core_stats and claim_analytics documents
        and merges them into a single response.

        Returns data matching frontend ClaimDashboardStats interface:
        - totalClaims: number
        - byStatus: Array<{ _id: string, count: number }>
        - byFailureCategory: Array<{ _id: string, count: number }>
        - byVehicleModel: Array<{ _id: string, count: number }>
        - thisMonth?: { count, totalValue }
        - processing?: { avgProcessingDays, maxProcessingDays, minProcessingDays }
        - values?: { totalClaimValue, totalApprovedValue, avgClaimValue }
        - rejection?: { rejectionRate }
        - slaBreached: number
        - refreshedAt?: string
        """
        if dealer_id:
            # For dealer-specific stats, use the dealer claim stats collection
            result = await self.db.mv_dealer_claim_stats.find_one({"_id": dealer_id})
            if result:
                return self._format_dealer_claim_stats(result)

        # Fetch both core and analytics documents for global stats
        core_stats = await self.db.mv_claim_stats.find_one({"_id": "claim_core_stats"})
        analytics = await self.db.mv_claim_stats.find_one({"_id": "claim_analytics"})

        if not core_stats:
            return await self._compute_claim_stats_direct(dealer_id)

        # Core stats provide counts and distributions
        by_status = core_stats.get("byStatus", [])
        by_failure_category = core_stats.get("byFailureCategory", [])
        by_vehicle_model = core_stats.get("byVehicleModel", [])
        this_month = core_stats.get("thisMonth") or {"count": 0, "totalValue": 0}
        sla_breached = core_stats.get("slaBreached", 0)

        # Analytics provide processing times, values, rejection rates, regional data
        processing = {"avgProcessingDays": 0, "maxProcessingDays": 0, "minProcessingDays": 0}
        values = {"totalClaimValue": 0, "totalApprovedValue": 0, "avgClaimValue": 0}
        rejection = {"rejectionRate": 0}
        by_dealer_region = []

        if analytics:
            proc = analytics.get("processing")
            if proc:
                processing = {
                    "avgProcessingDays": proc.get("avgProcessingDays", 0),
                    "maxProcessingDays": proc.get("maxProcessingDays", 0),
                    "minProcessingDays": proc.get("minProcessingDays", 0)
                }

            val = analytics.get("values")
            if val:
                values = {
                    "totalClaimValue": val.get("totalClaimValue", 0),
                    "totalApprovedValue": val.get("totalApprovedValue", 0),
                    "avgClaimValue": val.get("avgClaimValue", 0)
                }

            rej = analytics.get("rejection")
            if rej:
                rejection = {"rejectionRate": rej.get("rejectionRate", 0)}

            by_dealer_region = analytics.get("byDealerRegion", [])

        return {
            "totalClaims": core_stats.get("totalCount", 0),
            "byStatus": by_status,
            "byFailureCategory": by_failure_category,
            "byVehicleModel": by_vehicle_model,
            "byDealerRegion": by_dealer_region,
            "thisMonth": this_month,
            "processing": processing,
            "values": values,
            "rejection": rejection,
            "slaBreached": sla_breached,
            "refreshedAt": core_stats.get("refreshedAt")
        }

    def _format_dealer_claim_stats(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format dealer-specific claim stats into standard response format."""
        return {
            "totalClaims": result.get("totalClaims", 0),
            "byStatus": [
                {"_id": "Pending Review", "count": result.get("pendingCount", 0)},
                {"_id": "Under Review", "count": result.get("underReviewCount", 0)},
                {"_id": "Approved", "count": result.get("approvedCount", 0)},
                {"_id": "Rejected", "count": result.get("rejectedCount", 0)},
                {"_id": "Paid", "count": result.get("paidCount", 0)}
            ],
            "byFailureCategory": [],  # Not available in per-dealer stats
            "byVehicleModel": [],  # Not available in per-dealer stats
            "thisMonth": {"count": 0, "totalValue": 0},  # Would need separate calculation
            "processing": {"avgProcessingDays": 0, "maxProcessingDays": 0, "minProcessingDays": 0},
            "values": {
                "totalClaimValue": result.get("totalClaimValue", 0),
                "totalApprovedValue": result.get("totalApprovedValue", 0),
                "avgClaimValue": result.get("avgClaimValue", 0)
            },
            "rejection": {"rejectionRate": 1 - result.get("approvalRate", 0)},
            "slaBreached": result.get("slaBreachedCount", 0),
            "refreshedAt": result.get("refreshedAt")
        }

    async def _compute_claim_stats_direct(
        self,
        dealer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compute claim stats directly (fallback if MV doesn't exist)."""
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
                    "byCategory": [
                        {"$group": {"_id": "$failure.category", "count": {"$sum": 1}}}
                    ],
                    "byVehicleModel": [
                        {"$group": {"_id": "$vehicle.modelName", "count": {"$sum": 1}}}
                    ],
                    "thisMonth": [
                        {"$match": {
                            "submittedAt": {
                                "$gte": datetime(datetime.utcnow().year, datetime.utcnow().month, 1)
                            }
                        }},
                        {"$group": {
                            "_id": None,
                            "count": {"$sum": 1},
                            "totalValue": {"$sum": "$totals.claimTotal"}
                        }}
                    ],
                    "processing": [
                        {"$match": {"status": {"$in": ["Approved", "Rejected", "Paid"]}}},
                        {"$match": {"submittedAt": {"$exists": True}}},
                        {"$addFields": {
                            "processingDays": {
                                "$divide": [
                                    {"$subtract": ["$updatedAt", "$submittedAt"]},
                                    86400000
                                ]
                            }
                        }},
                        {"$group": {
                            "_id": None,
                            "avg": {"$avg": "$processingDays"},
                            "max": {"$max": "$processingDays"},
                            "min": {"$min": "$processingDays"}
                        }}
                    ],
                    "values": [
                        {"$group": {
                            "_id": None,
                            "totalClaimValue": {"$sum": "$totals.claimTotal"},
                            "totalApprovedValue": {"$sum": "$totals.approvedTotal"},
                            "avgClaimValue": {"$avg": "$totals.claimTotal"}
                        }}
                    ],
                    "slaBreached": [
                        {"$match": {"sla.slaBreached": True}},
                        {"$count": "count"}
                    ]
                }
            }
        ]

        cursor = await self.db.warrantyClaims.aggregate(pipeline)
        result = await cursor.to_list(length=1)

        if not result:
            return {
                "totalClaims": 0,
                "byStatus": [],
                "byFailureCategory": [],
                "byVehicleModel": [],
                "thisMonth": {"count": 0, "totalValue": 0},
                "processing": {"avgProcessingDays": 0, "maxProcessingDays": 0, "minProcessingDays": 0},
                "values": {"totalClaimValue": 0, "totalApprovedValue": 0, "avgClaimValue": 0},
                "rejection": {"rejectionRate": 0},
                "slaBreached": 0,
                "refreshedAt": datetime.utcnow()
            }

        data = result[0]

        # byStatus as array
        by_status = [
            {"_id": item["_id"], "count": item["count"]}
            for item in data.get("byStatus", [])
            if item.get("_id")
        ]

        # byFailureCategory as array
        by_category = [
            {"_id": item["_id"], "count": item["count"]}
            for item in data.get("byCategory", [])
            if item.get("_id")
        ]

        # byVehicleModel as array
        by_vehicle = [
            {"_id": item["_id"], "count": item["count"]}
            for item in data.get("byVehicleModel", [])
            if item.get("_id")
        ]

        # Calculate rejection rate
        approved_count = sum(item["count"] for item in by_status if item["_id"] == "Approved")
        rejected_count = sum(item["count"] for item in by_status if item["_id"] == "Rejected")
        decided = approved_count + rejected_count
        rejection_rate = (rejected_count / decided * 100) if decided > 0 else 0

        # thisMonth
        this_month_data = data.get("thisMonth", [{}])[0] if data.get("thisMonth") else {}
        this_month = {
            "count": this_month_data.get("count", 0),
            "totalValue": this_month_data.get("totalValue", 0)
        }

        # processing
        proc_data = data.get("processing", [{}])[0] if data.get("processing") else {}
        processing = {
            "avgProcessingDays": round(proc_data.get("avg", 0), 1),
            "maxProcessingDays": round(proc_data.get("max", 0), 1),
            "minProcessingDays": round(proc_data.get("min", 0), 1)
        }

        # values
        val_data = data.get("values", [{}])[0] if data.get("values") else {}
        values = {
            "totalClaimValue": val_data.get("totalClaimValue", 0),
            "totalApprovedValue": val_data.get("totalApprovedValue", 0),
            "avgClaimValue": round(val_data.get("avgClaimValue", 0), 2)
        }

        return {
            "totalClaims": data["totalClaims"][0]["count"] if data.get("totalClaims") else 0,
            "byStatus": by_status,
            "byFailureCategory": by_category,
            "byVehicleModel": by_vehicle,
            "thisMonth": this_month,
            "processing": processing,
            "values": values,
            "rejection": {"rejectionRate": round(rejection_rate, 1)},
            "slaBreached": data["slaBreached"][0]["count"] if data.get("slaBreached") else 0,
            "refreshedAt": datetime.utcnow()
        }

    async def get_top_dealers(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top dealers by claim volume from materialized view.

        Args:
            limit: Number of top dealers to return

        Returns:
            List of top dealers with claim stats
        """
        cursor = self.db.mv_dealer_claim_stats.find({}).sort("totalClaims", -1).limit(limit)
        results = await cursor.to_list(length=limit)
        
        # Format for frontend
        return [
            {
                "_id": doc.get("_id"),
                "dealerName": doc.get("dealerName"),
                "dealerRegion": doc.get("dealerRegion"),
                "totalClaims": doc.get("totalClaims", 0),
                "totalClaimValue": doc.get("totalClaimValue", 0),
                "totalApprovedValue": doc.get("totalApprovedValue", 0),
                "avgClaimValue": doc.get("avgClaimValue", 0),
                "approvalRate": doc.get("approvalRate", 0),
                "slaBreachedCount": doc.get("slaBreachedCount", 0),
                "refreshedAt": doc.get("refreshedAt")
            }
            for doc in results
        ]

    async def get_claims_trend(
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
        # Try to get from materialized view first
        query = {}
        if dealer_id:
            query["dealerId"] = dealer_id

        cursor = self.db.mv_claims_trend.find(query).sort("period", -1).limit(months)
        results = await cursor.to_list(length=months)

        if results:
            return results

        # Fallback to direct computation
        from app.services.claim_service import ClaimService
        claim_service = ClaimService(self.db)
        return await claim_service.get_claim_trend(months, dealer_id)

    # ====================================
    # COMBINED DASHBOARD
    # ====================================

    async def get_dealer_dashboard(
        self,
        dealer_id: str
    ) -> Dict[str, Any]:
        """
        Get complete dashboard data for a dealer.

        Args:
            dealer_id: Dealer ID

        Returns:
            Combined dashboard with product and claim stats
        """
        # Get dealer info
        dealer = await self.db.dealers.find_one(
            {"dealerId": dealer_id},
            {"dealerId": 1, "name": 1, "region": 1, "metrics": 1}
        )

        if not dealer:
            raise ValueError(f"Dealer not found: {dealer_id}")

        # Get stats in parallel
        product_stats = await self.get_product_stats()
        claim_stats = await self.get_claim_stats(dealer_id)
        claims_trend = await self.get_claims_trend(6, dealer_id)

        return {
            "dealerId": dealer.get("dealerId"),
            "dealerName": dealer.get("name"),
            "region": dealer.get("region"),
            "metrics": dealer.get("metrics", {}),
            "products": product_stats,
            "claims": {
                **claim_stats,
                "trend": claims_trend
            },
            "refreshedAt": datetime.utcnow()
        }

    # ====================================
    # MATERIALIZED VIEWS REFRESH
    # ====================================

    async def refresh_views(
        self,
        views: List[str],
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Manually refresh materialized views.

        Args:
            views: List of view names to refresh, or ["all"] for all views
            force: Force refresh bypassing any caching

        Returns:
            Dict with refresh results

        Available views:
        - product_stats (both core and analytics)
        - product_core_stats
        - product_analytics
        - claim_stats (core, analytics, and per-dealer)
        - claim_core_stats
        - claim_analytics
        - dealer_claim_stats
        - claims_trend
        - all
        """
        results = {
            "refreshedViews": [],
            "skippedViews": [],
            "errors": {}
        }
        start_time = time.time()

        if "all" in views:
            logger.info("Refreshing all materialized views...")
            try:
                await refresh_all_views(self.db)
                results["refreshedViews"] = [
                    "product_core_stats", "product_analytics",
                    "claim_core_stats", "claim_analytics", "dealer_claim_stats",
                    "claims_trend"
                ]
            except Exception as e:
                logger.error(f"Error refreshing all views: {e}")
                results["errors"]["all"] = str(e)
        else:
            view_functions = {
                # Combined views
                "product_stats": refresh_product_stats,
                "claim_stats": refresh_claim_stats,
                # Granular product views
                "product_core_stats": refresh_product_core_stats,
                "product_analytics": refresh_product_analytics,
                # Granular claim views
                "claim_core_stats": refresh_claim_core_stats,
                "claim_analytics": refresh_claim_analytics,
                "dealer_claim_stats": refresh_dealer_claim_stats,
                # Trend
                "claims_trend": refresh_claims_trend
            }

            for view in views:
                if view not in view_functions:
                    results["skippedViews"].append(view)
                    results["errors"][view] = f"Unknown view: {view}"
                    continue

                try:
                    await view_functions[view](self.db)
                    results["refreshedViews"].append(view)
                except Exception as e:
                    logger.error(f"Error refreshing {view}: {e}")
                    results["errors"][view] = str(e)

        duration_ms = int((time.time() - start_time) * 1000)

        return {
            **results,
            "durationMs": duration_ms,
            "message": f"Refreshed {len(results['refreshedViews'])} views in {duration_ms}ms"
        }
