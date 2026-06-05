"""Aggregation pipelines package for OEMPartner Dealer Portal."""
from .materialized_views import (
    # Product stats
    refresh_product_core_stats,
    refresh_product_analytics,
    refresh_product_stats,
    # Claim stats
    refresh_claim_core_stats,
    refresh_claim_analytics,
    refresh_dealer_claim_stats,
    refresh_claim_stats,
    # Claims trend
    refresh_claims_trend,
    # All views
    refresh_all_views
)

__all__ = [
    # Product stats (granular)
    "refresh_product_core_stats",
    "refresh_product_analytics",
    "refresh_product_stats",
    # Claim stats (granular)
    "refresh_claim_core_stats",
    "refresh_claim_analytics",
    "refresh_dealer_claim_stats",
    "refresh_claim_stats",
    # Claims trend
    "refresh_claims_trend",
    # All views
    "refresh_all_views"
]
