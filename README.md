<!-- Portfolio repository -->

> **Manufacturing Dealer Portal** — portfolio demonstration.
> Product and warranty search with Atlas Search and vector retrieval
>
> This is a sanitized public version of a real-world prototype. Client names,
> credentials, internal endpoints, and proprietary assets have been removed; all
> configuration is environment-driven (`.env.example`). Authored by
> [Paul Cleenewerck](https://github.com/pcleene).

---

# OEM Partner Dealer Portal

**Manufacturing Group Malaysia - OEMPartner Division**

---

## Overview

The OEMPartner Dealer Portal is a modern enterprise application designed to streamline dealer operations across Malaysia. Built on MongoDB Atlas, it provides powerful search capabilities, real-time analytics, and efficient warranty claims management for the OEMPartner motorcycle dealer network.

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **Product Catalog** | Search 10,000+ parts with fuzzy matching, autocomplete, and filtering |
| **Warranty Claims** | Submit, track, and manage warranty claims through a complete workflow |
| **Smart Search** | Natural language queries powered by AI vector search |
| **Real-Time Analytics** | Dashboard with instant insights via pre-computed materialized views |

---

## Technology Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│         SvelteKit 2.0  •  Tailwind CSS  •  Axios                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      REST API LAYER                              │
│            FastAPI  •  Python 3.12  •  Async/Await              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     MONGODB ATLAS                                │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐     │
│   │ Atlas Search│  │Vector Search│  │ Aggregation Pipelines│     │
│   │ • Fuzzy     │  │ • Voyage AI │  │ • Materialized Views │     │
│   │ • Facets    │  │ • Semantic  │  │ • Real-time Stats    │     │
│   └─────────────┘  └─────────────┘  └─────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

| Layer | Technologies |
|-------|--------------|
| **Frontend** | SvelteKit 2.0, Tailwind CSS 3.4, TypeScript |
| **Backend** | Python 3.12, FastAPI, Pydantic v2, PyMongo |
| **Database** | MongoDB Atlas, Atlas Search, Atlas Vector Search |
| **AI/ML** | Voyage AI embeddings for semantic search |

---

## Features

### Product Catalog Search

- **Full-Text Search** - Find products by name, part number, or description with typo tolerance
- **Autocomplete** - Instant suggestions as you type
- **Faceted Filtering** - Filter by category, subcategory, model series, price range, and availability
- **Smart Relevance** - Part number matches are prioritized over description matches

### Warranty Claims Management

- **Complete Workflow** - Draft → Pending Review → Under Review → Approved/Rejected → Paid → Closed
- **Multi-Field Search** - Search by claim ID, customer name, or vehicle registration
- **Status Tracking** - Filter claims by status, date range, vehicle model, and amount
- **SLA Monitoring** - Track processing times and compliance

### AI-Powered Semantic Search

- **Natural Language Queries** - Search using everyday language
- **Contextual Understanding** - Finds relevant results even without exact keywords
- **Example Queries:**
  - "protection from rain for riding" → Rain covers, waterproof gear
  - "parts for long distance touring" → Comfort seats, luggage systems
  - "engine problems with overheating" → Radiator parts, coolant, thermostats

### Dashboard & Analytics

- **Instant Load Times** - Pre-computed views load in under 30ms
- **Product Statistics** - Inventory counts, category breakdown, stock alerts
- **Claims Analytics** - Status distribution, approval rates, processing times
- **Trend Analysis** - Monthly claim trends and regional performance

---

## Project Structure

```
OEMPartner-dealer-portal/
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/        # REST API endpoints
│   │   ├── services/             # Business logic layer
│   │   ├── search/               # Search utilities
│   │   ├── models/               # Data models (Pydantic)
│   │   └── aggregations/         # Materialized view definitions
│   ├── atlas_search_indexes/     # MongoDB Atlas Search index configs
│   ├── generate_sample_data.py   # Sample data generator
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── routes/               # SvelteKit pages
│   │   └── lib/                  # Components & API client
│   └── package.json
└── docs/
    ├── ATLAS_SEARCH_INDEXES.md   # Search index setup guide
    ├── ATLAS_TRIGGERS_SETUP.md   # Scheduled refresh configuration
    ├── DEMO_GUIDE.md             # Demo walkthrough
    └── SESSION_HANDOFF.md        # Development notes
```

---

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Node.js 20 or higher
- MongoDB Atlas account with a configured cluster

### Installation

#### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your MongoDB Atlas connection string
```

#### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

#### 3. Configure MongoDB Atlas Search

Create search indexes in your Atlas cluster:

1. Navigate to your cluster → **Atlas Search** tab
2. Create index for `products` using `backend/atlas_search_indexes/products_search_index.json`
3. Create index for `warrantyClaims` using `backend/atlas_search_indexes/warrantyClaims_search_index.json`

See [docs/ATLAS_SEARCH_INDEXES.md](docs/ATLAS_SEARCH_INDEXES.md) for detailed instructions.

#### 4. Sample Data & Materialized Views

The application includes a sample data generator for demonstration purposes. After generating data, you must refresh the materialized views to populate the dashboard statistics.

**Generate sample data:**
```bash
cd backend
python generate_sample_data.py --products 100 --claims 200 --dealers 15
```

**Refresh materialized views** (required after data generation):
```bash
python refresh_materialized_views.py --all --stats
```

The materialized views pre-compute dashboard statistics for faster query performance. Available refresh options:
- `--all` - Refresh all views
- `--view product_stats` - Product catalog statistics only
- `--view claim_stats` - Claim statistics only
- `--view claims_trend` - Monthly trend data only

> **Note:** In this POC, materialized views are refreshed manually or via scheduled Atlas Triggers. For production deployments, automatic refresh using [Change Streams](https://www.mongodb.com/docs/manual/changeStreams/) or [Atlas Stream Processing](https://www.mongodb.com/docs/atlas/atlas-stream-processing/overview/) would provide real-time updates—this was not implemented for the demo.

### Running the Application

**Start the backend:**
```bash
cd backend
source venv/bin/activate
python -m app.main
```
Backend API: http://localhost:8000

**Start the frontend:**
```bash
cd frontend
npm run dev
```
Frontend: http://localhost:5173

**API Documentation:** http://localhost:8000/api/docs

---

## API Reference

### Products API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/products/search` | GET | Full-text search with faceted filtering |
| `/api/v1/products/search/semantic` | POST | AI-powered semantic search |
| `/api/v1/products/autocomplete` | GET | Real-time autocomplete suggestions |
| `/api/v1/products/categories` | GET | List all product categories |
| `/api/v1/products/low-stock` | GET | Products with low inventory |
| `/api/v1/products/{partNumber}` | GET | Product details |

### Claims API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/claims/search` | GET | Full-text search with faceted filtering |
| `/api/v1/claims/search/semantic` | POST | AI-powered semantic search |
| `/api/v1/claims/by-dealer/{dealerId}` | GET | Claims for a specific dealer |
| `/api/v1/claims/statistics` | GET | Aggregate claim statistics |
| `/api/v1/claims/{claimId}` | GET | Claim details |

### Dashboard API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/dashboard/products/stats` | GET | Product catalog statistics |
| `/api/v1/dashboard/claims/stats` | GET | Claim processing statistics |
| `/api/v1/dashboard/claims/trend` | GET | Monthly claims trend data |

---

## Performance

| Operation | Response Time |
|-----------|---------------|
| Text Search | 50-100ms |
| Faceted Search | 80-120ms |
| Vector Search | 150-300ms |
| Dashboard Load | 10-30ms |

*Performance measured with 10,000+ products and claims*

---

## Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory by copying `.env.example`:

```bash
cp .env.example .env
```

Then update the following **required** placeholder values:

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGODB_URL` | Your MongoDB Atlas connection string | Yes |
| `VOYAGE_API_KEY` | Your Voyage AI API key (for semantic search) | Yes* |

*Voyage AI key is only required if using the semantic/vector search feature.

**Example `.env` configuration:**
```bash
# MongoDB Atlas Connection (REQUIRED - replace with your connection string)
MONGODB_URL=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/
MONGODB_DB_NAME=OEMPartner_dealer_portal

# Voyage AI (REQUIRED for semantic search - get key from https://www.voyageai.com/)
VOYAGE_API_KEY=<your-voyage-api-key>
VOYAGE_MODEL=voyage-large-2

# Application
DEBUG=false
```

> **Important:** The repository contains only `.env.example` with placeholder values. You must create your own `.env` file and insert your actual MongoDB Atlas URI and Voyage AI API key. Never commit `.env` files containing real credentials.

---

## Malaysian Localization

The application is configured for the Malaysian market:

| Setting | Value |
|---------|-------|
| Currency | MYR (Malaysian Ringgit) |
| Date Format | DD/MM/YYYY |
| Phone Format | +60XX-XXXXXXX |
| Regions | All 16 Malaysian states and territories |

---

## Branding

| Element | Color Code | Usage |
|---------|------------|-------|
| OEMPartner Blue | `#0033A0` | Primary actions, headers |
| OEMPartner Red | `#E60012` | Accent, alerts |
| Dark Blue | `#002266` | Hover states |
| Light Blue | `#E8F1FF` | Backgrounds |

---

## Documentation

| Document | Purpose |
|----------|---------|
| [Atlas Search Indexes](docs/ATLAS_SEARCH_INDEXES.md) | Search index configuration guide |
| [Atlas Triggers Setup](docs/ATLAS_TRIGGERS_SETUP.md) | Scheduled refresh for materialized views |
| [Demo Guide](docs/DEMO_GUIDE.md) | Step-by-step demonstration walkthrough |

---

## Support

For technical support or questions about this application, please contact the development team.

---

**Manufacturing Group Malaysia - OEMPartner Division**
*Powered by MongoDB Atlas*
