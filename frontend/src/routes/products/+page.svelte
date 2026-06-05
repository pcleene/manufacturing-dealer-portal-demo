<script lang="ts">
	import { onMount } from 'svelte';
	import SearchBar from '$lib/components/SearchBar.svelte';
	import SearchModeToggle from '$lib/components/SearchModeToggle.svelte';
	import FacetPanel from '$lib/components/FacetPanel.svelte';
	import Pagination from '$lib/components/Pagination.svelte';
	import QueryModal from '$lib/components/QueryModal.svelte';
	import {
		searchProductsUnified,
		autocompleteProducts,
		formatCurrency,
		getInventoryStatusClass,
		type Product,
		type ProductSearchFilters,
		type SearchResponse,
		type SearchMode
	} from '$lib/api';

	let searchText = '';
	let filters: ProductSearchFilters = {};
	let selectedFilters: Record<string, string[]> = {};
	let searchResponse: SearchResponse<Product> | null = null;
	let loading = false;
	let error = '';
	let searchMode: SearchMode = 'standard';
	let currentPage = 1;
	const pageSize = 20;
	
	// Query modal state
	let showQueryModal = false;
	let currentQuery = '';

	const columns = [
		{ key: 'partNumber', label: 'Part Number', sortable: true },
		{ key: 'name', label: 'Name', sortable: true },
		{ key: 'category', label: 'Category', sortable: true },
		{ key: 'pricing.msrp', label: 'MSRP', sortable: true, format: (v: number) => formatCurrency(v) },
		{
			key: 'inventory.status',
			label: 'Status',
			sortable: true,
			format: (v: string) => v,
			badge: true,
			badgeClass: (v: string) => getInventoryStatusClass(v)
		},
		{ key: 'inventory.totalQuantity', label: 'Stock', sortable: true }
	];

	async function handleSearch(includeQuery = true) {
		loading = true;
		error = '';

		try {
			searchResponse = await searchProductsUnified(
				searchText || undefined,
				filters,
				{ limit: 20 },
				searchMode,
				includeQuery && searchMode === 'standard'  // Only include query for standard search
			);
			if (searchResponse?.debugQuery) {
				currentQuery = searchResponse.debugQuery;
			}
		} catch (err: any) {
			error = err.message || 'Search failed';
			console.error('Search error:', err);
		} finally {
			loading = false;
		}
	}

	function showQuery() {
		if (currentQuery) {
			showQueryModal = true;
		}
	}

	async function loadMore() {
		if (!searchResponse?.pagination.hasMore || loading) return;

		loading = true;
		try {
			const response = await searchProductsUnified(
				searchText || undefined,
				filters,
				{
					limit: 20,
					cursor: searchResponse.pagination.cursor || undefined
				},
				searchMode
			);

			searchResponse = {
				...response,
				results: [...searchResponse.results, ...response.results]
			};
		} catch (err: any) {
			error = err.message || 'Failed to load more results';
		} finally {
			loading = false;
		}
	}

	function handleFilterChange(event: CustomEvent) {
		const { field, values } = event.detail;

		// Update selectedFilters for UI state
		if (values.length > 0) {
			selectedFilters[field] = values;
		} else {
			delete selectedFilters[field];
		}
		selectedFilters = { ...selectedFilters };

		// Map fieldKey to API filter params
		if (field === 'category') {
			filters.category = values.length > 0 ? values : undefined;
		} else if (field === 'subcategory') {
			filters.subcategory = values.length > 0 ? values : undefined;
		} else if (field === 'inventory.status') {
			filters.availability_status = values.length > 0 ? values : undefined;
		} else if (field === 'compatibleModels.modelCode') {
			filters.model_series = values.length > 0 ? values : undefined;
		}

		currentPage = 1;
		handleSearch();
	}

	function handleClearFilters() {
		selectedFilters = {};
		filters = {};
		currentPage = 1;
		handleSearch();
	}

	async function handleAutocomplete(query: string) {
		return autocompleteProducts(query, 'name', 8);
	}

	function handleNextPage() {
		if (searchResponse?.pagination.hasMore) {
			currentPage++;
			loadMore();
		}
	}

	function handlePrevPage() {
		if (currentPage > 1) {
			currentPage--;
			// For cursor-based pagination, we need to re-fetch from the beginning
			// This is a simplification - ideal would be to cache cursors
			handleSearch();
		}
	}

	function handleModeChange(event: CustomEvent) {
		searchMode = event.detail as SearchMode;
		// Clear results and re-search if there's text
		if (searchText) {
			handleSearch();
		}
	}

	onMount(() => {
		handleSearch();
	});
</script>

<svelte:head>
	<title>Products - OEMPartner Dealer Portal</title>
</svelte:head>

<div class="space-y-6">
	<!-- Page Header -->
	<div class="page-header-section">
		<div class="page-header-content">
			<div class="page-icon">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
				</svg>
			</div>
			<div>
				<h1 class="page-title">Product Catalog</h1>
				<p class="page-subtitle">
					Search parts, accessories, and consumables for OEMPartner motorcycles
				</p>
			</div>
		</div>
		{#if searchResponse?.pagination?.totalCount}
			<div class="results-header">
				<div class="results-badge">
					<span class="results-count">{searchResponse.pagination.totalCount.toLocaleString()}</span>
					<span class="results-label">products</span>
				</div>
				{#if currentQuery && searchMode === 'standard'}
					<button class="query-btn" on:click={showQuery} title="View MongoDB Query">
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
						</svg>
						<span>Query</span>
					</button>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Search Controls -->
	<div class="search-controls">
		<div class="search-bar-wrapper">
			<SearchBar
				bind:value={searchText}
				placeholder={searchMode === 'semantic' 
					? "Describe what you're looking for in natural language..."
					: "Search by part number, name, or description..."}
				on:search={handleSearch}
				on:clear={() => { searchText = ''; currentPage = 1; handleSearch(); }}
				{loading}
				autocompleteEnabled={searchMode === 'standard'}
				autocompleteFunction={handleAutocomplete}
			/>
		</div>
		<SearchModeToggle bind:mode={searchMode} on:change={handleModeChange} />
	</div>

	<!-- Semantic Search Suggestions -->
	{#if searchMode === 'semantic'}
		<div class="semantic-suggestions">
			<div class="suggestions-header">
				<svg class="suggestions-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
				</svg>
				<span>Try asking</span>
			</div>
			<div class="suggestions-chips">
				<button 
					class="suggestion-chip" 
					on:click={() => { searchText = "parts to keep my engine cool in hot weather"; handleSearch(); }}
				>
					<span class="chip-icon">🌡️</span>
					parts to keep my engine cool in hot weather
				</button>
				<button 
					class="suggestion-chip" 
					on:click={() => { searchText = "protection from rain for riding"; handleSearch(); }}
				>
					<span class="chip-icon">🌧️</span>
					protection from rain for riding
				</button>
				<button 
					class="suggestion-chip" 
					on:click={() => { searchText = "accessories for long distance touring"; handleSearch(); }}
				>
					<span class="chip-icon">🛣️</span>
					accessories for long distance touring
				</button>
				<button 
					class="suggestion-chip" 
					on:click={() => { searchText = "cosmetic upgrades to make my bike look better"; handleSearch(); }}
				>
					<span class="chip-icon">✨</span>
					cosmetic upgrades to make my bike look better
				</button>
				<button 
					class="suggestion-chip" 
					on:click={() => { searchText = "replacement body parts for damaged fairing"; handleSearch(); }}
				>
					<span class="chip-icon">🔧</span>
					replacement body parts for damaged fairing
				</button>
			</div>
		</div>
	{/if}

	<div class="flex gap-6">
		<!-- Facet Panel - only show for standard search or when we have facets -->
		{#if searchResponse?.facets && searchResponse.facets.length > 0 && searchMode === 'standard'}
			<div class="w-64 flex-shrink-0">
				<FacetPanel 
					facets={searchResponse.facets} 
					{selectedFilters}
					on:filterChange={handleFilterChange}
					on:clearFilters={handleClearFilters}
				/>
			</div>
		{/if}

		<!-- Results -->
		<div class="flex-1">
			{#if loading && !searchResponse}
				<div class="flex justify-center items-center h-64">
					<div class="text-center">
						<svg
							class="animate-spin h-10 w-10 text-OEMPartner-blue mx-auto"
							fill="none"
							viewBox="0 0 24 24"
						>
							<circle
								class="opacity-25"
								cx="12"
								cy="12"
								r="10"
								stroke="currentColor"
								stroke-width="4"
							/>
							<path
								class="opacity-75"
								fill="currentColor"
								d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
							/>
						</svg>
						<p class="mt-4 text-gray-600">
							{searchMode === 'semantic' ? 'AI is analyzing your query...' : 'Searching products...'}
						</p>
					</div>
				</div>
			{:else if error}
				<div class="bg-red-50 border border-red-200 rounded-lg p-4">
					<div class="flex items-start gap-3">
						<svg class="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
						<div>
							<p class="text-red-800 font-medium">Search Error</p>
							<p class="text-red-700 text-sm mt-1">{error}</p>
							{#if searchMode === 'semantic'}
								<p class="text-red-600 text-xs mt-2">
									Semantic search requires vector embeddings. Make sure embeddings have been generated.
								</p>
							{/if}
						</div>
					</div>
				</div>
			{:else if searchResponse}
				{#if searchResponse.results.length === 0}
					<div class="text-center py-12">
						<svg
							class="mx-auto h-12 w-12 text-gray-400"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
							/>
						</svg>
						<h3 class="mt-2 text-sm font-medium text-gray-900">No products found</h3>
						<p class="mt-1 text-sm text-gray-500">
							{#if searchMode === 'semantic'}
								Try rephrasing your query or switch to Standard search.
							{:else}
								Try adjusting your search or filter criteria.
							{/if}
						</p>
					</div>
				{:else}
					<!-- Semantic search indicator -->
					{#if searchMode === 'semantic' && searchText}
						<div class="mb-4 flex items-center gap-2 text-sm text-indigo-600">
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
							</svg>
							<span>Showing AI-powered semantic results for "{searchText}"</span>
						</div>
					{/if}

					<!-- Results Table -->
					<div class="results-table-wrapper">
						<table class="results-table">
							<thead>
								<tr>
									<th>Part Number</th>
									<th>Product Name</th>
									<th>Category</th>
									<th>MSRP</th>
									<th>Status</th>
									<th>Stock</th>
									{#if searchMode === 'semantic'}
										<th>Score</th>
									{/if}
								</tr>
							</thead>
							<tbody>
								{#each searchResponse.results as product, index}
									<tr
										class="result-row"
										style="animation-delay: {index * 30}ms"
										on:click={() => (window.location.href = `/products/${product.partNumber}`)}
									>
										<td>
											<span class="part-number">{product.partNumber}</span>
										</td>
										<td>
											<div class="product-info">
												<span class="product-name">{product.name}</span>
												<span class="product-sub">{product.subcategory}</span>
											</div>
										</td>
										<td>
											<span class="category-tag">{product.category}</span>
										</td>
										<td>
											<span class="price">{formatCurrency(product.pricing.msrp)}</span>
										</td>
										<td>
											<span class="badge {getInventoryStatusClass(product.inventory.status)}">
												{product.inventory.status}
											</span>
										</td>
										<td>
											<span class="stock-qty">{product.inventory.totalQuantity.toLocaleString()}</span>
										</td>
										{#if searchMode === 'semantic'}
											<td>
												{#if product.vectorScore}
													<div class="score-bar">
														<div class="score-fill" style="width: {Math.round(product.vectorScore * 100)}%"></div>
														<span class="score-text">{(product.vectorScore * 100).toFixed(0)}%</span>
													</div>
												{:else}
													<span class="score-na">-</span>
												{/if}
											</td>
										{/if}
									</tr>
								{/each}
							</tbody>
						</table>
					</div>

					<!-- Pagination -->
					<Pagination
						hasMore={searchResponse.pagination.hasMore}
						totalCount={searchResponse.pagination.totalCount}
						{currentPage}
						{loading}
						pageSize={pageSize}
						on:next={handleNextPage}
						on:previous={handlePrevPage}
					/>
				{/if}
			{/if}
		</div>
	</div>
</div>

<!-- Query Modal -->
<QueryModal bind:show={showQueryModal} query={currentQuery} />

<style>
	/* Search Controls */
	.search-controls {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.search-bar-wrapper {
		flex: 1;
	}

	@media (min-width: 768px) {
		.search-controls {
			flex-direction: row;
			align-items: flex-start;
			gap: 1.5rem;
		}
	}

	/* Semantic Suggestions */
	.semantic-suggestions {
		background: linear-gradient(135deg, rgba(99, 102, 241, 0.04) 0%, rgba(139, 92, 246, 0.04) 100%);
		border: 1px solid rgba(99, 102, 241, 0.12);
		border-radius: 12px;
		padding: 0.875rem 1.25rem;
		animation: fadeIn 0.3s ease-out;
	}

	@keyframes fadeIn {
		from { opacity: 0; transform: translateY(-4px); }
		to { opacity: 1; transform: translateY(0); }
	}

	.suggestions-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.75rem;
	}

	.suggestions-icon {
		width: 1rem;
		height: 1rem;
		color: #6366f1;
		opacity: 0.8;
	}

	.suggestions-header span {
		font-size: 0.75rem;
		font-weight: 500;
		color: #6366f1;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.suggestions-chips {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.suggestion-chip {
		display: inline-flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.5rem 0.875rem;
		background: white;
		border: 1px solid rgba(99, 102, 241, 0.2);
		border-radius: 99px;
		font-size: 0.8125rem;
		color: #475569;
		cursor: pointer;
		transition: all 0.2s ease;
		box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
	}

	.suggestion-chip:hover {
		background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
		color: white;
		border-color: transparent;
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
	}

	.chip-icon {
		font-size: 0.875rem;
		line-height: 1;
	}

	.suggestion-chip:hover .chip-icon {
		transform: scale(1.1);
	}

	@media (max-width: 768px) {
		.semantic-suggestions {
			padding: 0.75rem 1rem;
		}

		.suggestion-chip {
			font-size: 0.75rem;
			padding: 0.4rem 0.75rem;
		}
	}

	/* Page Header */
	.page-header-section {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.page-header-content {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.page-icon {
		width: 3.5rem;
		height: 3.5rem;
		background: linear-gradient(135deg, #0033A0 0%, #002277 100%);
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: white;
		flex-shrink: 0;
		box-shadow: 0 4px 12px rgba(0, 51, 160, 0.25);
	}

	.page-icon svg {
		width: 1.5rem;
		height: 1.5rem;
	}

	.page-title {
		font-size: 1.875rem;
		font-weight: 800;
		color: #0f172a;
		letter-spacing: -0.025em;
		margin: 0;
	}

	.page-subtitle {
		font-size: 0.9375rem;
		color: #64748b;
		margin-top: 0.25rem;
	}

	.results-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.results-badge {
		display: flex;
		align-items: baseline;
		gap: 0.375rem;
		background: linear-gradient(135deg, #EBF4FF 0%, #E0EBFF 100%);
		padding: 0.5rem 1rem;
		border-radius: 99px;
		border: 1px solid #c7d8f7;
	}

	.results-count {
		font-size: 1.25rem;
		font-weight: 700;
		color: #0033A0;
	}

	.results-label {
		font-size: 0.8125rem;
		color: #64748b;
	}

	.query-btn {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.5rem 0.875rem;
		background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
		border: 1px solid #3d3d3d;
		border-radius: 99px;
		color: #d4d4d4;
		font-size: 0.75rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.query-btn:hover {
		background: linear-gradient(135deg, #2d2d2d 0%, #3d3d3d 100%);
		border-color: #4d4d4d;
		color: white;
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
	}

	.query-btn svg {
		width: 0.875rem;
		height: 0.875rem;
	}

	/* Results Table */
	.results-table-wrapper {
		background: white;
		border-radius: 12px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.06);
		border: 1px solid #e5e7eb;
		overflow: hidden;
	}

	.results-table {
		width: 100%;
		border-collapse: collapse;
	}

	.results-table thead {
		background: linear-gradient(to bottom, #f8fafc, #f1f5f9);
		border-bottom: 2px solid #0033A0;
	}

	.results-table th {
		padding: 0.875rem 1.25rem;
		text-align: left;
		font-size: 0.6875rem;
		font-weight: 700;
		color: #475569;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.results-table tbody {
		background: white;
	}

	.result-row {
		border-bottom: 1px solid #f1f5f9;
		cursor: pointer;
		transition: all 0.15s;
		animation: fadeInUp 0.3s ease-out both;
	}

	@keyframes fadeInUp {
		from {
			opacity: 0;
			transform: translateY(8px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.result-row:hover {
		background: linear-gradient(to right, #f8fafc, #EBF4FF);
	}

	.result-row:last-child {
		border-bottom: none;
	}

	.results-table td {
		padding: 1rem 1.25rem;
		vertical-align: middle;
	}

	.part-number {
		font-size: 0.875rem;
		font-weight: 600;
		color: #0033A0;
		font-family: 'SF Mono', Monaco, monospace;
	}

	.product-info {
		display: flex;
		flex-direction: column;
		gap: 0.125rem;
	}

	.product-name {
		font-size: 0.875rem;
		font-weight: 500;
		color: #1e293b;
	}

	.product-sub {
		font-size: 0.75rem;
		color: #94a3b8;
	}

	.category-tag {
		font-size: 0.75rem;
		color: #64748b;
		background: #f1f5f9;
		padding: 0.25rem 0.625rem;
		border-radius: 6px;
	}

	.price {
		font-size: 0.875rem;
		font-weight: 600;
		color: #1e293b;
	}

	.stock-qty {
		font-size: 0.875rem;
		color: #64748b;
		font-weight: 500;
	}

	.score-bar {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.score-fill {
		height: 6px;
		background: linear-gradient(90deg, #0033A0, #6366f1);
		border-radius: 3px;
		min-width: 4rem;
	}

	.score-text {
		font-size: 0.75rem;
		color: #64748b;
		font-weight: 500;
	}

	.score-na {
		color: #cbd5e1;
	}

	/* Mobile */
	@media (max-width: 768px) {
		.page-header-section {
			flex-direction: column;
			align-items: flex-start;
		}

		.page-icon {
			width: 2.5rem;
			height: 2.5rem;
		}

		.page-icon svg {
			width: 1.25rem;
			height: 1.25rem;
		}

		.page-title {
			font-size: 1.5rem;
		}

		.results-table-wrapper {
			overflow-x: auto;
		}

		.results-table {
			min-width: 700px;
		}
	}
</style>
