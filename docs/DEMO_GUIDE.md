# OEM Partner Dealer Portal - MongoDB Demo Guide

Manufacturing Group Malaysia
A demonstration of MongoDB Atlas capabilities for enterprise applications

---

## What This Demo Shows

This dealer portal demonstrates how MongoDB Atlas powers a modern enterprise application:

• Atlas Search - Lightning-fast product and warranty claim searches
• Vector Search - Natural language queries ("find parts for rainy weather")
• Faceted Search - Filter results by category, status, price range
• Aggregation Pipelines - Real-time analytics and reporting
• Materialized Views - Pre-computed dashboards for instant insights

---

## 1. Atlas Search - Smart Text Search

THE CHALLENGE:
Dealers need to find products quickly using partial names, part numbers, or descriptions - even with typos.

THE SOLUTION:
Atlas Search provides Google-like search with fuzzy matching, autocomplete, and relevance scoring.

EXAMPLE - Product Search for "brake pad Y15":

    db.products.aggregate([
      {
        "$search": {
          "index": "products_search_index",
          "compound": {
            "should": [
              {
                "text": {
                  "query": "brake pad Y15",
                  "path": ["name", "description"],
                  "fuzzy": {"maxEdits": 1}
                }
              },
              {
                "text": {
                  "query": "brake pad Y15",
                  "path": "partNumber",
                  "score": {"boost": {"value": 3}}
                }
              }
            ]
          }
        }
      },
      {"$limit": 20}
    ])

KEY FEATURES:

• Fuzzy Matching - Finds "brake" even if user types "brak"
• Multi-field Search - Searches name, description, and part number simultaneously
• Relevance Boosting - Part number matches rank higher than description matches
• Real-time Results - Sub-100ms response times on 10,000+ products

---

## 2. Faceted Search - Filter and Refine

THE CHALLENGE:
Users want to narrow down results by category, price, availability, and compatible vehicle models.

THE SOLUTION:
Atlas Search Facets compute filter options and counts in a single query - no separate database calls needed.

WHAT USERS SEE:

    Category                  Availability          Price Range
    ☐ Filters (245)          ☐ In Stock (1,842)    ☐ Under RM50 (456)
    ☐ Brake System (189)     ☐ Low Stock (234)     ☐ RM50-100 (892)  
    ☐ Engine Parts (567)     ☐ Out of Stock (89)   ☐ RM100-500 (743)
    ☐ Electrical (342)                             ☐ Over RM500 (234)

EXAMPLE - Faceted Search Query:

    db.products.aggregate([
      {
        "$searchMeta": {
          "index": "products_search_index",
          "facet": {
            "facets": {
              "categoryFacet": {
                "type": "string",
                "path": "category"
              },
              "availabilityFacet": {
                "type": "string", 
                "path": "inventory.status"
              },
              "priceFacet": {
                "type": "number",
                "path": "pricing.msrp",
                "boundaries": [0, 50, 100, 500, 1000, 5000]
              }
            }
          }
        }
      }
    ])

BUSINESS VALUE:
Users can explore and refine results without waiting for separate filter queries.

---

## 3. Vector Search - Natural Language Queries

THE CHALLENGE:
Traditional keyword search fails when users don't know exact product names. How do you search for "something to protect me from rain while riding"?

THE SOLUTION:
Vector Search with Voyage AI embeddings understands the meaning behind queries, not just keywords.

HOW IT WORKS:

    User types: "protection from rain for riding"
                        ↓
            Voyage AI creates embedding
                        ↓
            1024-dimensional vector
                        ↓
            MongoDB finds similar vectors
                        ↓
    Results: Rain covers, waterproof bags, 
             riding jackets, helmet visors...

EXAMPLE - Vector Search Query:

    db.products.aggregate([
      {
        "$vectorSearch": {
          "index": "products_vector_index",
          "path": "embedding",
          "queryVector": [0.023, -0.156, 0.089, ... 1024 numbers],
          "numCandidates": 100,
          "limit": 20
        }
      },
      {
        "$addFields": {
          "relevanceScore": {"$meta": "vectorSearchScore"}
        }
      }
    ])

REAL EXAMPLES THAT WORK:

• "protection from rain for riding" → Rain covers, waterproof gear, windshields
• "parts for long distance touring" → Comfort seats, luggage systems, highway pegs
• "engine problems with overheating" → Radiator parts, coolant, thermostats, fans
• "electrical issues after flooding" → Warranty claims with water damage symptoms

BUSINESS VALUE:
Dealers find what they need even when they can't describe it technically.

---

## 4. Aggregation Pipelines - Real-Time Analytics

THE CHALLENGE:
Management needs instant insights: claim values, approval rates, processing times, regional performance.

THE SOLUTION:
MongoDB Aggregation Pipelines transform raw data into actionable insights in real-time.

EXAMPLE - Claims by Status with Values:

    db.warrantyClaims.aggregate([
      {
        "$group": {
          "_id": "$status",
          "count": {"$sum": 1},
          "totalValue": {"$sum": "$totals.claimTotal"},
          "avgValue": {"$avg": "$totals.claimTotal"}
        }
      },
      {"$sort": {"count": -1}}
    ])

RESULT:

    Status          Count    Total Value      Avg Value
    Approved        4,521    RM 2,845,670     RM 629
    Pending Review  1,234    RM 756,890       RM 613
    Under Review      892    RM 534,200       RM 599
    Rejected          456    RM 267,800       RM 587
    Paid            3,897    RM 2,456,780     RM 630

EXAMPLE - Monthly Claims Trend:

    db.warrantyClaims.aggregate([
      {
        "$match": {
          "submittedAt": {"$gte": new Date("2024-01-01")}
        }
      },
      {
        "$group": {
          "_id": {
            "year": {"$year": "$submittedAt"},
            "month": {"$month": "$submittedAt"}
          },
          "claimsCount": {"$sum": 1},
          "totalValue": {"$sum": "$totals.claimTotal"}
        }
      },
      {"$sort": {"_id": 1}}
    ])

---

## 5. Materialized Views - Instant Dashboards

THE CHALLENGE:
Complex analytics queries can take seconds. Dashboards need instant responses.

THE SOLUTION:
Materialized Views pre-compute expensive aggregations on a schedule, storing results in dedicated collections.

ARCHITECTURE:

    Raw Collections                Materialized Views (Pre-computed)
    
    products (10,000+ docs)   →    mv_product_stats (refreshed every 15 min)
    
    warrantyClaims            →    mv_claim_stats
    (10,000+ docs)            →    mv_dealer_claim_stats  
                              →    mv_claims_trend (refreshed hourly)

EXAMPLE - Creating a Materialized View:

    db.products.aggregate([
      {
        "$facet": {
          "totalProducts": [{"$count": "count"}],
          "byCategory": [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
          ],
          "inventoryValue": [
            {
              "$group": {
                "_id": null,
                "totalValue": {
                  "$sum": {
                    "$multiply": ["$pricing.dealerPrice", "$inventory.totalQuantity"]
                  }
                }
              }
            }
          ]
        }
      },
      {
        "$merge": {
          "into": "mv_product_stats",
          "whenMatched": "replace"
        }
      }
    ])

DASHBOARD QUERY (Instant!):

    // Loads in <10ms instead of 2-3 seconds
    db.mv_product_stats.findOne({})
    
    // Returns pre-computed data:
    {
        "totalProducts": 2165,
        "byCategory": [
            {"_id": "Engine Parts", "count": 567},
            {"_id": "Electrical", "count": 342}
        ],
        "inventoryValue": {"totalValue": 4567890.00},
        "refreshedAt": "2024-12-10T09:15:00Z"
    }

MATERIALIZED VIEWS IN THIS SYSTEM:

• mv_product_stats - Product counts, categories, inventory value (every 15 min)
• mv_claim_stats - Claim counts by status, values, approval rates (every 15 min)
• mv_dealer_claim_stats - Per-dealer performance metrics (every 15 min)
• mv_claims_trend - Monthly claim trends for charts (hourly)

BUSINESS VALUE:
Executive dashboards load instantly, even with millions of records.

---

## Demo Walkthrough

SCENE 1: Product Search
1. Open Products page
2. Type "brake" → See fuzzy matching in action
3. Click "Show Query" button → View the MongoDB pipeline
4. Apply filters → Watch facet counts update

SCENE 2: Semantic Search  
1. Toggle to "Semantic Search" mode
2. Type: "protection from rain for riding"
3. Click "Show Query" → See vector search pipeline
4. Note: Results are contextually relevant, not just keyword matches

SCENE 3: Claims Search
1. Open Claims page
2. Search: "engine problems"
3. Filter by status → See combined search + filters
4. Toggle semantic → Try "electrical issues after flooding"

SCENE 4: Dashboard Analytics
1. Return to Home/Dashboard
2. Point out instant load times
3. Explain these are materialized views
4. Show variety of aggregations: charts, top dealers, trends

SCENE 5: The Query Button
1. On any search page, click "{ } Query" button
2. Show the actual MongoDB pipeline
3. Highlight: "This is production code, not a demo trick"

---

## Performance Metrics

• Text Search: ~50-100ms (10,000+ products)
• Vector Search: ~150-300ms (includes AI embedding generation)
• Faceted Search: ~80-120ms (with facet computation)
• Dashboard Load: ~10-30ms (from materialized views)
• Full Aggregation: ~2-3 seconds (raw computation - avoided via materialized views)

---

## MongoDB Features Used

ATLAS SEARCH
• Fuzzy text matching
• Faceted search
• Autocomplete
• Relevance scoring

VECTOR SEARCH
• Semantic understanding
• Voyage AI embeddings
• 1024-dimensional vectors
• Similarity scoring

AGGREGATION FRAMEWORK
• $group, $match, $sort
• $facet (multiple pipelines)
• $merge (write results)
• $project (shape output)

MATERIALIZED VIEWS
• Pre-computed aggregations
• Scheduled refresh via Atlas Triggers
• Instant dashboard queries

---

## Key Takeaways

1. SINGLE PLATFORM
   All features (search, vectors, analytics) in MongoDB - no external search engines needed

2. DEVELOPER FRIENDLY
   Python/JavaScript aggregation pipelines are readable and maintainable

3. SCALE READY
   Same queries work whether you have 1,000 or 10,000,000 documents

4. REAL-TIME + PRE-COMPUTED
   Balance between fresh data and instant dashboards

5. AI-READY
   Vector search enables natural language interfaces without custom ML infrastructure

---

## Quick Reference URLs

• Dashboard: http://localhost:5173/
• Products Search: http://localhost:5173/products
• Claims Search: http://localhost:5173/claims
• API Documentation: http://localhost:8001/api/docs

---

Demo Version 1.0 - December 2024
Built with MongoDB Atlas, FastAPI, and SvelteKit
