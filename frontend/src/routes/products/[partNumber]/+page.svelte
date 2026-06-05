<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import {
		getProductByPartNumber,
		getRelatedProducts,
		formatCurrency,
		formatDate,
		getInventoryStatusClass,
		type Product
	} from '$lib/api';
	import { cart, toasts } from '$lib/stores/cart';

	let product: Product | null = null;
	let relatedProducts: Product[] = [];
	let loading = true;
	let error = '';
	let quantity = 1;

	$: partNumber = $page.params.partNumber;

	onMount(async () => {
		await loadProduct();
	});

	async function loadProduct() {
		loading = true;
		error = '';

		try {
			const [productData, related] = await Promise.all([
				getProductByPartNumber(partNumber),
				getRelatedProducts(partNumber).catch(() => [])
			]);

			product = productData;
			relatedProducts = related;
		} catch (err: any) {
			error = err.response?.data?.detail || err.message || 'Failed to load product';
			console.error('Load product error:', err);
		} finally {
			loading = false;
		}
	}

	function addToCart() {
		if (!product) return;
		
		cart.addItem({
			partNumber: product.partNumber,
			sku: product.sku,
			name: product.name,
			category: product.category,
			subcategory: product.subcategory,
			unitPrice: product.pricing.dealerPrice,
			msrp: product.pricing.msrp
		}, quantity);

		toasts.show(`Added ${quantity}x ${product.partNumber} to cart`, 'success');
		quantity = 1;
	}

	function getDifficultyColor(level: string): string {
		const colors: Record<string, string> = {
			'Easy': 'difficulty-easy',
			'Intermediate': 'difficulty-intermediate',
			'Advanced': 'difficulty-advanced',
			'Professional': 'difficulty-professional'
		};
		return colors[level] || '';
	}

	function getDocTypeIcon(docType: string): string {
		const icons: Record<string, string> = {
			'Installation': 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4',
			'Repair': 'M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z',
			'Maintenance': 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z',
			'Safety': 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
			'Technical Bulletin': 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'
		};
		return icons[docType] || icons['Technical Bulletin'];
	}
</script>

<svelte:head>
	<title>{product?.name || 'Product'} - OEMPartner Dealer Portal</title>
</svelte:head>

{#if loading}
	<div class="loading-container">
		<div class="loading-spinner">
			<svg class="animate-spin" fill="none" viewBox="0 0 24 24">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
				<path
					class="opacity-75"
					fill="currentColor"
					d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
				/>
			</svg>
			<p>Loading product details...</p>
		</div>
	</div>
{:else if error}
	<div class="error-container">
		<div class="error-icon">
			<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
		</div>
		<h2>Product Not Found</h2>
		<p>{error}</p>
		<a href="/products" class="back-button">
			<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
			</svg>
			Back to Products
		</a>
	</div>
{:else if product}
	<div class="product-detail">
		<!-- Top Navigation Bar -->
		<div class="top-nav">
			<a href="/products" class="back-link">
				<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
				</svg>
				Back to Product Catalog
			</a>
			<nav class="breadcrumb">
				<a href="/products">Products</a>
				<svg class="separator" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
				</svg>
				<a href="/products?category={encodeURIComponent(product.category)}">{product.category}</a>
				<svg class="separator" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
				</svg>
				<span class="current">{product.partNumber}</span>
			</nav>
		</div>

		<!-- Product Header -->
		<header class="product-header">
			<div class="header-content">
				<div class="page-icon">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
					</svg>
				</div>
				<div class="header-text">
					<div class="part-number-row">
						<span class="part-number">{product.partNumber}</span>
						<span class="sku">SKU: {product.sku}</span>
					</div>
					<h1>{product.name}</h1>
				</div>
			</div>
			<div class="header-status">
				<span class="badge {getInventoryStatusClass(product.inventory.status)} status-badge">
					{product.inventory.status}
				</span>
			</div>
		</header>

		<div class="content-grid">
			<!-- Sidebar (Left) -->
			<aside class="sidebar">
				<!-- Pricing Card -->
				<div class="sidebar-card pricing-card animate-in" style="animation-delay: 50ms">
					<div class="card-header">
						<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
						<h3>Pricing</h3>
					</div>
					<div class="card-body">
						<div class="price-row primary">
							<span class="label">MSRP</span>
							<span class="value">{formatCurrency(product.pricing.msrp)}</span>
						</div>
						<div class="price-row dealer">
							<span class="label">Dealer Price</span>
							<span class="value">{formatCurrency(product.pricing.dealerPrice)}</span>
						</div>
						<div class="price-row margin">
							<span class="label">Margin</span>
							<span class="value">{((1 - product.pricing.dealerPrice / product.pricing.msrp) * 100).toFixed(1)}%</span>
						</div>
						<div class="divider"></div>
						
						<!-- Add to Cart Section -->
						<div class="add-to-cart-section">
							<div class="quantity-selector">
								<button type="button" on:click={() => quantity = Math.max(1, quantity - 1)} aria-label="Decrease quantity">−</button>
								<input type="number" bind:value={quantity} min="1" max="99" />
								<button type="button" on:click={() => quantity = Math.min(99, quantity + 1)} aria-label="Increase quantity">+</button>
							</div>
							<button 
								class="add-to-cart-btn" 
								on:click={addToCart}
								disabled={product.inventory.status === 'Out of Stock'}
							>
								<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
								</svg>
								{product.inventory.status === 'Out of Stock' ? 'Out of Stock' : 'Add to Cart'}
							</button>
						</div>
						
						<div class="last-update">
							<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
							<span>Updated {formatDate(product.pricing.lastPriceUpdate)}</span>
						</div>
					</div>
				</div>

				<!-- Inventory Card -->
				<div class="sidebar-card inventory-card animate-in" style="animation-delay: 100ms">
					<div class="card-header">
						<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
						</svg>
						<h3>Inventory</h3>
					</div>
					<div class="card-body">
						<div class="inventory-stat">
							<span class="stat-value">{product.inventory.totalQuantity.toLocaleString()}</span>
							<span class="stat-label">Total Units</span>
						</div>
						<div class="inventory-row">
							<span class="label">Reorder Point</span>
							<span class="value">{product.inventory.reorderPoint}</span>
						</div>
						<div class="inventory-row">
							<span class="label">Last Stock Check</span>
							<span class="value">{formatDate(product.inventory.lastStockCheck)}</span>
						</div>
						{#if product.inventory.totalQuantity <= product.inventory.reorderPoint}
							<div class="alert warning">
								<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
								</svg>
								<span>Stock at or below reorder point</span>
							</div>
						{/if}
					</div>
				</div>

				<!-- Category Info -->
				<div class="sidebar-card animate-in" style="animation-delay: 150ms">
					<div class="card-header">
						<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
						</svg>
						<h3>Category</h3>
					</div>
					<div class="card-body">
						<div class="category-item">
							<span class="label">Category</span>
							<a href="/products?category={encodeURIComponent(product.category)}" class="value link">{product.category}</a>
						</div>
						<div class="category-item">
							<span class="label">Subcategory</span>
							<span class="value">{product.subcategory}</span>
						</div>
						<div class="category-item">
							<span class="label">Brand</span>
							<span class="value brand">{product.brand}</span>
						</div>
					</div>
				</div>

				<!-- Supersession Info -->
				{#if product.supersession?.supersededBy || product.supersession?.supersedes}
					<div class="sidebar-card supersession-card animate-in" style="animation-delay: 200ms">
						<div class="card-header">
							<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
							</svg>
							<h3>Supersession</h3>
						</div>
						<div class="card-body">
							{#if product.supersession.supersededBy}
								<div class="supersession-item replaced">
									<span class="label">Replaced By</span>
									<a href="/products/{product.supersession.supersededBy}" class="value">
										{product.supersession.supersededBy}
										<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
										</svg>
									</a>
								</div>
							{/if}
							{#if product.supersession.supersedes}
								<div class="supersession-item replaces">
									<span class="label">Replaces</span>
									<a href="/products/{product.supersession.supersedes}" class="value">
										{product.supersession.supersedes}
										<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
										</svg>
									</a>
								</div>
							{/if}
						</div>
					</div>
				{/if}
			</aside>

			<!-- Main Content (Right) -->
			<div class="main-content">
				<!-- Description Card -->
				<div class="detail-card animate-in" style="animation-delay: 0ms">
					<div class="card-header">
						<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7" />
						</svg>
						<h2>Description</h2>
					</div>
					<div class="card-body">
						<p class="description-text">{product.description}</p>
					</div>
				</div>

				<!-- Compatible Models -->
				{#if product.compatibleModels && product.compatibleModels.length > 0}
					<div class="detail-card animate-in" style="animation-delay: 50ms">
						<div class="card-header">
							<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
							</svg>
							<h2>Compatible Models</h2>
							<span class="count-badge">{product.compatibleModels.length}</span>
						</div>
						<div class="card-body">
							<div class="table-wrapper">
								<table class="detail-table">
									<thead>
										<tr>
											<th>Model Code</th>
											<th>Model Name</th>
											<th>Years</th>
											<th>Notes</th>
										</tr>
									</thead>
									<tbody>
										{#each product.compatibleModels as model}
											<tr>
												<td>
													<span class="model-code">{model.modelCode}</span>
												</td>
												<td>{model.modelName}</td>
												<td>
													<span class="year-range">{model.yearStart} – {model.yearEnd}</span>
												</td>
												<td class="notes">{model.notes || '—'}</td>
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
						</div>
					</div>
				{/if}

				<!-- Specifications -->
				{#if product.specifications && Object.keys(product.specifications).length > 0}
					<div class="detail-card animate-in" style="animation-delay: 100ms">
						<div class="card-header">
							<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
							</svg>
							<h2>Specifications</h2>
						</div>
						<div class="card-body">
							<dl class="specs-grid">
								{#each Object.entries(product.specifications) as [key, value]}
									{#if value}
										<div class="spec-item">
											<dt>{key.replace(/([A-Z])/g, ' $1').trim()}</dt>
											<dd>{value}</dd>
										</div>
									{/if}
								{/each}
							</dl>
						</div>
					</div>
				{/if}

				<!-- Warehouse Inventory -->
				{#if product.inventory.warehouses && product.inventory.warehouses.length > 0}
					<div class="detail-card animate-in" style="animation-delay: 150ms">
						<div class="card-header">
							<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
							</svg>
							<h2>Warehouse Inventory</h2>
							<span class="count-badge">{product.inventory.warehouses.length} locations</span>
						</div>
						<div class="card-body">
							<div class="table-wrapper">
								<table class="detail-table">
									<thead>
										<tr>
											<th>Warehouse</th>
											<th>Code</th>
											<th>Quantity</th>
											<th>Last Restocked</th>
										</tr>
									</thead>
									<tbody>
										{#each product.inventory.warehouses as warehouse}
											<tr>
												<td>
													<span class="warehouse-name">{warehouse.name}</span>
												</td>
												<td>
													<span class="warehouse-code">{warehouse.code}</span>
												</td>
												<td>
													<span class="quantity" class:low={warehouse.quantity < 10}>
														{warehouse.quantity.toLocaleString()}
													</span>
												</td>
												<td class="date">{formatDate(warehouse.lastRestocked)}</td>
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
						</div>
					</div>
				{/if}

				<!-- Technical Documentation -->
				{#if product.technicalDocs && product.technicalDocs.length > 0}
					<div class="detail-card tech-docs-card animate-in" style="animation-delay: 200ms">
						<div class="card-header">
							<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
							</svg>
							<h2>Technical Documentation</h2>
							<span class="count-badge">{product.technicalDocs.length} documents</span>
						</div>
						<div class="card-body">
							<div class="tech-docs-grid">
								{#each product.technicalDocs as doc}
									<a href={doc.downloadUrl} target="_blank" rel="noopener noreferrer" class="tech-doc-item">
										<div class="doc-icon">
											<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={getDocTypeIcon(doc.docType)} />
											</svg>
										</div>
										<div class="doc-info">
											<span class="doc-type-badge">{doc.docType}</span>
											<h4>{doc.title}</h4>
											<p class="doc-summary">{doc.summary}</p>
											<div class="doc-meta">
												<span>v{doc.version}</span>
												<span>•</span>
												<span>{doc.pageCount} pages</span>
												<span>•</span>
												<span>{doc.fileSize}</span>
											</div>
											<div class="doc-models">
												{#each doc.applicableModels.slice(0, 3) as model}
													<span class="model-tag">{model}</span>
												{/each}
												{#if doc.applicableModels.length > 3}
													<span class="model-tag more">+{doc.applicableModels.length - 3}</span>
												{/if}
											</div>
										</div>
										<div class="doc-download">
											<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
											</svg>
											<span>PDF</span>
										</div>
									</a>
								{/each}
							</div>
						</div>
					</div>
				{/if}

				<!-- Manufacturing Info -->
				{#if product.manufacturing}
					<div class="detail-card animate-in" style="animation-delay: 250ms">
						<div class="card-header">
							<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
							</svg>
							<h2>Manufacturing Info</h2>
						</div>
						<div class="card-body">
							<div class="manufacturing-grid">
								<div class="mfg-item">
									<span class="mfg-label">Country of Origin</span>
									<span class="mfg-value">{product.manufacturing.countryOfOrigin}</span>
								</div>
								<div class="mfg-item">
									<span class="mfg-label">Manufacturer</span>
									<span class="mfg-value">{product.manufacturing.manufacturerName}</span>
								</div>
								<div class="mfg-item">
									<span class="mfg-label">Plant Code</span>
									<span class="mfg-value code">{product.manufacturing.plantCode}</span>
								</div>
								<div class="mfg-item">
									<span class="mfg-label">Lead Time</span>
									<span class="mfg-value">{product.manufacturing.leadTimeDays} days</span>
								</div>
								<div class="mfg-item">
									<span class="mfg-label">Min Order Qty</span>
									<span class="mfg-value">{product.manufacturing.minOrderQuantity} units</span>
								</div>
								<div class="mfg-item full-width">
									<span class="mfg-label">Quality Certifications</span>
									<div class="certifications">
										{#each product.manufacturing.qualityCertifications as cert}
											<span class="cert-badge">{cert}</span>
										{/each}
									</div>
								</div>
							</div>
						</div>
					</div>
				{/if}

				<!-- Fitment Guide -->
				{#if product.fitmentNotes}
					<div class="detail-card animate-in" style="animation-delay: 300ms">
						<div class="card-header">
							<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
							</svg>
							<h2>Fitment Guide</h2>
						</div>
						<div class="card-body">
							<div class="fitment-header">
								<div class="difficulty-badge {getDifficultyColor(product.fitmentNotes.difficultyLevel)}">
									{product.fitmentNotes.difficultyLevel}
								</div>
								<div class="install-time">
									<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
									</svg>
									<span>Est. {product.fitmentNotes.estimatedInstallTime}</span>
								</div>
								{#if product.fitmentNotes.professionalInstallRecommended}
									<div class="pro-recommended">
										<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
										</svg>
										<span>Professional Install Recommended</span>
									</div>
								{/if}
							</div>
							
							<div class="tools-section">
								<h4>Tools Required</h4>
								<div class="tools-list">
									{#each product.fitmentNotes.toolsRequired as tool}
										<span class="tool-tag">{tool}</span>
									{/each}
								</div>
							</div>

							{#if product.fitmentNotes.specialInstructions}
								<div class="special-instructions">
									<h4>Special Instructions</h4>
									<p>{product.fitmentNotes.specialInstructions}</p>
								</div>
							{/if}
						</div>
					</div>
				{/if}

				<!-- Packaging & Shipping -->
				{#if product.packaging}
					<div class="detail-card animate-in" style="animation-delay: 350ms">
						<div class="card-header">
							<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
							</svg>
							<h2>Packaging & Shipping</h2>
						</div>
						<div class="card-body">
							<div class="packaging-grid">
								<div class="pkg-item">
									<span class="pkg-label">Package Weight</span>
									<span class="pkg-value">{product.packaging.packageWeight}</span>
								</div>
								<div class="pkg-item">
									<span class="pkg-label">Package Dimensions</span>
									<span class="pkg-value">{product.packaging.packageDimensions}</span>
								</div>
								<div class="pkg-item">
									<span class="pkg-label">Units per Carton</span>
									<span class="pkg-value">{product.packaging.unitsPerCarton}</span>
								</div>
								<div class="pkg-item">
									<span class="pkg-label">Carton Barcode</span>
									<span class="pkg-value code">{product.packaging.cartonBarcode}</span>
								</div>
								{#if product.packaging.hazmatClass}
									<div class="pkg-item hazmat">
										<span class="pkg-label">Hazmat Classification</span>
										<span class="pkg-value hazmat-badge">{product.packaging.hazmatClass}</span>
									</div>
								{/if}
							</div>
						</div>
					</div>
				{/if}

				<!-- Sales Performance -->
				{#if product.salesData}
					<div class="detail-card sales-card animate-in" style="animation-delay: 400ms">
						<div class="card-header">
							<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
							</svg>
							<h2>Sales Performance</h2>
							<span class="internal-badge">Dealer View</span>
						</div>
						<div class="card-body">
							<div class="sales-stats">
								<div class="sales-stat">
									<span class="stat-number">{product.salesData.totalUnitsSold.toLocaleString()}</span>
									<span class="stat-label">Units Sold</span>
								</div>
								{#if product.salesData.avgRating}
									<div class="sales-stat">
										<span class="stat-number rating">
											<svg fill="currentColor" viewBox="0 0 24 24">
												<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
											</svg>
											{product.salesData.avgRating}
										</span>
										<span class="stat-label">{product.salesData.reviewCount} Reviews</span>
									</div>
								{/if}
								<div class="sales-stat">
									<span class="stat-number return-rate">{product.salesData.returnRate}%</span>
									<span class="stat-label">Return Rate</span>
								</div>
							</div>
							<div class="top-regions">
								<h4>Top Selling Regions</h4>
								<div class="regions-list">
									{#each product.salesData.topSellingRegions as region, i}
										<div class="region-item">
											<span class="region-rank">#{i + 1}</span>
											<span class="region-name">{region}</span>
										</div>
									{/each}
								</div>
							</div>
						</div>
					</div>
				{/if}
			</div>
		</div>

		<!-- Related Products -->
		{#if relatedProducts.length > 0}
			<section class="related-section animate-in" style="animation-delay: 200ms">
				<div class="section-header">
					<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
					</svg>
					<h2>Related Products</h2>
					<span class="count-badge">{relatedProducts.length}</span>
				</div>
				<div class="related-grid">
					{#each relatedProducts.slice(0, 6) as related, index}
						<a href="/products/{related.partNumber}" class="related-card" style="animation-delay: {250 + index * 30}ms">
							<div class="related-header">
								<span class="related-part-number">{related.partNumber}</span>
								<span class="badge {getInventoryStatusClass(related.inventory.status)} small">
									{related.inventory.status}
								</span>
							</div>
							<h4>{related.name}</h4>
							<p class="related-category">{related.category} / {related.subcategory}</p>
							<div class="related-footer">
								<span class="related-price">{formatCurrency(related.pricing.msrp)}</span>
								<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
								</svg>
							</div>
						</a>
					{/each}
				</div>
			</section>
		{/if}

	</div>
{/if}

<style>
	/* Animation */
	@keyframes fadeInUp {
		from {
			opacity: 0;
			transform: translateY(12px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.animate-in {
		animation: fadeInUp 0.4s ease-out both;
	}

	/* Loading State */
	.loading-container {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 400px;
	}

	.loading-spinner {
		text-align: center;
	}

	.loading-spinner svg {
		width: 3rem;
		height: 3rem;
		color: #0033A0;
		margin: 0 auto;
	}

	.loading-spinner p {
		margin-top: 1rem;
		color: #64748b;
		font-size: 0.9375rem;
	}

	/* Error State */
	.error-container {
		text-align: center;
		padding: 4rem 2rem;
		max-width: 28rem;
		margin: 0 auto;
	}

	.error-icon {
		width: 4rem;
		height: 4rem;
		background: #fef2f2;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 0 auto 1.5rem;
	}

	.error-icon svg {
		width: 2rem;
		height: 2rem;
		color: #ef4444;
	}

	.error-container h2 {
		font-size: 1.5rem;
		font-weight: 700;
		color: #1e293b;
		margin-bottom: 0.5rem;
	}

	.error-container p {
		color: #64748b;
		margin-bottom: 1.5rem;
	}

	.back-button {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		color: #0033A0;
		font-weight: 600;
		text-decoration: none;
		padding: 0.75rem 1.25rem;
		background: #EBF4FF;
		border-radius: 8px;
		transition: all 0.2s;
	}

	.back-button:hover {
		background: #dbeafe;
	}

	.back-button svg {
		width: 1.25rem;
		height: 1.25rem;
	}

	/* Product Detail Container */
	.product-detail {
		max-width: 1400px;
		margin: 0 auto;
	}

	/* Top Navigation */
	.top-nav {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
		flex-wrap: wrap;
		gap: 1rem;
	}

	/* Breadcrumb */
	.breadcrumb {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
	}

	.breadcrumb a {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		color: #64748b;
		text-decoration: none;
		transition: color 0.15s;
	}

	.breadcrumb a:hover {
		color: #0033A0;
	}

	.breadcrumb a svg {
		width: 1rem;
		height: 1rem;
	}

	.breadcrumb .separator {
		width: 0.875rem;
		height: 0.875rem;
		color: #cbd5e1;
	}

	.breadcrumb .current {
		color: #1e293b;
		font-weight: 600;
		font-family: 'SF Mono', Monaco, monospace;
	}

	/* Back Link in Top Nav */
	.top-nav .back-link {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		color: #0033A0;
		font-weight: 600;
		font-size: 0.875rem;
		text-decoration: none;
		padding: 0.5rem 1rem;
		background: #EBF4FF;
		border-radius: 8px;
		transition: all 0.2s;
	}

	.top-nav .back-link:hover {
		background: #dbeafe;
		gap: 0.625rem;
	}

	.top-nav .back-link svg {
		width: 1rem;
		height: 1rem;
	}

	/* Product Header */
	.product-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 1.5rem;
		margin-bottom: 2rem;
		flex-wrap: wrap;
	}

	.header-content {
		display: flex;
		align-items: flex-start;
		gap: 1.25rem;
	}

	.page-icon {
		width: 4rem;
		height: 4rem;
		background: linear-gradient(135deg, #0033A0 0%, #002277 100%);
		border-radius: 14px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: white;
		flex-shrink: 0;
		box-shadow: 0 6px 16px rgba(0, 51, 160, 0.3);
	}

	.page-icon svg {
		width: 1.75rem;
		height: 1.75rem;
	}

	.header-text {
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
	}

	.part-number-row {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.part-number {
		font-size: 1rem;
		font-weight: 700;
		color: #0033A0;
		font-family: 'SF Mono', Monaco, monospace;
		background: #EBF4FF;
		padding: 0.25rem 0.75rem;
		border-radius: 6px;
	}

	.sku {
		font-size: 0.75rem;
		color: #94a3b8;
	}

	.header-text h1 {
		font-size: 1.75rem;
		font-weight: 800;
		color: #0f172a;
		letter-spacing: -0.025em;
		margin: 0;
	}

	.header-status {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.status-badge {
		font-size: 0.9375rem;
		padding: 0.625rem 1.25rem;
		font-weight: 600;
	}

	/* Content Grid - Sidebar LEFT, Main Content RIGHT */
	.content-grid {
		display: grid;
		grid-template-columns: 320px 1fr;
		gap: 1.5rem;
		margin-bottom: 2rem;
	}

	.main-content {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.sidebar {
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	/* Detail Cards */
	.detail-card {
		background: white;
		border-radius: 14px;
		border: 1px solid #e5e7eb;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
		overflow: hidden;
	}

	.card-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 1.25rem 1.5rem;
		background: linear-gradient(to bottom, #f8fafc, #f1f5f9);
		border-bottom: 2px solid #0033A0;
	}

	.card-header svg {
		width: 1.25rem;
		height: 1.25rem;
		color: #0033A0;
	}

	.card-header h2 {
		font-size: 1rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0;
	}

	.count-badge {
		margin-left: auto;
		font-size: 0.75rem;
		font-weight: 600;
		color: #0033A0;
		background: #EBF4FF;
		padding: 0.25rem 0.625rem;
		border-radius: 99px;
	}

	.card-body {
		padding: 1.5rem;
	}

	.description-text {
		color: #475569;
		line-height: 1.7;
		font-size: 0.9375rem;
	}

	/* Tables */
	.table-wrapper {
		overflow-x: auto;
		margin: -0.5rem;
	}

	.detail-table {
		width: 100%;
		border-collapse: collapse;
	}

	.detail-table thead {
		background: #f8fafc;
	}

	.detail-table th {
		padding: 0.75rem 1rem;
		text-align: left;
		font-size: 0.6875rem;
		font-weight: 700;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		border-bottom: 1px solid #e5e7eb;
	}

	.detail-table td {
		padding: 0.875rem 1rem;
		font-size: 0.875rem;
		color: #475569;
		border-bottom: 1px solid #f1f5f9;
	}

	.detail-table tbody tr:last-child td {
		border-bottom: none;
	}

	.detail-table tbody tr:hover {
		background: #f8fafc;
	}

	.model-code {
		font-weight: 600;
		color: #0033A0;
		font-family: 'SF Mono', Monaco, monospace;
		font-size: 0.8125rem;
	}

	.year-range {
		color: #64748b;
		white-space: nowrap;
	}

	.notes {
		color: #94a3b8;
		font-style: italic;
	}

	.warehouse-name {
		font-weight: 500;
		color: #1e293b;
	}

	.warehouse-code {
		font-family: 'SF Mono', Monaco, monospace;
		font-size: 0.8125rem;
		color: #64748b;
		background: #f1f5f9;
		padding: 0.125rem 0.375rem;
		border-radius: 4px;
	}

	.quantity {
		font-weight: 600;
		color: #059669;
	}

	.quantity.low {
		color: #d97706;
	}

	.date {
		color: #64748b;
		font-size: 0.8125rem;
	}

	/* Specs Grid */
	.specs-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 1.25rem;
	}

	.spec-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.spec-item dt {
		font-size: 0.75rem;
		font-weight: 600;
		color: #64748b;
		text-transform: capitalize;
	}

	.spec-item dd {
		font-size: 0.9375rem;
		font-weight: 500;
		color: #1e293b;
		margin: 0;
	}

	/* Sidebar Cards */
	.sidebar-card {
		background: white;
		border-radius: 14px;
		border: 1px solid #e5e7eb;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
		overflow: hidden;
	}

	.sidebar-card .card-header {
		padding: 1rem 1.25rem;
	}

	.sidebar-card .card-header h3 {
		font-size: 0.9375rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0;
	}

	.sidebar-card .card-body {
		padding: 1.25rem;
	}

	/* Pricing Card */
	.pricing-card {
		background: linear-gradient(135deg, #EBF4FF 0%, #dbeafe 50%, #fff 100%);
		border-color: #c7d8f7;
	}

	.pricing-card .card-header {
		background: linear-gradient(135deg, #0033A0 0%, #002277 100%);
		border-bottom: none;
	}

	.pricing-card .card-header svg,
	.pricing-card .card-header h3 {
		color: white;
	}

	.price-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem 0;
		border-bottom: 1px solid rgba(0, 51, 160, 0.1);
	}

	.price-row:last-of-type {
		border-bottom: none;
	}

	.price-row .label {
		font-size: 0.875rem;
		color: #475569;
	}

	.price-row.primary .value {
		font-size: 1.5rem;
		font-weight: 800;
		color: #0f172a;
	}

	.price-row.dealer .value {
		font-size: 1.125rem;
		font-weight: 700;
		color: #0033A0;
	}

	.price-row.margin .value {
		font-size: 0.9375rem;
		font-weight: 600;
		color: #059669;
	}

	.divider {
		height: 1px;
		background: rgba(0, 51, 160, 0.15);
		margin: 0.75rem 0;
	}

	.last-update {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		font-size: 0.75rem;
		color: #64748b;
	}

	.last-update svg {
		width: 0.875rem;
		height: 0.875rem;
	}

	/* Inventory Card */
	.inventory-stat {
		text-align: center;
		padding: 1rem;
		background: linear-gradient(135deg, #f8fafc, #f1f5f9);
		border-radius: 10px;
		margin-bottom: 1rem;
	}

	.stat-value {
		font-size: 2.5rem;
		font-weight: 800;
		color: #0f172a;
		line-height: 1;
	}

	.stat-label {
		font-size: 0.75rem;
		font-weight: 600;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-top: 0.5rem;
		display: block;
	}

	.inventory-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem 0;
	}

	.inventory-row .label {
		font-size: 0.8125rem;
		color: #64748b;
	}

	.inventory-row .value {
		font-size: 0.875rem;
		font-weight: 600;
		color: #1e293b;
	}

	.alert {
		display: flex;
		align-items: flex-start;
		gap: 0.5rem;
		padding: 0.75rem;
		border-radius: 8px;
		margin-top: 1rem;
		font-size: 0.8125rem;
	}

	.alert.warning {
		background: #fffbeb;
		color: #92400e;
		border: 1px solid #fcd34d;
	}

	.alert svg {
		width: 1rem;
		height: 1rem;
		flex-shrink: 0;
		margin-top: 0.125rem;
	}

	/* Category Card */
	.category-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		padding: 0.625rem 0;
		border-bottom: 1px solid #f1f5f9;
	}

	.category-item:last-child {
		border-bottom: none;
	}

	.category-item .label {
		font-size: 0.6875rem;
		font-weight: 600;
		color: #94a3b8;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.category-item .value {
		font-size: 0.9375rem;
		font-weight: 600;
		color: #1e293b;
	}

	.category-item .value.link {
		color: #0033A0;
		text-decoration: none;
		transition: color 0.15s;
	}

	.category-item .value.link:hover {
		color: #002277;
		text-decoration: underline;
	}

	.category-item .value.brand {
		color: #0033A0;
	}

	/* Supersession Card */
	.supersession-card {
		background: #fffbeb;
		border-color: #fcd34d;
	}

	.supersession-card .card-header {
		background: linear-gradient(to bottom, #fef3c7, #fde68a);
		border-bottom-color: #f59e0b;
	}

	.supersession-card .card-header svg,
	.supersession-card .card-header h3 {
		color: #92400e;
	}

	.supersession-item {
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
		padding: 0.75rem 0;
	}

	.supersession-item:not(:last-child) {
		border-bottom: 1px solid rgba(245, 158, 11, 0.2);
	}

	.supersession-item .label {
		font-size: 0.6875rem;
		font-weight: 600;
		color: #92400e;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.supersession-item .value {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.9375rem;
		font-weight: 700;
		font-family: 'SF Mono', Monaco, monospace;
		color: #78350f;
		text-decoration: none;
		transition: color 0.15s;
	}

	.supersession-item .value:hover {
		color: #451a03;
	}

	.supersession-item .value svg {
		width: 1rem;
		height: 1rem;
	}

	/* Add to Cart Section */
	.add-to-cart-section {
		margin: 1rem 0;
	}

	.quantity-selector {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0;
		margin-bottom: 0.75rem;
		background: #f1f5f9;
		border-radius: 10px;
		padding: 0.25rem;
	}

	.quantity-selector button {
		width: 36px;
		height: 36px;
		border: none;
		background: white;
		color: #0033A0;
		font-size: 1.125rem;
		font-weight: 600;
		cursor: pointer;
		border-radius: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.15s;
		box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
	}

	.quantity-selector button:hover {
		background: #EBF4FF;
	}

	.quantity-selector input {
		width: 50px;
		height: 36px;
		border: none;
		background: transparent;
		text-align: center;
		font-size: 1rem;
		font-weight: 700;
		color: #1e293b;
		-moz-appearance: textfield;
	}

	.quantity-selector input::-webkit-outer-spin-button,
	.quantity-selector input::-webkit-inner-spin-button {
		-webkit-appearance: none;
		margin: 0;
	}

	.add-to-cart-btn {
		width: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		padding: 0.75rem 1rem;
		background: linear-gradient(180deg, #0040c8 0%, #002b8a 100%);
		border: 1px solid rgba(255, 255, 255, 0.15);
		border-radius: 10px;
		color: white;
		font-size: 0.8125rem;
		font-weight: 600;
		letter-spacing: 0.02em;
		cursor: pointer;
		transition: all 0.2s;
		box-shadow: 0 2px 8px rgba(0, 51, 160, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.12);
	}

	.add-to-cart-btn:hover:not(:disabled) {
		background: linear-gradient(180deg, #0052e0 0%, #0033A0 100%);
		box-shadow: 0 4px 12px rgba(0, 51, 160, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.15);
		transform: translateY(-1px);
	}

	.add-to-cart-btn:active:not(:disabled) {
		transform: translateY(0);
		box-shadow: 0 1px 4px rgba(0, 51, 160, 0.2);
	}

	.add-to-cart-btn:disabled {
		background: #e2e8f0;
		border-color: transparent;
		color: #94a3b8;
		cursor: not-allowed;
		box-shadow: none;
	}

	.add-to-cart-btn svg {
		width: 1rem;
		height: 1rem;
		opacity: 0.9;
	}

	/* Technical Documentation Card */
	.tech-docs-card .card-header {
		border-bottom-color: #059669;
	}

	.tech-docs-grid {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.tech-doc-item {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
		padding: 1rem;
		background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
		border: 1px solid #bbf7d0;
		border-radius: 12px;
		text-decoration: none;
		transition: all 0.2s;
	}

	.tech-doc-item:hover {
		border-color: #059669;
		box-shadow: 0 4px 12px rgba(5, 150, 105, 0.15);
		transform: translateY(-2px);
	}

	.doc-icon {
		width: 48px;
		height: 48px;
		background: #059669;
		border-radius: 10px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.doc-icon svg {
		width: 24px;
		height: 24px;
		color: white;
	}

	.doc-info {
		flex: 1;
		min-width: 0;
	}

	.doc-type-badge {
		display: inline-block;
		font-size: 0.625rem;
		font-weight: 700;
		color: #059669;
		background: white;
		padding: 0.125rem 0.5rem;
		border-radius: 99px;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 0.375rem;
	}

	.doc-info h4 {
		margin: 0 0 0.25rem 0;
		font-size: 0.9375rem;
		font-weight: 700;
		color: #1e293b;
	}

	.doc-summary {
		margin: 0 0 0.5rem 0;
		font-size: 0.8125rem;
		color: #64748b;
		line-height: 1.4;
	}

	.doc-meta {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.6875rem;
		color: #94a3b8;
		margin-bottom: 0.5rem;
	}

	.doc-models {
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem;
	}

	.model-tag {
		font-size: 0.625rem;
		font-weight: 600;
		color: #0033A0;
		background: white;
		padding: 0.125rem 0.375rem;
		border-radius: 4px;
		border: 1px solid #c7d8f7;
	}

	.model-tag.more {
		background: #f1f5f9;
		color: #64748b;
		border-color: #e2e8f0;
	}

	.doc-download {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
		padding: 0.75rem;
		background: #059669;
		border-radius: 10px;
		color: white;
		flex-shrink: 0;
	}

	.doc-download svg {
		width: 24px;
		height: 24px;
	}

	.doc-download span {
		font-size: 0.625rem;
		font-weight: 700;
		letter-spacing: 0.05em;
	}

	/* Manufacturing Grid */
	.manufacturing-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
		gap: 1rem;
	}

	.mfg-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.mfg-item.full-width {
		grid-column: 1 / -1;
	}

	.mfg-label {
		font-size: 0.6875rem;
		font-weight: 600;
		color: #94a3b8;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.mfg-value {
		font-size: 0.9375rem;
		font-weight: 600;
		color: #1e293b;
	}

	.mfg-value.code {
		font-family: 'SF Mono', Monaco, monospace;
		color: #0033A0;
	}

	.certifications {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		margin-top: 0.25rem;
	}

	.cert-badge {
		font-size: 0.75rem;
		font-weight: 600;
		color: #059669;
		background: #ecfdf5;
		padding: 0.375rem 0.75rem;
		border-radius: 6px;
		border: 1px solid #bbf7d0;
	}

	/* Fitment Guide */
	.fitment-header {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 0.75rem;
		margin-bottom: 1.25rem;
		padding-bottom: 1rem;
		border-bottom: 1px solid #f1f5f9;
	}

	.difficulty-badge {
		padding: 0.5rem 1rem;
		border-radius: 8px;
		font-size: 0.8125rem;
		font-weight: 700;
	}

	.difficulty-easy {
		background: #ecfdf5;
		color: #059669;
		border: 1px solid #bbf7d0;
	}

	.difficulty-intermediate {
		background: #fefce8;
		color: #ca8a04;
		border: 1px solid #fde047;
	}

	.difficulty-advanced {
		background: #fff7ed;
		color: #ea580c;
		border: 1px solid #fdba74;
	}

	.difficulty-professional {
		background: #fef2f2;
		color: #dc2626;
		border: 1px solid #fca5a5;
	}

	.install-time {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		font-size: 0.875rem;
		color: #64748b;
	}

	.install-time svg {
		width: 1rem;
		height: 1rem;
	}

	.pro-recommended {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.5rem 0.75rem;
		background: #fef2f2;
		color: #dc2626;
		border-radius: 6px;
		font-size: 0.75rem;
		font-weight: 600;
	}

	.pro-recommended svg {
		width: 1rem;
		height: 1rem;
	}

	.tools-section h4,
	.special-instructions h4 {
		font-size: 0.75rem;
		font-weight: 700;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin: 0 0 0.75rem 0;
	}

	.tools-list {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.tool-tag {
		font-size: 0.8125rem;
		font-weight: 500;
		color: #475569;
		background: #f8fafc;
		padding: 0.375rem 0.75rem;
		border-radius: 6px;
		border: 1px solid #e2e8f0;
	}

	.special-instructions {
		margin-top: 1.25rem;
		padding-top: 1rem;
		border-top: 1px solid #f1f5f9;
	}

	.special-instructions p {
		margin: 0;
		font-size: 0.9375rem;
		color: #475569;
		line-height: 1.6;
	}

	/* Packaging Grid */
	.packaging-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
		gap: 1rem;
	}

	.pkg-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.pkg-item.hazmat {
		grid-column: 1 / -1;
	}

	.pkg-label {
		font-size: 0.6875rem;
		font-weight: 600;
		color: #94a3b8;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.pkg-value {
		font-size: 0.9375rem;
		font-weight: 600;
		color: #1e293b;
	}

	.pkg-value.code {
		font-family: 'SF Mono', Monaco, monospace;
		font-size: 0.8125rem;
		color: #64748b;
	}

	.hazmat-badge {
		display: inline-block;
		background: #fef2f2;
		color: #dc2626;
		padding: 0.375rem 0.75rem;
		border-radius: 6px;
		border: 1px solid #fca5a5;
		font-size: 0.8125rem;
	}

	/* Sales Performance */
	.sales-card .card-header {
		border-bottom-color: #8b5cf6;
	}

	.internal-badge {
		margin-left: auto;
		font-size: 0.625rem;
		font-weight: 600;
		color: #8b5cf6;
		background: #f5f3ff;
		padding: 0.25rem 0.625rem;
		border-radius: 99px;
	}

	.sales-stats {
		display: flex;
		gap: 2rem;
		margin-bottom: 1.5rem;
		padding-bottom: 1.25rem;
		border-bottom: 1px solid #f1f5f9;
	}

	.sales-stat {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.stat-number {
		font-size: 1.75rem;
		font-weight: 800;
		color: #1e293b;
		line-height: 1;
	}

	.stat-number.rating {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		color: #f59e0b;
	}

	.stat-number.rating svg {
		width: 1.25rem;
		height: 1.25rem;
	}

	.stat-number.return-rate {
		color: #059669;
	}

	.sales-stat .stat-label {
		font-size: 0.75rem;
		color: #64748b;
	}

	.top-regions h4 {
		font-size: 0.75rem;
		font-weight: 700;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin: 0 0 0.75rem 0;
	}

	.regions-list {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.region-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 0.875rem;
		background: #f8fafc;
		border-radius: 8px;
		border: 1px solid #e2e8f0;
	}

	.region-rank {
		font-size: 0.75rem;
		font-weight: 700;
		color: #8b5cf6;
	}

	.region-name {
		font-size: 0.875rem;
		font-weight: 500;
		color: #1e293b;
	}

	/* Related Products Section */
	.related-section {
		background: white;
		border-radius: 14px;
		border: 1px solid #e5e7eb;
		padding: 1.5rem;
		margin-bottom: 2rem;
	}

	.section-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 1.25rem;
	}

	.section-header svg {
		width: 1.5rem;
		height: 1.5rem;
		color: #0033A0;
	}

	.section-header h2 {
		font-size: 1.125rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0;
	}

	.related-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 1rem;
	}

	.related-card {
		display: flex;
		flex-direction: column;
		padding: 1.25rem;
		background: #f8fafc;
		border: 1px solid #e5e7eb;
		border-radius: 10px;
		text-decoration: none;
		transition: all 0.2s;
		animation: fadeInUp 0.3s ease-out both;
	}

	.related-card:hover {
		border-color: #0033A0;
		background: #EBF4FF;
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 51, 160, 0.1);
	}

	.related-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.625rem;
	}

	.related-part-number {
		font-size: 0.8125rem;
		font-weight: 700;
		font-family: 'SF Mono', Monaco, monospace;
		color: #0033A0;
	}

	.badge.small {
		font-size: 0.625rem;
		padding: 0.25rem 0.5rem;
	}

	.related-card h4 {
		font-size: 0.9375rem;
		font-weight: 600;
		color: #1e293b;
		margin: 0 0 0.375rem 0;
		line-height: 1.4;
	}

	.related-category {
		font-size: 0.75rem;
		color: #64748b;
		margin: 0 0 auto 0;
	}

	.related-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 1rem;
		padding-top: 0.75rem;
		border-top: 1px solid #e5e7eb;
	}

	.related-price {
		font-size: 0.9375rem;
		font-weight: 700;
		color: #0f172a;
	}

	.related-footer svg {
		width: 1rem;
		height: 1rem;
		color: #94a3b8;
		transition: transform 0.2s;
	}

	.related-card:hover .related-footer svg {
		color: #0033A0;
		transform: translateX(4px);
	}

	/* Responsive */
	@media (max-width: 1024px) {
		.content-grid {
			grid-template-columns: 1fr;
		}

		.sidebar {
			order: -1;
			display: grid;
			grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		}
	}

	@media (max-width: 768px) {
		.top-nav {
			flex-direction: column;
			align-items: flex-start;
		}

		.product-header {
			flex-direction: column;
		}

		.header-content {
			flex-direction: column;
			align-items: flex-start;
		}

		.page-icon {
			width: 3rem;
			height: 3rem;
		}

		.page-icon svg {
			width: 1.25rem;
			height: 1.25rem;
		}

		.header-text h1 {
			font-size: 1.375rem;
		}

		.breadcrumb {
			flex-wrap: wrap;
		}

		.sidebar {
			grid-template-columns: 1fr;
		}

		.related-grid {
			grid-template-columns: 1fr;
		}

		.specs-grid {
			grid-template-columns: 1fr 1fr;
		}

		/* Responsive: new sections */
		.tech-doc-item {
			flex-direction: column;
		}

		.doc-download {
			width: 100%;
			flex-direction: row;
			justify-content: center;
		}

		.manufacturing-grid {
			grid-template-columns: 1fr 1fr;
		}

		.fitment-header {
			flex-direction: column;
			align-items: flex-start;
		}

		.sales-stats {
			flex-direction: column;
			gap: 1rem;
		}

		.packaging-grid {
			grid-template-columns: 1fr 1fr;
		}
	}
</style>
