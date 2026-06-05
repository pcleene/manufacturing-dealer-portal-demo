"""
Materialized view aggregation pipelines for OEMPartner Dealer Portal dashboard.

This module contains materialized view pipelines that pre-aggregate
data for dashboard statistics. These should be executed on a schedule using
Atlas Triggers or APScheduler.

Pipeline Structure:
- Product pipelines are split into core stats and analytics
- Claim pipelines are split into core stats and processing analytics
- Each pipeline outputs to the same collection with different _id values

Manufacturing Group Malaysia - OEMPartner Dealer Portal
"""
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


# =======================
# PRODUCT MATERIALIZED VIEWS
# =======================

def get_product_core_stats_pipeline() -> List[Dict[str, Any]]:
    """
    Pipeline for core product statistics (mv_product_stats).

    Contains essential dashboard metrics:
    - Total counts and category breakdown
    - Stock status alerts (low stock, out of stock)
    - Availability status distribution
    - New products this quarter

    Refresh frequency: Every 15 minutes
    Size: Very small (~1 document)
    """
    return [
        {
            "$facet": {
                "totalProducts": [
                    {"$count": "count"}
                ],
                "byCategory": [
                    {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ],
                "byAvailabilityStatus": [
                    {"$group": {"_id": "$inventory.status", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ],
                "lowStockCount": [
                    {
                        "$match": {
                            "$expr": {
                                "$lte": ["$inventory.totalQuantity", "$inventory.reorderPoint"]
                            }
                        }
                    },
                    {"$count": "count"}
                ],
                "outOfStockCount": [
                    {"$match": {"inventory.status": "Out of Stock"}},
                    {"$count": "count"}
                ],
                "newProductsThisQuarter": [
                    {
                        "$match": {
                            "createdAt": {
                                "$gte": {
                                    "$dateSubtract": {
                                        "startDate": "$$NOW",
                                        "unit": "month",
                                        "amount": 3
                                    }
                                }
                            }
                        }
                    },
                    {"$count": "count"}
                ]
            }
        },
        {
            "$addFields": {
                "_id": "product_core_stats",
                "viewType": "product_core_stats",
                "refreshedAt": "$$NOW",
                "totalCount": {"$arrayElemAt": ["$totalProducts.count", 0]},
                "lowStockAlerts": {"$ifNull": [{"$arrayElemAt": ["$lowStockCount.count", 0]}, 0]},
                "outOfStock": {"$ifNull": [{"$arrayElemAt": ["$outOfStockCount.count", 0]}, 0]},
                "newThisQuarter": {"$ifNull": [{"$arrayElemAt": ["$newProductsThisQuarter.count", 0]}, 0]}
            }
        },
        {
            "$merge": {
                "into": "mv_product_stats",
                "on": "_id",
                "whenMatched": "replace",
                "whenNotMatched": "insert"
            }
        }
    ]


def get_product_analytics_pipeline() -> List[Dict[str, Any]]:
    """
    Pipeline for product inventory analytics (mv_product_stats).

    Contains deeper analytics:
    - Inventory value calculations
    - Price distribution buckets
    - Subcategory breakdown
    - Top model series compatibility

    Refresh frequency: Every 30 minutes (less critical)
    Size: Very small (~1 document)
    Note: Uses $unwind for model compatibility analysis
    """
    return [
        {
            "$facet": {
                "bySubcategory": [
                    {"$group": {
                        "_id": {"category": "$category", "subcategory": "$subcategory"},
                        "count": {"$sum": 1}
                    }},
                    {"$sort": {"count": -1}},
                    {"$limit": 20}
                ],
                "priceDistribution": [
                    {
                        "$bucket": {
                            "groupBy": "$pricing.msrp",
                            "boundaries": [0, 50, 100, 200, 500, 1000, 5000, 10000, 50000],
                            "default": "50000+",
                            "output": {
                                "count": {"$sum": 1},
                                "avgPrice": {"$avg": "$pricing.msrp"}
                            }
                        }
                    }
                ],
                "topModelSeries": [
                    {"$unwind": "$compatibleModels"},
                    {"$group": {"_id": "$compatibleModels.modelCode", "productCount": {"$sum": 1}}},
                    {"$sort": {"productCount": -1}},
                    {"$limit": 10}
                ],
                "inventoryValue": [
                    {
                        "$group": {
                            "_id": None,
                            "totalValue": {
                                "$sum": {"$multiply": ["$pricing.msrp", "$inventory.totalQuantity"]}
                            },
                            "avgUnitPrice": {"$avg": "$pricing.msrp"},
                            "totalUnits": {"$sum": "$inventory.totalQuantity"}
                        }
                    }
                ]
            }
        },
        {
            "$addFields": {
                "_id": "product_analytics",
                "viewType": "product_analytics",
                "refreshedAt": "$$NOW",
                "inventoryValue": {"$arrayElemAt": ["$inventoryValue", 0]}
            }
        },
        {
            "$merge": {
                "into": "mv_product_stats",
                "on": "_id",
                "whenMatched": "replace",
                "whenNotMatched": "insert"
            }
        }
    ]


# =======================
# CLAIMS MATERIALIZED VIEWS
# =======================

def get_claim_core_stats_pipeline() -> List[Dict[str, Any]]:
    """
    Pipeline for core claim statistics (mv_claim_stats).

    Contains essential dashboard metrics:
    - Total counts and status breakdown
    - Failure category distribution
    - Vehicle model distribution
    - This month summary
    - SLA breach count

    Refresh frequency: Every 15 minutes
    Size: Very small (~1 document)
    """
    return [
        {
            "$facet": {
                "totalClaims": [
                    {"$count": "count"}
                ],
                "byStatus": [
                    {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ],
                "byFailureCategory": [
                    {"$group": {"_id": "$failure.category", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 15}
                ],
                "byVehicleModel": [
                    {"$group": {"_id": "$vehicle.modelCode", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 10}
                ],
                "thisMonthClaims": [
                    {
                        "$match": {
                            "submittedAt": {
                                "$gte": {
                                    "$dateFromParts": {
                                        "year": {"$year": "$$NOW"},
                                        "month": {"$month": "$$NOW"},
                                        "day": 1
                                    }
                                }
                            }
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "count": {"$sum": 1},
                            "totalValue": {"$sum": "$totals.claimTotal"}
                        }
                    }
                ],
                "slaMetrics": [
                    {"$match": {"sla.slaBreached": True}},
                    {"$count": "breachedCount"}
                ]
            }
        },
        {
            "$addFields": {
                "_id": "claim_core_stats",
                "viewType": "claim_core_stats",
                "refreshedAt": "$$NOW",
                "totalCount": {"$arrayElemAt": ["$totalClaims.count", 0]},
                "thisMonth": {"$arrayElemAt": ["$thisMonthClaims", 0]},
                "slaBreached": {"$ifNull": [{"$arrayElemAt": ["$slaMetrics.breachedCount", 0]}, 0]}
            }
        },
        {
            "$merge": {
                "into": "mv_claim_stats",
                "on": "_id",
                "whenMatched": "replace",
                "whenNotMatched": "insert"
            }
        }
    ]


def get_claim_analytics_pipeline() -> List[Dict[str, Any]]:
    """
    Pipeline for claim processing analytics (mv_claim_stats).

    Contains deeper analytics:
    - Claim value statistics (total, approved, average)
    - Processing time metrics
    - Rejection rate calculation
    - Regional distribution
    - Claim type distribution (parts only, labour only, mixed)

    Refresh frequency: Every 30 minutes (less critical)
    Size: Very small (~1 document)
    """
    return [
        {
            "$facet": {
                "byDealerRegion": [
                    {"$group": {
                        "_id": "$dealer.region",
                        "count": {"$sum": 1},
                        "totalValue": {"$sum": "$totals.claimTotal"}
                    }},
                    {"$sort": {"count": -1}}
                ],
                "claimValues": [
                    {
                        "$group": {
                            "_id": None,
                            "totalClaimValue": {"$sum": "$totals.claimTotal"},
                            "totalApprovedValue": {"$sum": "$totals.approvedTotal"},
                            "avgClaimValue": {"$avg": "$totals.claimTotal"},
                            "maxClaimValue": {"$max": "$totals.claimTotal"},
                            "minClaimValue": {"$min": "$totals.claimTotal"}
                        }
                    }
                ],
                "processingTimes": [
                    {"$match": {"status": {"$in": ["Approved", "Rejected", "Closed"]}}},
                    {
                        "$project": {
                            "processingDays": {
                                "$dateDiff": {
                                    "startDate": "$submittedAt",
                                    "endDate": {"$ifNull": ["$review.reviewedAt", "$updatedAt"]},
                                    "unit": "day"
                                }
                            }
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "avgProcessingDays": {"$avg": "$processingDays"},
                            "maxProcessingDays": {"$max": "$processingDays"},
                            "minProcessingDays": {"$min": "$processingDays"}
                        }
                    }
                ],
                "rejectionRate": [
                    {
                        "$group": {
                            "_id": None,
                            "totalResolved": {
                                "$sum": {
                                    "$cond": [{"$in": ["$status", ["Approved", "Rejected"]]}, 1, 0]
                                }
                            },
                            "totalRejected": {
                                "$sum": {
                                    "$cond": [{"$eq": ["$status", "Rejected"]}, 1, 0]
                                }
                            }
                        }
                    },
                    {
                        "$project": {
                            "rejectionRate": {
                                "$cond": [
                                    {"$gt": ["$totalResolved", 0]},
                                    {"$divide": ["$totalRejected", "$totalResolved"]},
                                    0
                                ]
                            }
                        }
                    }
                ],
                "claimTypeDistribution": [
                    {
                        "$group": {
                            "_id": None,
                            "partsOnly": {
                                "$sum": {
                                    "$cond": [
                                        {"$and": [
                                            {"$gt": [{"$size": {"$ifNull": ["$partsClaimed", []]}}, 0]},
                                            {"$eq": [{"$size": {"$ifNull": ["$labourClaimed", []]}}, 0]}
                                        ]},
                                        1, 0
                                    ]
                                }
                            },
                            "labourOnly": {
                                "$sum": {
                                    "$cond": [
                                        {"$and": [
                                            {"$eq": [{"$size": {"$ifNull": ["$partsClaimed", []]}}, 0]},
                                            {"$gt": [{"$size": {"$ifNull": ["$labourClaimed", []]}}, 0]}
                                        ]},
                                        1, 0
                                    ]
                                }
                            },
                            "partsAndLabour": {
                                "$sum": {
                                    "$cond": [
                                        {"$and": [
                                            {"$gt": [{"$size": {"$ifNull": ["$partsClaimed", []]}}, 0]},
                                            {"$gt": [{"$size": {"$ifNull": ["$labourClaimed", []]}}, 0]}
                                        ]},
                                        1, 0
                                    ]
                                }
                            }
                        }
                    }
                ]
            }
        },
        {
            "$addFields": {
                "_id": "claim_analytics",
                "viewType": "claim_analytics",
                "refreshedAt": "$$NOW",
                "processing": {"$arrayElemAt": ["$processingTimes", 0]},
                "values": {"$arrayElemAt": ["$claimValues", 0]},
                "rejection": {"$arrayElemAt": ["$rejectionRate", 0]},
                "claimTypes": {"$arrayElemAt": ["$claimTypeDistribution", 0]}
            }
        },
        {
            "$merge": {
                "into": "mv_claim_stats",
                "on": "_id",
                "whenMatched": "replace",
                "whenNotMatched": "insert"
            }
        }
    ]


def get_dealer_claim_stats_pipeline() -> List[Dict[str, Any]]:
    """
    Pipeline for per-dealer claim statistics (mv_dealer_claim_stats).

    Refresh frequency: Every 30 minutes
    Size: ~10-50 documents (one per active dealer)
    """
    return [
        {
            "$group": {
                "_id": "$dealer.dealerId",
                "dealerName": {"$first": "$dealer.name"},
                "dealerRegion": {"$first": "$dealer.region"},
                "totalClaims": {"$sum": 1},
                "totalClaimValue": {"$sum": "$totals.claimTotal"},
                "totalApprovedValue": {"$sum": "$totals.approvedTotal"},
                "avgClaimValue": {"$avg": "$totals.claimTotal"},
                "pendingCount": {
                    "$sum": {"$cond": [{"$eq": ["$status", "Pending Review"]}, 1, 0]}
                },
                "underReviewCount": {
                    "$sum": {"$cond": [{"$eq": ["$status", "Under Review"]}, 1, 0]}
                },
                "approvedCount": {
                    "$sum": {"$cond": [{"$eq": ["$status", "Approved"]}, 1, 0]}
                },
                "rejectedCount": {
                    "$sum": {"$cond": [{"$eq": ["$status", "Rejected"]}, 1, 0]}
                },
                "paidCount": {
                    "$sum": {"$cond": [{"$eq": ["$status", "Paid"]}, 1, 0]}
                },
                "slaBreachedCount": {
                    "$sum": {"$cond": ["$sla.slaBreached", 1, 0]}
                },
                "lastClaimDate": {"$max": "$submittedAt"},
                "topFailureCategories": {"$push": "$failure.category"}
            }
        },
        {
            "$addFields": {
                "approvalRate": {
                    "$cond": [
                        {"$gt": [{"$add": ["$approvedCount", "$rejectedCount"]}, 0]},
                        {
                            "$divide": [
                                "$approvedCount",
                                {"$add": ["$approvedCount", "$rejectedCount"]}
                            ]
                        },
                        0
                    ]
                },
                "viewType": "dealer_claim_stats",
                "refreshedAt": "$$NOW"
            }
        },
        {
            "$merge": {
                "into": "mv_dealer_claim_stats",
                "on": "_id",
                "whenMatched": "replace",
                "whenNotMatched": "insert"
            }
        }
    ]


def get_claims_trend_pipeline() -> List[Dict[str, Any]]:
    """
    Pipeline for monthly claims trend (mv_claims_trend).

    Refresh frequency: Daily
    Size: Small (~12-24 documents, one per month)
    """
    return [
        {
            "$addFields": {
                "claimMonth": {
                    "$dateToString": {
                        "format": "%Y-%m",
                        "date": "$submittedAt"
                    }
                }
            }
        },
        {
            "$group": {
                "_id": "$claimMonth",
                "totalClaims": {"$sum": 1},
                "totalClaimValue": {"$sum": "$totals.claimTotal"},
                "totalApprovedValue": {"$sum": "$totals.approvedTotal"},
                "avgClaimValue": {"$avg": "$totals.claimTotal"},
                "approvedCount": {
                    "$sum": {"$cond": [{"$eq": ["$status", "Approved"]}, 1, 0]}
                },
                "rejectedCount": {
                    "$sum": {"$cond": [{"$eq": ["$status", "Rejected"]}, 1, 0]}
                },
                "pendingCount": {
                    "$sum": {"$cond": [{"$in": ["$status", ["Pending Review", "Under Review", "Awaiting Parts"]]}, 1, 0]}
                },
                "paidCount": {
                    "$sum": {"$cond": [{"$eq": ["$status", "Paid"]}, 1, 0]}
                },
                "partsClaimValue": {"$sum": "$totals.partsTotal"},
                "labourClaimValue": {"$sum": "$totals.labourTotal"},
                "uniqueDealers": {"$addToSet": "$dealer.dealerId"},
                "uniqueVehicleModels": {"$addToSet": "$vehicle.modelCode"}
            }
        },
        {
            "$addFields": {
                "dealerCount": {"$size": "$uniqueDealers"},
                "vehicleModelCount": {"$size": "$uniqueVehicleModels"},
                "approvalRate": {
                    "$cond": [
                        {"$gt": [{"$add": ["$approvedCount", "$rejectedCount"]}, 0]},
                        {
                            "$round": [
                                {
                                    "$multiply": [
                                        {"$divide": ["$approvedCount", {"$add": ["$approvedCount", "$rejectedCount"]}]},
                                        100
                                    ]
                                },
                                2
                            ]
                        },
                        0
                    ]
                }
            }
        },
        {
            "$project": {
                "_id": 1,
                "month": "$_id",
                "totalClaims": 1,
                "totalClaimValue": {"$round": ["$totalClaimValue", 2]},
                "totalApprovedValue": {"$round": ["$totalApprovedValue", 2]},
                "avgClaimValue": {"$round": ["$avgClaimValue", 2]},
                "approvedCount": 1,
                "rejectedCount": 1,
                "pendingCount": 1,
                "paidCount": 1,
                "approvalRate": 1,
                "partsClaimValue": {"$round": ["$partsClaimValue", 2]},
                "labourClaimValue": {"$round": ["$labourClaimValue", 2]},
                "dealerCount": 1,
                "vehicleModelCount": 1
            }
        },
        {"$sort": {"_id": -1}},
        {"$limit": 24},
        {
            "$addFields": {
                "viewType": "claims_trend",
                "refreshedAt": "$$NOW"
            }
        },
        {
            "$merge": {
                "into": "mv_claims_trend",
                "on": "_id",
                "whenMatched": "replace",
                "whenNotMatched": "insert"
            }
        }
    ]


def get_dealer_claims_trend_pipeline(dealer_id: str) -> List[Dict[str, Any]]:
    """
    Pipeline for per-dealer claims trend (not materialized, run on-demand).

    Args:
        dealer_id: The dealer ID to filter by

    Returns:
        Aggregation pipeline for dealer-specific monthly claims trend
    """
    return [
        {"$match": {"dealer.dealerId": dealer_id}},
        {
            "$addFields": {
                "claimMonth": {
                    "$dateToString": {
                        "format": "%Y-%m",
                        "date": "$submittedAt"
                    }
                }
            }
        },
        {
            "$group": {
                "_id": "$claimMonth",
                "totalClaims": {"$sum": 1},
                "totalClaimValue": {"$sum": "$totals.claimTotal"},
                "approvedCount": {
                    "$sum": {"$cond": [{"$eq": ["$status", "Approved"]}, 1, 0]}
                },
                "rejectedCount": {
                    "$sum": {"$cond": [{"$eq": ["$status", "Rejected"]}, 1, 0]}
                },
                "avgClaimValue": {"$avg": "$totals.claimTotal"}
            }
        },
        {
            "$addFields": {
                "approvalRate": {
                    "$cond": [
                        {"$gt": [{"$add": ["$approvedCount", "$rejectedCount"]}, 0]},
                        {
                            "$round": [
                                {
                                    "$multiply": [
                                        {"$divide": ["$approvedCount", {"$add": ["$approvedCount", "$rejectedCount"]}]},
                                        100
                                    ]
                                },
                                2
                            ]
                        },
                        0
                    ]
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "month": "$_id",
                "totalClaims": 1,
                "totalClaimValue": {"$round": ["$totalClaimValue", 2]},
                "approvedCount": 1,
                "rejectedCount": 1,
                "avgClaimValue": {"$round": ["$avgClaimValue", 2]},
                "approvalRate": 1
            }
        },
        {"$sort": {"month": -1}},
        {"$limit": 12}
    ]


# =======================
# REFRESH FUNCTIONS
# =======================

async def refresh_product_core_stats(db):
    """Refresh core product statistics materialized view."""
    logger.info("Refreshing core product statistics...")
    pipeline = get_product_core_stats_pipeline()
    cursor = await db.products.aggregate(pipeline)
    await cursor.to_list(None)
    logger.info("✅ Core product statistics refreshed")


async def refresh_product_analytics(db):
    """Refresh product analytics materialized view."""
    logger.info("Refreshing product analytics...")
    pipeline = get_product_analytics_pipeline()
    cursor = await db.products.aggregate(pipeline)
    await cursor.to_list(None)
    logger.info("✅ Product analytics refreshed")


async def refresh_product_stats(db):
    """Refresh all product statistics (core + analytics)."""
    await refresh_product_core_stats(db)
    await refresh_product_analytics(db)


async def refresh_claim_core_stats(db):
    """Refresh core claim statistics materialized view."""
    logger.info("Refreshing core claim statistics...")
    pipeline = get_claim_core_stats_pipeline()
    cursor = await db.warrantyClaims.aggregate(pipeline)
    await cursor.to_list(None)
    logger.info("✅ Core claim statistics refreshed")


async def refresh_claim_analytics(db):
    """Refresh claim analytics materialized view."""
    logger.info("Refreshing claim analytics...")
    pipeline = get_claim_analytics_pipeline()
    cursor = await db.warrantyClaims.aggregate(pipeline)
    await cursor.to_list(None)
    logger.info("✅ Claim analytics refreshed")


async def refresh_dealer_claim_stats(db):
    """Refresh per-dealer claim statistics materialized view."""
    logger.info("Refreshing per-dealer claim statistics...")
    pipeline = get_dealer_claim_stats_pipeline()
    cursor = await db.warrantyClaims.aggregate(pipeline)
    await cursor.to_list(None)
    logger.info("✅ Per-dealer claim statistics refreshed")


async def refresh_claim_stats(db):
    """Refresh all claim statistics (core + analytics + per-dealer)."""
    await refresh_claim_core_stats(db)
    await refresh_claim_analytics(db)
    await refresh_dealer_claim_stats(db)


async def refresh_claims_trend(db):
    """Refresh claims trend materialized view."""
    logger.info("Refreshing claims trend...")
    pipeline = get_claims_trend_pipeline()
    cursor = await db.warrantyClaims.aggregate(pipeline)
    await cursor.to_list(None)
    logger.info("✅ Claims trend refreshed")


async def refresh_all_views(db):
    """Refresh all materialized views."""
    logger.info("🚀 Refreshing all materialized views...")

    # Product views (core first, then analytics)
    await refresh_product_core_stats(db)
    await refresh_product_analytics(db)

    # Claims views (core first, then analytics, then per-dealer)
    await refresh_claim_core_stats(db)
    await refresh_claim_analytics(db)
    await refresh_dealer_claim_stats(db)
    await refresh_claims_trend(db)

    logger.info("✅ All materialized views refreshed successfully!")
