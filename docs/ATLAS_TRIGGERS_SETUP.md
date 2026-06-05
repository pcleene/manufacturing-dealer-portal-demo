# Atlas Triggers Setup Guide

This guide explains how to set up MongoDB Atlas Triggers to automatically refresh materialized views on a schedule for the OEMPartner Dealer Portal.

## Overview

Atlas Triggers allow you to run serverless functions on a schedule (similar to cron jobs). We use them to refresh the materialized views that power the dashboard statistics.

## Prerequisites

- MongoDB Atlas cluster (M10 or higher recommended)
- Atlas App Services enabled for your project
- `OEMPartner_dealer_portal` database with all collections created

## Step 1: Enable Atlas App Services

1. Log in to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Select your project
3. Click "App Services" in the left sidebar
4. Click "Create a New App" (if you haven't already)
5. Name it "OEMPartner-Dealer-Portal-Services"
6. Link it to your MongoDB cluster
7. Click "Create"

## Step 2: Create Scheduled Triggers

For each materialized view, create a separate scheduled trigger:

### 1. Product Stats Trigger

**Schedule:** Every 15 minutes (`*/15 * * * *`)

1. Go to App Services → Triggers
2. Click "Add a Trigger"
3. Configure:
   - **Trigger Type:** Scheduled
   - **Name:** `refresh_product_stats`
   - **Schedule Type:** Advanced (cron expression)
   - **Cron Schedule:** `*/15 * * * *`
   - **Select An Event Type:** Function

4. **Function Code:**

```javascript
exports = async function() {
  const mongodb = context.services.get("mongodb-atlas");
  const db = mongodb.db("OEMPartner_dealer_portal");

  console.log("Refreshing product stats...");

  try {
    await db.collection("products").aggregate([
      {
        $facet: {
          totalProducts: [{ $count: "count" }],
          byCategory: [
            { $group: { _id: "$category", count: { $sum: 1 } } },
            { $sort: { count: -1 } }
          ],
          byAvailability: [
            { $group: { _id: "$inventory.status", count: { $sum: 1 } } },
            { $sort: { count: -1 } }
          ],
          lowStockCount: [
            { $match: { "inventory.status": "Low Stock" } },
            { $count: "count" }
          ],
          outOfStockCount: [
            { $match: { "inventory.status": "Out of Stock" } },
            { $count: "count" }
          ],
          inventoryValue: [
            {
              $group: {
                _id: null,
                totalValue: { $sum: { $multiply: ["$pricing.msrp", "$inventory.totalQuantity"] } },
                totalUnits: { $sum: "$inventory.totalQuantity" },
                avgUnitPrice: { $avg: "$pricing.msrp" }
              }
            }
          ]
        }
      },
      {
        $addFields: {
          _id: "product_stats",
          totalProducts: { $arrayElemAt: ["$totalProducts.count", 0] },
          lowStockCount: { $ifNull: [{ $arrayElemAt: ["$lowStockCount.count", 0] }, 0] },
          outOfStockCount: { $ifNull: [{ $arrayElemAt: ["$outOfStockCount.count", 0] }, 0] },
          inventoryValue: { $arrayElemAt: ["$inventoryValue", 0] },
          computedAt: "$$NOW"
        }
      },
      {
        $merge: {
          into: "mv_product_stats",
          on: "_id",
          whenMatched: "replace",
          whenNotMatched: "insert"
        }
      }
    ]).toArray();

    console.log("✅ Product stats refreshed successfully at", new Date());
  } catch (error) {
    console.error("❌ Error refreshing product stats:", error);
  }
};
```

5. Click "Save"

### 2. Claim Stats Trigger

**Schedule:** Every 15 minutes (`*/15 * * * *`)

- **Name:** `refresh_claim_stats`
- **Cron Schedule:** `*/15 * * * *`

**Function Code:**

```javascript
exports = async function() {
  const mongodb = context.services.get("mongodb-atlas");
  const db = mongodb.db("OEMPartner_dealer_portal");

  console.log("Refreshing claim stats...");

  try {
    const now = new Date();
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);

    await db.collection("warrantyClaims").aggregate([
      {
        $facet: {
          totalClaims: [{ $count: "count" }],
          byStatus: [
            { $group: { _id: "$status", count: { $sum: 1 } } },
            { $sort: { count: -1 } }
          ],
          byCategory: [
            { $group: { _id: "$failure.category", count: { $sum: 1 } } },
            { $sort: { count: -1 } }
          ],
          byVehicleModel: [
            { $group: { _id: "$vehicle.modelName", count: { $sum: 1 } } },
            { $sort: { count: -1 } },
            { $limit: 10 }
          ],
          thisMonth: [
            { $match: { submittedAt: { $gte: monthStart } } },
            {
              $group: {
                _id: null,
                count: { $sum: 1 },
                totalValue: { $sum: "$totals.claimTotal" }
              }
            }
          ],
          values: [
            {
              $group: {
                _id: null,
                totalClaimValue: { $sum: "$totals.claimTotal" },
                totalApprovedValue: { $sum: "$totals.approvedTotal" },
                avgClaimValue: { $avg: "$totals.claimTotal" }
              }
            }
          ],
          slaBreached: [
            { $match: { "sla.slaBreached": true } },
            { $count: "count" }
          ]
        }
      },
      {
        $addFields: {
          _id: "global",
          totalClaims: { $ifNull: [{ $arrayElemAt: ["$totalClaims.count", 0] }, 0] },
          statusCounts: {
            $arrayToObject: {
              $map: {
                input: "$byStatus",
                as: "item",
                in: { k: "$$item._id", v: "$$item.count" }
              }
            }
          },
          thisMonthCount: { $ifNull: [{ $arrayElemAt: ["$thisMonth.count", 0] }, 0] },
          claimsValueThisMonth: { $ifNull: [{ $arrayElemAt: ["$thisMonth.totalValue", 0] }, 0] },
          totalClaimValue: { $ifNull: [{ $arrayElemAt: ["$values.totalClaimValue", 0] }, 0] },
          totalApprovedValue: { $ifNull: [{ $arrayElemAt: ["$values.totalApprovedValue", 0] }, 0] },
          avgClaimValue: { $ifNull: [{ $arrayElemAt: ["$values.avgClaimValue", 0] }, 0] },
          slaBreachedCount: { $ifNull: [{ $arrayElemAt: ["$slaBreached.count", 0] }, 0] },
          computedAt: "$$NOW"
        }
      },
      {
        $merge: {
          into: "mv_claim_stats",
          on: "_id",
          whenMatched: "replace",
          whenNotMatched: "insert"
        }
      }
    ]).toArray();

    console.log("✅ Claim stats refreshed successfully at", new Date());
  } catch (error) {
    console.error("❌ Error refreshing claim stats:", error);
  }
};
```

### 3. Claims Trend Trigger

**Schedule:** Hourly (`0 * * * *`)

- **Name:** `refresh_claims_trend`
- **Cron Schedule:** `0 * * * *`

**Function Code:**

```javascript
exports = async function() {
  const mongodb = context.services.get("mongodb-atlas");
  const db = mongodb.db("OEMPartner_dealer_portal");

  console.log("Refreshing claims trend...");

  try {
    await db.collection("warrantyClaims").aggregate([
      {
        $group: {
          _id: {
            year: { $year: "$submittedAt" },
            month: { $month: "$submittedAt" }
          },
          claimsCount: { $sum: 1 },
          totalValue: { $sum: "$totals.claimTotal" },
          approvedCount: {
            $sum: { $cond: [{ $in: ["$status", ["Approved", "Paid", "Closed"]] }, 1, 0] }
          },
          rejectedCount: {
            $sum: { $cond: [{ $eq: ["$status", "Rejected"] }, 1, 0] }
          }
        }
      },
      {
        $addFields: {
          period: {
            $dateFromParts: {
              year: "$_id.year",
              month: "$_id.month",
              day: 1
            }
          },
          approvalRate: {
            $cond: [
              { $gt: ["$claimsCount", 0] },
              { $divide: ["$approvedCount", "$claimsCount"] },
              0
            ]
          }
        }
      },
      { $sort: { period: -1 } },
      { $limit: 24 },
      {
        $merge: {
          into: "mv_claims_trend",
          on: "_id",
          whenMatched: "replace",
          whenNotMatched: "insert"
        }
      }
    ]).toArray();

    console.log("✅ Claims trend refreshed successfully at", new Date());
  } catch (error) {
    console.error("❌ Error refreshing claims trend:", error);
  }
};
```

### 4. Dealer Claim Stats Trigger

**Schedule:** Every 30 minutes (`*/30 * * * *`)

- **Name:** `refresh_dealer_claim_stats`
- **Cron Schedule:** `*/30 * * * *`

**Function Code:**

```javascript
exports = async function() {
  const mongodb = context.services.get("mongodb-atlas");
  const db = mongodb.db("OEMPartner_dealer_portal");

  console.log("Refreshing dealer claim stats...");

  try {
    await db.collection("warrantyClaims").aggregate([
      {
        $group: {
          _id: "$dealer.dealerId",
          dealerCode: { $first: "$dealer.dealerCode" },
          dealerName: { $first: "$dealer.name" },
          region: { $first: "$dealer.region" },
          totalClaims: { $sum: 1 },
          totalValue: { $sum: "$totals.claimTotal" },
          approvedClaims: {
            $sum: { $cond: [{ $in: ["$status", ["Approved", "Paid", "Closed"]] }, 1, 0] }
          },
          rejectedClaims: {
            $sum: { $cond: [{ $eq: ["$status", "Rejected"] }, 1, 0] }
          },
          approvedValue: { $sum: "$totals.approvedTotal" }
        }
      },
      {
        $addFields: {
          approvalRate: {
            $cond: [
              { $gt: ["$totalClaims", 0] },
              { $divide: ["$approvedClaims", "$totalClaims"] },
              0
            ]
          },
          computedAt: "$$NOW"
        }
      },
      {
        $merge: {
          into: "mv_dealer_claim_stats",
          on: "_id",
          whenMatched: "replace",
          whenNotMatched: "insert"
        }
      }
    ]).toArray();

    console.log("✅ Dealer claim stats refreshed successfully at", new Date());
  } catch (error) {
    console.error("❌ Error refreshing dealer claim stats:", error);
  }
};
```

## Step 3: Test Triggers

To test a trigger manually before the scheduled time:

1. Go to App Services → Triggers
2. Find your trigger in the list
3. Click "Run" on the right side
4. View the execution logs to verify success

## Step 4: Monitor Trigger Execution

1. Go to App Services → Logs
2. Filter by "Triggers"
3. Monitor for successful executions and errors
4. Set up alerts for failed triggers (optional)

## Refresh Frequency Summary

| View | Refresh Frequency | Cron Expression | Reason |
|------|------------------|-----------------|--------|
| Product Stats | Every 15 min | `*/15 * * * *` | Lightweight, fast aggregation |
| Claim Stats | Every 15 min | `*/15 * * * *` | Dashboard critical data |
| Claims Trend | Hourly | `0 * * * *` | Historical trend, less time-sensitive |
| Dealer Claim Stats | Every 30 min | `*/30 * * * *` | Per-dealer breakdown |

## Alternative: Manual Refresh via API

If you prefer not to use Atlas Triggers, you can refresh views manually via the API:

```bash
# Refresh all views
curl -X POST http://localhost:8000/api/v1/dashboard/refresh \
  -H "Content-Type: application/json" \
  -d '{"views": ["all"]}'

# Refresh specific views
curl -X POST http://localhost:8000/api/v1/dashboard/refresh \
  -H "Content-Type: application/json" \
  -d '{"views": ["product_stats", "claim_stats"]}'
```

You could then set up a cron job or scheduled task on your server to call these endpoints.

## Alternative: Using refresh_materialized_views.py Script

For local development or manual refreshes:

```bash
cd backend

# Refresh all views
python refresh_materialized_views.py --all

# Refresh specific view
python refresh_materialized_views.py --view product_stats
python refresh_materialized_views.py --view claim_stats
python refresh_materialized_views.py --view claims_trend
python refresh_materialized_views.py --view dealer_claim_stats

# Refresh with stats output
python refresh_materialized_views.py --all --stats
```

## Best Practices

1. **Stagger refreshes:** If you have many views, schedule them at different intervals to avoid database load spikes

2. **Monitor execution time:** If a trigger takes too long, consider:
   - Adding indexes to the source collections
   - Reducing the refresh frequency
   - Optimizing the aggregation pipeline

3. **Set up alerts:** Configure Atlas to alert you when triggers fail

4. **Test with sample data first:** Before running on production data, test all triggers with a small dataset

## Troubleshooting

### Trigger Fails with Timeout

- Reduce the amount of data being processed
- Add indexes to improve aggregation performance
- Consider increasing the trigger timeout limit

### Trigger Runs But View is Empty

- Check that the source collection has data
- Verify the `$merge` target collection name matches your database
- Check the trigger logs for errors

### Dashboard Shows Stale Data

- Verify triggers are enabled and running on schedule
- Check trigger execution logs
- Manually trigger a refresh to test
- Verify the materialized view collections exist

## Resources

- [MongoDB Atlas Triggers Documentation](https://www.mongodb.com/docs/atlas/app-services/triggers/)
- [Cron Expression Generator](https://crontab.guru/)
- [Aggregation Pipeline Operators](https://www.mongodb.com/docs/manual/reference/operator/aggregation/)
