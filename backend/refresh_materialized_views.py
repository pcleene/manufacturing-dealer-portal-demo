"""
Materialized views refresh script for OEMPartner Dealer Portal.

This script manually refreshes the materialized views (aggregation pipelines)
that pre-compute dashboard statistics for faster query performance.

Manufacturing Group Malaysia - OEMPartner Dealer Portal

Usage:
    python refresh_materialized_views.py --all
    python refresh_materialized_views.py --view product_stats
    python refresh_materialized_views.py --view claim_stats
    python refresh_materialized_views.py --view claims_trend
    python refresh_materialized_views.py --view dealer_claim_stats

Requirements:
    - MongoDB Atlas connection configured
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime

from pymongo import AsyncMongoClient

from app.config import settings
from app.aggregations.materialized_views import (
    refresh_product_stats,
    refresh_claim_stats,
    refresh_claims_trend,
    refresh_all_views
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main(args):
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("OEMPartner Dealer Portal - Materialized Views Refresh Script")
    logger.info("=" * 60)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Connect to MongoDB
    logger.info(f"Connecting to MongoDB: {settings.mongodb_db_name}")
    client = AsyncMongoClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    try:
        # Test connection
        await db.command('ping')
        logger.info("MongoDB connection successful")

        start_time = datetime.now()

        if args.all:
            logger.info("Refreshing ALL materialized views...")
            await refresh_all_views(db)
        elif args.view == 'product_stats':
            logger.info("Refreshing product statistics view...")
            await refresh_product_stats(db)
        elif args.view == 'claim_stats':
            logger.info("Refreshing claim statistics views...")
            await refresh_claim_stats(db)
        elif args.view == 'claims_trend':
            logger.info("Refreshing claims trend view...")
            await refresh_claims_trend(db)
        elif args.view == 'dealer_claim_stats':
            logger.info("Refreshing per-dealer claim statistics view...")
            # Import the specific pipeline function
            from app.aggregations.materialized_views import get_dealer_claim_stats_pipeline
            pipeline = get_dealer_claim_stats_pipeline()
            await db.warrantyClaims.aggregate(pipeline).to_list(None)
            logger.info("Per-dealer claim statistics refreshed")
        else:
            logger.error(f"Unknown view: {args.view}")
            sys.exit(1)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("=" * 60)
        logger.info(f"Refresh completed in {duration:.2f} seconds")
        logger.info("=" * 60)

        # Print view statistics
        if args.stats:
            await print_view_statistics(db)

    except Exception as e:
        logger.error(f"Error during refresh: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        await client.close()


async def print_view_statistics(db):
    """Print statistics about materialized views."""
    logger.info("\nMaterialized View Statistics:")
    logger.info("-" * 40)

    views = [
        ("mv_product_stats", "Product Statistics"),
        ("mv_claim_stats", "Claim Statistics"),
        ("mv_dealer_claim_stats", "Per-Dealer Claim Stats"),
        ("mv_claims_trend", "Claims Trend"),
    ]

    for collection_name, display_name in views:
        try:
            count = await db[collection_name].count_documents({})

            # Get last refresh time
            doc = await db[collection_name].find_one(
                {},
                sort=[("refreshedAt", -1)]
            )
            last_refresh = doc.get("refreshedAt", "Never") if doc else "Never"

            if isinstance(last_refresh, datetime):
                last_refresh = last_refresh.strftime("%Y-%m-%d %H:%M:%S")

            logger.info(f"  {display_name}:")
            logger.info(f"    Documents: {count}")
            logger.info(f"    Last Refresh: {last_refresh}")
        except Exception as e:
            logger.warning(f"  {display_name}: Error - {e}")

    logger.info("-" * 40)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Refresh materialized views for OEMPartner Dealer Portal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available Views:
  product_stats       - Product catalog statistics (categories, inventory, pricing)
  claim_stats         - Global claim statistics (by status, failure category, etc.)
  dealer_claim_stats  - Per-dealer claim statistics
  claims_trend        - Monthly claims trend data

Examples:
  # Refresh all views
  python refresh_materialized_views.py --all

  # Refresh specific view
  python refresh_materialized_views.py --view product_stats

  # Refresh and show statistics
  python refresh_materialized_views.py --all --stats

Recommended Refresh Schedule:
  - product_stats:       Every 15-30 minutes
  - claim_stats:         Every 15-30 minutes
  - dealer_claim_stats:  Every 30 minutes
  - claims_trend:        Daily (or hourly)

For production, set up Atlas Triggers or a cron job to run this script automatically.
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all",
        action="store_true",
        help="Refresh all materialized views"
    )
    group.add_argument(
        "--view",
        choices=["product_stats", "claim_stats", "claims_trend", "dealer_claim_stats"],
        help="Specific view to refresh"
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print view statistics after refresh"
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args))
