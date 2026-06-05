# OEM Partner Dealer Portal - Frontend (SvelteKit)

Modern, responsive frontend for the Manufacturing Group Manufacturing OEMPartner Dealer Portal using SvelteKit and Tailwind CSS.

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
# Create .env file with API URL
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env
```

### 3. Run Development Server

```bash
npm run dev
```

Visit: http://localhost:5173

## Tech Stack

- **SvelteKit 2.0+** - Full-stack framework
- **Tailwind CSS 3.4+** - Utility-first styling
- **TypeScript** - Type safety
- **Axios** - HTTP client

## Project Structure

```
frontend/
├── src/
│   ├── routes/
│   │   ├── +layout.svelte        # Main layout (OEMPartner branding)
│   │   ├── +page.svelte          # Dashboard home
│   │   ├── products/
│   │   │   ├── +page.svelte      # Products search
│   │   │   └── [partNumber]/+page.svelte  # Product detail
│   │   └── claims/
│   │       ├── +page.svelte      # Claims search
│   │       └── [claimId]/+page.svelte     # Claim detail
│   ├── lib/
│   │   ├── api.ts                # API client & types
│   │   └── components/           # Reusable components
│   └── app.css                   # Global styles & OEMPartner colors
├── tailwind.config.js            # OEMPartner color palette
└── package.json
```

## Features

### Products Page (`/products`)
- Full-text search with autocomplete
- Faceted filtering (category, subcategory, model, availability, price)
- Product card grid with inventory status
- Vector/semantic search option

### Product Detail Page (`/products/[partNumber]`)
- Complete product information
- Compatible models list
- Warehouse inventory breakdown
- Pricing (MSRP and dealer price)
- Supersession information
- Related products

### Claims Page (`/claims`)
- Search warranty claims
- Filter by status, date, model, failure category
- Status badges and SLA indicators
- Quick claim summaries

### Claim Detail Page (`/claims/[claimId]`)
- Full claim information
- Vehicle and customer details
- Parts and labour claimed
- Status history timeline
- Review and payment information
- SLA tracking

### Dashboard (`/`)
- Product statistics
- Claim statistics
- Low stock alerts
- Recent activity

## OEM Partner Branding

### Colors (Tailwind Config)

```javascript
colors: {
  OEMPartner: {
    blue: '#0033A0',      // Primary
    red: '#E60012',       // Accent
    darkblue: '#002266',  // Hover states
    lightblue: '#E8F1FF', // Backgrounds
    gray: '#F5F7FA'       // Subtle backgrounds
  }
}
```

### CSS Classes

```css
/* OEMPartner-branded buttons */
.btn-OEMPartner-primary  /* Blue button */
.btn-OEMPartner-outline  /* Blue outline button */

/* Status badges */
.status-draft, .status-pending, .status-review
.status-approved, .status-rejected, .status-paid

/* Inventory status */
.inventory-in-stock, .inventory-low-stock, .inventory-out-of-stock
```

## API Integration

The frontend connects to the FastAPI backend at `VITE_API_URL`.

### Key API Calls

```typescript
// Products
searchProducts(params)           // GET /products/search
vectorSearchProducts(query)      // POST /products/search/semantic
getProductByPartNumber(pn)       // GET /products/{partNumber}

// Claims
searchClaims(params)             // GET /claims/search
getClaimById(id)                 // GET /claims/{claimId}

// Dashboard
getProductDashboardStats()       // GET /dashboard/products/stats
getClaimDashboardStats()         // GET /dashboard/claims/stats
```

## Building for Production

```bash
npm run build
npm run preview
```

## Deployment

### Vercel (Recommended)

```bash
npm install -g vercel
vercel
```

### Other Platforms

- Netlify
- Railway
- AWS Amplify
- Cloudflare Pages

## Malaysian Locale

- **Currency:** MYR (Malaysian Ringgit) - formatted as `RM X,XXX.XX`
- **Date Format:** DD/MM/YYYY
- **Phone Format:** +60XX-XXXXXXX

## Resources

- [SvelteKit Documentation](https://kit.svelte.dev/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
