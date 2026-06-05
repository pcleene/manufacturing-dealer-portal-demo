/**
 * API client for OEMPartner Dealer Portal Backend
 * Manufacturing Group Malaysia
 */
import axios, { type AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1';

// Custom params serializer for FastAPI compatibility
// FastAPI expects array params as repeated keys: category=A&category=B
function serializeParams(params: Record<string, any>): string {
	const parts: string[] = [];
	
	for (const [key, value] of Object.entries(params)) {
		if (value === undefined || value === null) continue;
		
		if (Array.isArray(value)) {
			// Serialize arrays as repeated keys for FastAPI
			for (const item of value) {
				parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(item)}`);
			}
		} else {
			parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
		}
	}
	
	return parts.join('&');
}

// Create axios instance
const apiClient: AxiosInstance = axios.create({
	baseURL: API_BASE_URL,
	headers: {
		'Content-Type': 'application/json'
	},
	timeout: 30000, // 30 seconds
	paramsSerializer: serializeParams
});

// ============================================================================
// TYPES - Products
// ============================================================================

export interface CompatibleModel {
	modelCode: string;
	modelName: string;
	yearStart: number;
	yearEnd: number;
	notes?: string;
}

export interface Pricing {
	msrp: number;
	dealerPrice: number;
	cost: number;
	currency: string;
	lastPriceUpdate: string;
}

export interface Warehouse {
	code: string;
	name: string;
	quantity: number;
	lastRestocked: string;
}

export interface Inventory {
	totalQuantity: number;
	reorderPoint: number;
	status: 'In Stock' | 'Low Stock' | 'Out of Stock';
	warehouses: Warehouse[];
	lastStockCheck: string;
}

// NEW: Technical Documentation
export interface TechnicalDoc {
	docId: string;
	title: string;
	docType: 'Installation' | 'Repair' | 'Maintenance' | 'Safety' | 'Technical Bulletin';
	language: string;
	version: string;
	pageCount: number;
	lastUpdated: string;
	fileSize: string;
	applicableModels: string[];
	summary: string;
	downloadUrl: string;
}

// NEW: Manufacturing Info
export interface Manufacturing {
	countryOfOrigin: string;
	manufacturerCode: string;
	manufacturerName: string;
	plantCode: string;
	qualityCertifications: string[];
	leadTimeDays: number;
	minOrderQuantity: number;
}

// NEW: Specifications with nested dimensions
export interface Dimensions {
	length: string;
	width: string;
	height: string;
}

export interface Specifications {
	weight?: string;
	material?: string;
	dimensions?: Dimensions;
	color?: string;
	finishType?: string;
	operatingTemp?: string;
	warrantyMonths?: number;
	voltage?: string;
	waterproofRating?: string;
	brakeType?: string;
	viscosity?: string;
	volume?: string;
	[key: string]: string | number | Dimensions | undefined;
}

// NEW: Fitment Notes
export interface FitmentNotes {
	difficultyLevel: 'Easy' | 'Intermediate' | 'Advanced' | 'Professional';
	estimatedInstallTime: string;
	toolsRequired: string[];
	specialInstructions: string;
	professionalInstallRecommended: boolean;
}

// NEW: Cross-sell
export interface CrossSell {
	frequentlyBoughtTogether: string[];
	accessories: string[];
	alternativeProducts: string[];
}

// NEW: Sales Data
export interface SalesData {
	totalUnitsSold: number;
	avgRating: number | null;
	reviewCount: number;
	returnRate: number;
	topSellingRegions: string[];
}

// NEW: Packaging Info
export interface Packaging {
	packageWeight: string;
	packageDimensions: string;
	unitsPerCarton: number;
	cartonBarcode: string;
	hazmatClass: string | null;
}

export interface Product {
	partNumber: string;
	sku: string;
	name: string;
	description: string;
	category: string;
	subcategory: string;
	brand: string;
	compatibleModels: CompatibleModel[];
	pricing: Pricing;
	inventory: Inventory;
	specifications?: Specifications;
	// NEW: Enriched product fields
	technicalDocs?: TechnicalDoc[];
	manufacturing?: Manufacturing;
	fitmentNotes?: FitmentNotes;
	crossSell?: CrossSell;
	salesData?: SalesData;
	packaging?: Packaging;
	supersession?: {
		supersededBy?: string;
		supersedes?: string;
	};
	relatedProducts: string[];
	images: Array<{
		url: string;
		altText: string;
		isPrimary: boolean;
	}>;
	createdAt: string;
	updatedAt: string;
	// Vector search score (only present in semantic search results)
	vectorScore?: number;
}

export interface ProductSearchFilters {
	category?: string[];
	subcategory?: string[];
	model_series?: string[];
	model_year?: number[];
	availability_status?: string[];
	min_price?: number;
	max_price?: number;
	warehouse_region?: string[];
}

// ============================================================================
// TYPES - Warranty Claims
// ============================================================================

export interface StatusHistoryEntry {
	status: string;
	changedAt: string;
	changedBy: string;
	notes?: string;
}

export interface DealerInfo {
	dealerId: string;
	dealerCode: string;
	name: string;
	region: string;
}

export interface VehicleInfo {
	modelCode: string;
	modelName: string;
	registrationNumber: string;
	engineNumber: string;
	frameNumber: string;
	purchaseDate: string;
	mileageAtClaim: number;
	warrantyStartDate: string;
	warrantyEndDate: string;
}

export interface CustomerInfo {
	name: string;
	phone: string;
	email: string;
	address: string;
}

export interface FailureDetails {
	category: string;
	description: string;
	dateReported: string;
	technicianNotes?: string;
}

export interface PartClaimed {
	partNumber: string;
	partName: string;
	quantity: number;
	unitPrice: number;
	totalPrice: number;
	warrantyApproved: boolean;
}

export interface LabourClaimed {
	operationCode: string;
	description: string;
	hours: number;
	rate: number;
	totalPrice: number;
	warrantyApproved: boolean;
}

export interface ClaimTotals {
	partsTotal: number;
	labourTotal: number;
	claimTotal: number;
	approvedParts: number;
	approvedLabour: number;
	approvedTotal: number;
}

export interface ReviewInfo {
	reviewedBy: string;
	reviewedAt: string;
	decision: string;
	rejectionReason?: string;
	comments?: string;
}

export interface PaymentInfo {
	paymentDate: string;
	paymentAmount: number;
	paymentReference: string;
	paymentMethod: string;
}

export interface SLAInfo {
	targetDays: number;
	submittedAt: string;
	dueDate: string;
	slaBreached: boolean;
	daysElapsed: number;
}

export interface WarrantyClaim {
	claimId: string;
	status: string;
	statusHistory: StatusHistoryEntry[];
	dealer: DealerInfo;
	vehicle: VehicleInfo;
	customer: CustomerInfo;
	failure: FailureDetails;
	partsClaimed: PartClaimed[];
	labourClaimed: LabourClaimed[];
	totals: ClaimTotals;
	supportingDocuments: Array<{
		documentId: string;
		documentType: string;
		fileName: string;
		uploadedAt: string;
		uploadedBy: string;
	}>;
	review?: ReviewInfo;
	payment?: PaymentInfo;
	sla: SLAInfo;
	submittedAt: string;
	createdAt: string;
	updatedAt: string;
	// Vector search score (only present in semantic search results)
	vectorScore?: number;
}

export interface ClaimSearchFilters {
	status?: string[];
	date_from?: string;
	date_to?: string;
	vehicle_model?: string[];
	claim_type?: string[];
	failure_category?: string[];
	min_amount?: number;
	max_amount?: number;
	dealer_id?: string;
}

// ============================================================================
// TYPES - Common
// ============================================================================

export interface PaginationParams {
	limit?: number;
	cursor?: string;
}

export interface SearchResponse<T> {
	results: T[];
	totalCount?: number;
	pagination: {
		limit: number;
		cursor: string | null;
		hasMore: boolean;
		totalCount?: number;
	};
	facets?: Array<{
		field: string;      // Display label (e.g., "Category")
		fieldKey: string;   // Filter key for API (e.g., "category")
		buckets: Array<{
			value: string;
			count: number;
		}>;
	}>;
	debugQuery?: string;  // MongoDB query in Python format (when includeQuery=true)
}

export interface ProductDashboardStats {
	totalProducts: number;
	byCategory: Array<{ _id: string; count: number }>;
	byAvailabilityStatus: Array<{ _id: string; count: number }>;
	lowStockAlerts: number;
	outOfStock: number;
	newThisQuarter: number;
	inventoryValue?: {
		totalValue: number;
		avgUnitPrice: number;
		totalUnits: number;
	};
	refreshedAt?: string;
}

export interface ClaimDashboardStats {
	totalClaims: number;
	byStatus: Array<{ _id: string; count: number }>;
	byFailureCategory: Array<{ _id: string; count: number }>;
	byVehicleModel: Array<{ _id: string; count: number }>;
	byDealerRegion?: Array<{ _id: string; count: number; totalValue: number }>;
	thisMonth?: {
		count: number;
		totalValue: number;
	};
	processing?: {
		avgProcessingDays: number;
		maxProcessingDays: number;
		minProcessingDays: number;
	};
	values?: {
		totalClaimValue: number;
		totalApprovedValue: number;
		avgClaimValue: number;
	};
	rejection?: {
		rejectionRate: number;
	};
	slaBreached: number;
	refreshedAt?: string;
}

export interface DealerClaimStats {
	_id: string;
	dealerName: string;
	dealerRegion: string;
	totalClaims: number;
	totalClaimValue: number;
	totalApprovedValue: number;
	avgClaimValue: number;
	approvalRate: number;
	slaBreachedCount: number;
	refreshedAt?: string;
}

export interface ClaimsTrend {
	month: string;
	totalClaims: number;
	totalClaimValue: number;
	approvedCount: number;
	rejectedCount: number;
	approvalRate: number;
}

// ============================================================================
// PRODUCT API ENDPOINTS
// ============================================================================

export type SearchMode = 'standard' | 'semantic';

/**
 * Search products with text and filters (standard keyword search)
 */
export async function searchProducts(
	searchText?: string,
	filters?: ProductSearchFilters,
	pagination?: PaginationParams,
	includeQuery: boolean = false
): Promise<SearchResponse<Product>> {
	const response = await apiClient.get('/products/search', {
		params: {
			search_text: searchText,
			...filters,
			limit: pagination?.limit || 20,
			cursor: pagination?.cursor,
			includeQuery
		}
	});
	return response.data;
}

/**
 * Vector search products (semantic search using Voyage AI)
 */
export async function vectorSearchProducts(
	searchText: string,
	filters?: ProductSearchFilters,
	pagination?: PaginationParams,
	includeQuery: boolean = false
): Promise<SearchResponse<Product>> {
	const response = await apiClient.post('/products/search/semantic', {
		query: searchText,
		filters,
		limit: pagination?.limit || 20,
		num_candidates: 100,
		includeQuery
	});
	return response.data;
}

/**
 * Unified product search - switches between standard and semantic based on mode
 */
export async function searchProductsUnified(
	searchText: string | undefined,
	filters: ProductSearchFilters | undefined,
	pagination: PaginationParams | undefined,
	mode: SearchMode,
	includeQuery: boolean = false
): Promise<SearchResponse<Product>> {
	if (mode === 'semantic' && searchText && searchText.trim().length > 0) {
		return vectorSearchProducts(searchText, filters, pagination, includeQuery);
	}
	return searchProducts(searchText, filters, pagination, includeQuery);
}

/**
 * Get product by part number
 */
export async function getProductByPartNumber(partNumber: string): Promise<Product> {
	const response = await apiClient.get(`/products/${partNumber}`);
	return response.data.product;
}

/**
 * Get related products
 */
export async function getRelatedProducts(partNumber: string): Promise<Product[]> {
	const response = await apiClient.get(`/products/${partNumber}/related`);
	return response.data.relatedProducts;
}

/**
 * Get products by model
 */
export async function getProductsByModel(modelCode: string, limit?: number): Promise<Product[]> {
	const response = await apiClient.get(`/products/by-model/${modelCode}`, {
		params: { limit }
	});
	return response.data.products;
}

/**
 * Autocomplete products
 */
export async function autocompleteProducts(
	query: string,
	field: string = 'name',
	limit: number = 10
): Promise<Array<{ partNumber: string; name: string; category: string }>> {
	const response = await apiClient.get('/products/autocomplete', {
		params: { q: query, field, limit }
	});
	return response.data.suggestions;
}

/**
 * Get low stock products
 */
export async function getLowStockProducts(limit?: number): Promise<Product[]> {
	const response = await apiClient.get('/products/low-stock', {
		params: { limit }
	});
	return response.data.products;
}

/**
 * Get product categories
 */
export async function getProductCategories(): Promise<
	Array<{ category: string; subcategories: string[]; count: number }>
> {
	const response = await apiClient.get('/products/categories');
	return response.data.categories;
}

// ============================================================================
// WARRANTY CLAIMS API ENDPOINTS
// ============================================================================

/**
 * Search warranty claims with text and filters (standard keyword search)
 */
export async function searchClaims(
	searchText?: string,
	filters?: ClaimSearchFilters,
	pagination?: PaginationParams,
	includeQuery: boolean = false
): Promise<SearchResponse<WarrantyClaim>> {
	const response = await apiClient.get('/claims/search', {
		params: {
			search_text: searchText,
			...filters,
			limit: pagination?.limit || 20,
			cursor: pagination?.cursor,
			includeQuery
		}
	});
	return response.data;
}

/**
 * Vector search claims (semantic search using Voyage AI)
 */
export async function vectorSearchClaims(
	searchText: string,
	filters?: ClaimSearchFilters,
	pagination?: PaginationParams,
	includeQuery: boolean = false
): Promise<SearchResponse<WarrantyClaim>> {
	const response = await apiClient.post('/claims/search/semantic', {
		query: searchText,
		filters,
		limit: pagination?.limit || 20,
		num_candidates: 100,
		includeQuery
	});
	return response.data;
}

/**
 * Unified claims search - switches between standard and semantic based on mode
 */
export async function searchClaimsUnified(
	searchText: string | undefined,
	filters: ClaimSearchFilters | undefined,
	pagination: PaginationParams | undefined,
	mode: SearchMode,
	includeQuery: boolean = false
): Promise<SearchResponse<WarrantyClaim>> {
	if (mode === 'semantic' && searchText && searchText.trim().length > 0) {
		return vectorSearchClaims(searchText, filters, pagination, includeQuery);
	}
	return searchClaims(searchText, filters, pagination, includeQuery);
}

/**
 * Get claim by ID
 */
export async function getClaimById(claimId: string): Promise<WarrantyClaim> {
	const response = await apiClient.get(`/claims/${claimId}`);
	return response.data.claim;
}

/**
 * Get claims by dealer
 */
export async function getClaimsByDealer(
	dealerId: string,
	status?: string,
	limit?: number
): Promise<WarrantyClaim[]> {
	const response = await apiClient.get(`/claims/by-dealer/${dealerId}`, {
		params: { status, limit }
	});
	return response.data.claims;
}

/**
 * Get claim statistics
 */
export async function getClaimStatistics(dealerId?: string): Promise<any> {
	const response = await apiClient.get('/claims/statistics', {
		params: { dealer_id: dealerId }
	});
	return response.data;
}

/**
 * Get claim trend
 */
export async function getClaimTrend(months: number = 12, dealerId?: string): Promise<ClaimsTrend[]> {
	const response = await apiClient.get('/claims/trend', {
		params: { months, dealer_id: dealerId }
	});
	return response.data.trend;
}

/**
 * Autocomplete claims - searches across claim ID, customer name, and registration
 */
export async function autocompleteClaims(
	query: string,
	field: string = 'claimId',
	limit: number = 10
): Promise<Array<{ claimId: string; name: string; category?: string }>> {
	const response = await apiClient.get('/claims/autocomplete', {
		params: { q: query, field, limit }
	});
	// Map response to match SearchBar expected format (needs 'name' property)
	return response.data.suggestions.map((s: { claimId: string; customerName: string; vehicleModel: string; registrationNumber: string; status: string }) => ({
		claimId: s.claimId,
		name: s.customerName || s.claimId,
		category: `${s.claimId} • ${s.vehicleModel || ''} • ${s.status || ''}`.trim()
	}));
}

// ============================================================================
// DASHBOARD API ENDPOINTS
// ============================================================================

/**
 * Get product dashboard statistics
 */
export async function getProductDashboardStats(): Promise<ProductDashboardStats> {
	const response = await apiClient.get('/dashboard/products/stats');
	return response.data;
}

/**
 * Get claim dashboard statistics
 */
export async function getClaimDashboardStats(dealerId?: string): Promise<ClaimDashboardStats> {
	const response = await apiClient.get('/dashboard/claims/stats', {
		params: { dealerId }
	});
	return response.data;
}

/**
 * Get claims trend for dashboard
 */
export async function getDashboardClaimsTrend(
	months: number = 12,
	dealerId?: string
): Promise<{ trend: ClaimsTrend[]; months: number }> {
	const response = await apiClient.get('/dashboard/claims/trend', {
		params: { months, dealerId }
	});
	return response.data;
}

/**
 * Get dealer dashboard (combined stats)
 */
export async function getDealerDashboard(dealerId: string): Promise<any> {
	const response = await apiClient.get(`/dashboard/dealer/${dealerId}`);
	return response.data;
}

/**
 * Refresh materialized views
 */
export async function refreshViews(views: string[], force: boolean = false): Promise<any> {
	const response = await apiClient.post('/dashboard/refresh', null, {
		params: { views, force }
	});
	return response.data;
}

/**
 * Get top dealers by claims (reads from mv_dealer_claim_stats)
 */
export async function getTopDealers(limit: number = 10): Promise<DealerClaimStats[]> {
	const response = await apiClient.get('/dashboard/dealers/top', {
		params: { limit }
	});
	return response.data.dealers;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Format currency in MYR
 */
export function formatCurrency(value: number): string {
	return `RM ${value.toLocaleString('en-MY', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * Format number with thousands separator
 */
export function formatNumber(value: number): string {
	return value.toLocaleString('en-MY');
}

/**
 * Format date in Malaysian format (DD/MM/YYYY)
 */
export function formatDate(dateString: string): string {
	return new Date(dateString).toLocaleDateString('en-MY', {
		day: '2-digit',
		month: '2-digit',
		year: 'numeric'
	});
}

/**
 * Get status badge class
 */
export function getStatusBadgeClass(status: string): string {
	const statusMap: Record<string, string> = {
		Draft: 'status-draft',
		'Pending Review': 'status-pending',
		'Under Review': 'status-under-review',
		'Awaiting Parts': 'status-pending',
		Approved: 'status-approved',
		Rejected: 'status-rejected',
		Paid: 'status-paid',
		Closed: 'status-closed'
	};
	return statusMap[status] || 'badge-info';
}

/**
 * Get inventory status badge class
 */
export function getInventoryStatusClass(status: string): string {
	const statusMap: Record<string, string> = {
		'In Stock': 'inventory-in-stock',
		'Low Stock': 'inventory-low-stock',
		'Out of Stock': 'inventory-out-of-stock'
	};
	return statusMap[status] || 'badge-info';
}

export default apiClient;
