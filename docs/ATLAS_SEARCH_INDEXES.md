# Atlas Search Indexes Setup

This document describes the Atlas Search indexes required for the OEMPartner Dealer Portal.

## Overview

The portal uses MongoDB Atlas Search for:
- **Full-text search** with fuzzy matching and autocomplete
- **Faceted search** for filtering with counts
- **Vector search** for semantic/natural language queries (optional)

## Required Indexes

### 1. Products Search Index

**Collection:** `products`  
**Index Name:** `products_search_index`

Create this index in MongoDB Atlas:
1. Go to your cluster → **Search** tab
2. Click **Create Index**
3. Choose **JSON Editor**
4. Select collection: `products`
5. Paste the contents from: `backend/atlas_search_indexes/products_search_index.json`

**Key features:**
- Autocomplete on `name` field
- Keyword search on `partNumber`, `sku`
- Faceting on `category`, `subcategory`, `inventory.status`, `compatibleModels.modelCode`
- Number range on `pricing.msrp`

### 2. Warranty Claims Search Index

**Collection:** `warrantyClaims`  
**Index Name:** `warrantyClaims_search_index`

Create this index in MongoDB Atlas:
1. Go to your cluster → **Search** tab
2. Click **Create Index**
3. Choose **JSON Editor**
4. Select collection: `warrantyClaims`
5. Paste the contents from: `backend/atlas_search_indexes/warrantyClaims_search_index.json`

**Key features:**
- Autocomplete on `claimId`, `customer.name`, `vehicle.registrationNumber`
- Faceting on `status`, `vehicle.modelCode`, `failure.category`, `dealer.region`
- Date filtering on `submittedAt`
- Number range on `totals.claimTotal`
- Boolean filtering on `sla.slaBreached`

## Index Build Time

After creating an index, it takes approximately 1-5 minutes to build depending on data size. You can monitor progress in the Atlas UI.

## Verifying Indexes

Once indexes are built, test them:

```bash
# Test products search (should return results with facets)
curl "http://localhost:8000/api/v1/products/search?limit=5"

# Test claims search
curl "http://localhost:8000/api/v1/claims/search?limit=5"
```

## Index Field Mapping

### Products Index Fields

| Field | Type | Purpose |
|-------|------|---------|
| `name` | string + autocomplete | Text search + typeahead |
| `partNumber` | keyword | Exact part number lookup |
| `sku` | keyword | Exact SKU lookup |
| `description` | string | Full-text search |
| `category` | token | Facet filtering |
| `subcategory` | token | Facet filtering |
| `inventory.status` | token | Availability filter |
| `pricing.msrp` | number | Price range filter |
| `compatibleModels.modelCode` | token | Model compatibility filter |

### Claims Index Fields

| Field | Type | Purpose |
|-------|------|---------|
| `claimId` | keyword + autocomplete | Claim ID lookup + typeahead |
| `customer.name` | string + autocomplete | Customer search + typeahead |
| `vehicle.registrationNumber` | keyword + autocomplete | Vehicle lookup |
| `status` | token | Status facet filtering |
| `failure.category` | token | Failure type filtering |
| `dealer.region` | token | Region filtering |
| `totals.claimTotal` | number | Amount range filter |
| `sla.slaBreached` | boolean | SLA status filter |
| `submittedAt` | date | Date range filter |

## Troubleshooting

### "Index not found" error
- Verify the index name matches config: `products_search_index`, `warrantyClaims_search_index`
- Wait for index to finish building

### "facet.operator must be present" error
- This means the search is using facets but no valid operator was provided
- Check that the query builder returns an `exists` operator when no search criteria

### Slow search queries
- Check index build status in Atlas
- Consider adding more specific field mappings
- Reduce `numBuckets` in facet definitions

## Optional: Vector Search Indexes

For semantic/natural language search, you'll also need vector indexes. See `docs/VECTOR_SEARCH_SETUP.md` for details.

