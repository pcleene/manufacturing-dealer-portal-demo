<script lang="ts">
	import { onMount } from 'svelte';
	import { Chart, registerables } from 'chart.js';
	import {
		getProductDashboardStats,
		getClaimDashboardStats,
		getDashboardClaimsTrend,
		getTopDealers,
		formatCurrency,
		formatNumber,
		type ProductDashboardStats,
		type ClaimDashboardStats,
		type ClaimsTrend,
		type DealerClaimStats
	} from '$lib/api';

	// Register Chart.js components
	Chart.register(...registerables);

	let productStats: ProductDashboardStats | null = null;
	let claimStats: ClaimDashboardStats | null = null;
	let claimsTrend: ClaimsTrend[] = [];
	let topDealers: DealerClaimStats[] = [];
	let loading = true;
	let error = '';

	// Chart references
	let statusChartCanvas: HTMLCanvasElement;
	let failureChartCanvas: HTMLCanvasElement;
	let trendChartCanvas: HTMLCanvasElement;
	let categoryChartCanvas: HTMLCanvasElement;
	let stockChartCanvas: HTMLCanvasElement;

	let statusChart: Chart | null = null;
	let failureChart: Chart | null = null;
	let trendChart: Chart | null = null;
	let categoryChart: Chart | null = null;
	let stockChart: Chart | null = null;

	const statusColors: Record<string, string> = {
		'Draft': '#94a3b8',
		'Pending Review': '#fbbf24',
		'Under Review': '#3b82f6',
		'Awaiting Parts': '#f97316',
		'Approved': '#22c55e',
		'Rejected': '#ef4444',
		'Paid': '#8b5cf6',
		'Closed': '#64748b'
	};

	const failureCategoryColors = [
		'#ef4444', '#f97316', '#fbbf24', '#22c55e', '#14b8a6',
		'#3b82f6', '#8b5cf6', '#ec4899', '#6366f1', '#0ea5e9',
		'#84cc16'
	];

	const categoryColors = [
		'#0033A0', '#E60012', '#3b82f6', '#22c55e', '#f59e0b',
		'#8b5cf6', '#ec4899', '#14b8a6', '#6366f1'
	];

	onMount(async () => {
		try {
			const [productData, claimData, trendData, dealersData] = await Promise.all([
				getProductDashboardStats(),
				getClaimDashboardStats(),
				getDashboardClaimsTrend(12),
				getTopDealers(10)
			]);
			productStats = productData;
			claimStats = claimData;
			claimsTrend = trendData.trend || [];
			topDealers = dealersData;

			// Initialize charts after data loads
			setTimeout(() => {
				initCharts();
			}, 100);
		} catch (err: any) {
			error = err.message || 'Failed to load dashboard statistics';
			console.error('Dashboard error:', err);
		} finally {
			loading = false;
		}
	});

	function initCharts() {
		if (claimStats) {
			// Claims by Status Chart
			if (statusChartCanvas && claimStats.byStatus?.length) {
				const labels = claimStats.byStatus.map(s => s._id);
				const data = claimStats.byStatus.map(s => s.count);
				const colors = labels.map(l => statusColors[l] || '#64748b');

				statusChart = new Chart(statusChartCanvas, {
					type: 'bar',
					data: {
						labels,
						datasets: [{
							label: 'Claims',
							data,
							backgroundColor: colors,
							borderRadius: 6,
							barThickness: 28
						}]
					},
					options: {
						indexAxis: 'y',
						responsive: true,
						maintainAspectRatio: false,
						plugins: {
							legend: { display: false }
						},
						scales: {
							x: { 
								grid: { display: false },
								ticks: { font: { size: 11 } }
							},
							y: { 
								grid: { display: false },
								ticks: { font: { size: 11 } }
							}
						}
					}
				});
			}

			// Claims by Failure Category Chart
			if (failureChartCanvas && claimStats.byFailureCategory?.length) {
				const labels = claimStats.byFailureCategory.slice(0, 8).map(s => s._id);
				const data = claimStats.byFailureCategory.slice(0, 8).map(s => s.count);

				failureChart = new Chart(failureChartCanvas, {
					type: 'doughnut',
					data: {
						labels,
						datasets: [{
							data,
							backgroundColor: failureCategoryColors.slice(0, data.length),
							borderWidth: 0,
							hoverOffset: 8
						}]
					},
					options: {
						responsive: true,
						maintainAspectRatio: false,
						plugins: {
							legend: {
								position: 'right',
								labels: { 
									usePointStyle: true, 
									padding: 12,
									font: { size: 11 }
								}
							}
						},
						cutout: '60%'
					}
				});
			}
		}

		// Claims Trend Chart
		if (trendChartCanvas && claimsTrend.length) {
			const sortedTrend = [...claimsTrend].sort((a, b) => a.month.localeCompare(b.month));
			const labels = sortedTrend.map(t => {
				const [year, month] = t.month.split('-');
				return new Date(parseInt(year), parseInt(month) - 1).toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
			});

			trendChart = new Chart(trendChartCanvas, {
				type: 'line',
				data: {
					labels,
					datasets: [
						{
							label: 'Total Claims',
							data: sortedTrend.map(t => t.totalClaims),
							borderColor: '#0033A0',
							backgroundColor: 'rgba(0, 51, 160, 0.1)',
							fill: true,
							tension: 0.3,
							pointRadius: 4,
							pointHoverRadius: 6
						},
						{
							label: 'Approved',
							data: sortedTrend.map(t => t.approvedCount),
							borderColor: '#22c55e',
							backgroundColor: 'transparent',
							tension: 0.3,
							pointRadius: 3,
							borderDash: [5, 5]
						}
					]
				},
				options: {
					responsive: true,
					maintainAspectRatio: false,
					plugins: {
						legend: {
							position: 'top',
							labels: { 
								usePointStyle: true,
								padding: 16,
								font: { size: 11 }
							}
						}
					},
					scales: {
						x: { grid: { display: false } },
						y: { 
							beginAtZero: true,
							grid: { color: 'rgba(0,0,0,0.05)' }
						}
					}
				}
			});
		}

		// Product Category Chart
		if (categoryChartCanvas && productStats?.byCategory?.length) {
			const labels = productStats.byCategory.slice(0, 8).map(c => c._id);
			const data = productStats.byCategory.slice(0, 8).map(c => c.count);

			categoryChart = new Chart(categoryChartCanvas, {
				type: 'pie',
				data: {
					labels,
					datasets: [{
						data,
						backgroundColor: categoryColors.slice(0, data.length),
						borderWidth: 2,
						borderColor: '#fff'
					}]
				},
				options: {
					responsive: true,
					maintainAspectRatio: false,
					plugins: {
						legend: {
							position: 'right',
							labels: { 
								usePointStyle: true, 
								padding: 10,
								font: { size: 10 }
							}
						}
					}
				}
			});
		}

		// Stock Status Chart
		if (stockChartCanvas && productStats?.byAvailabilityStatus?.length) {
			const stockColors: Record<string, string> = {
				'In Stock': '#22c55e',
				'Low Stock': '#f59e0b',
				'Out of Stock': '#ef4444'
			};
			const labels = productStats.byAvailabilityStatus.map(s => s._id);
			const data = productStats.byAvailabilityStatus.map(s => s.count);
			const colors = labels.map(l => stockColors[l] || '#64748b');

			stockChart = new Chart(stockChartCanvas, {
				type: 'doughnut',
				data: {
					labels,
					datasets: [{
						data,
						backgroundColor: colors,
						borderWidth: 0
					}]
				},
				options: {
					responsive: true,
					maintainAspectRatio: false,
					plugins: {
						legend: {
							position: 'bottom',
							labels: { 
								usePointStyle: true,
								padding: 12,
								font: { size: 11 }
							}
						}
					},
					cutout: '70%'
				}
			});
		}
	}

	// Cleanup charts on destroy
	import { onDestroy } from 'svelte';
	onDestroy(() => {
		statusChart?.destroy();
		failureChart?.destroy();
		trendChart?.destroy();
		categoryChart?.destroy();
		stockChart?.destroy();
	});
</script>

<svelte:head>
	<title>OEMPartner Dealer Portal - Dashboard</title>
</svelte:head>

<div class="dashboard">
	<!-- Welcome Section -->
	<div class="welcome-section">
		<div class="welcome-content">
			<div class="welcome-icon">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<rect x="3" y="3" width="7" height="9" rx="1"/>
					<rect x="14" y="3" width="7" height="5" rx="1"/>
					<rect x="14" y="12" width="7" height="9" rx="1"/>
					<rect x="3" y="16" width="7" height="5" rx="1"/>
				</svg>
			</div>
			<div>
				<h1 class="welcome-title">Dashboard Overview</h1>
				<p class="welcome-subtitle">
					Comprehensive analytics for OEMPartner warranty claims and product catalog
				</p>
			</div>
		</div>
		<div class="welcome-decoration"></div>
	</div>

	{#if loading}
		<div class="loading-state">
			<div class="loading-spinner">
				<svg viewBox="0 0 24 24" fill="none">
					<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-opacity="0.25"/>
					<path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
				</svg>
			</div>
			<p class="loading-text">Loading dashboard data...</p>
		</div>
	{:else if error}
		<div class="error-state">
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<circle cx="12" cy="12" r="10"/>
				<path d="m15 9-6 6M9 9l6 6"/>
			</svg>
			<p>{error}</p>
		</div>
	{:else}
		<!-- Primary Stats Grid -->
		<div class="stats-grid">
			<div class="stat-card stat-products">
				<div class="stat-icon">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
					</svg>
				</div>
				<div class="stat-content">
					<span class="stat-label">Total Products</span>
					<span class="stat-value">{productStats?.totalProducts ? formatNumber(productStats.totalProducts) : '-'}</span>
				</div>
				<div class="stat-accent"></div>
			</div>

			<div class="stat-card stat-warning">
				<div class="stat-icon">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
					</svg>
				</div>
				<div class="stat-content">
					<span class="stat-label">Low Stock Alerts</span>
					<span class="stat-value">{productStats?.lowStockAlerts !== undefined ? formatNumber(productStats.lowStockAlerts) : '-'}</span>
				</div>
				<div class="stat-accent"></div>
			</div>

			<div class="stat-card stat-claims">
				<div class="stat-icon">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
					</svg>
				</div>
				<div class="stat-content">
					<span class="stat-label">Total Claims</span>
					<span class="stat-value">{claimStats?.totalClaims ? formatNumber(claimStats.totalClaims) : '-'}</span>
				</div>
				<div class="stat-accent"></div>
			</div>

			<div class="stat-card stat-success">
				<div class="stat-icon">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
					</svg>
				</div>
				<div class="stat-content">
					<span class="stat-label">Claims This Month</span>
					<span class="stat-value">{claimStats?.thisMonth?.totalValue ? formatCurrency(claimStats.thisMonth.totalValue) : '-'}</span>
					{#if claimStats?.thisMonth?.count}
						<span class="stat-sub">{claimStats.thisMonth.count} claims submitted</span>
					{/if}
				</div>
				<div class="stat-accent"></div>
			</div>
		</div>

		<!-- Secondary Metrics -->
		<div class="metrics-row">
			<div class="metric-card">
				<div class="metric-header">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<circle cx="12" cy="12" r="10"/>
						<path d="M12 6v6l4 2"/>
					</svg>
					<span>Avg Processing Time</span>
				</div>
				<div class="metric-value">
					{claimStats?.processing?.avgProcessingDays ? claimStats.processing.avgProcessingDays.toFixed(1) : '-'}
					<span class="metric-unit">days</span>
				</div>
			</div>

			<div class="metric-card">
				<div class="metric-header">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M3 3v18h18"/>
						<path d="m19 9-5 5-4-4-3 3"/>
					</svg>
					<span>Rejection Rate</span>
				</div>
				<div class="metric-value">
					{claimStats?.rejection?.rejectionRate !== undefined ? (claimStats.rejection.rejectionRate * 100).toFixed(1) : '-'}
					<span class="metric-unit">%</span>
				</div>
			</div>

			<div class="metric-card metric-danger">
				<div class="metric-header">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
					</svg>
					<span>SLA Breached</span>
				</div>
				<div class="metric-value">
					{claimStats?.slaBreached !== undefined ? formatNumber(claimStats.slaBreached) : '-'}
				</div>
			</div>

			<div class="metric-card metric-highlight">
				<div class="metric-header">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
					</svg>
					<span>Total Claim Value</span>
				</div>
				<div class="metric-value metric-currency">
					{claimStats?.values?.totalClaimValue ? formatCurrency(claimStats.values.totalClaimValue) : '-'}
				</div>
			</div>
		</div>

		<!-- Charts Row 1: Claims Analysis -->
		<div class="section-header">
			<h2>📊 Claims Analysis</h2>
		</div>
		<div class="charts-row">
			<div class="chart-card">
				<h3 class="chart-title">Claims by Status</h3>
				<div class="chart-container chart-status">
					<canvas bind:this={statusChartCanvas}></canvas>
				</div>
			</div>

			<div class="chart-card">
				<h3 class="chart-title">Failure Categories</h3>
				<div class="chart-container chart-doughnut">
					<canvas bind:this={failureChartCanvas}></canvas>
				</div>
			</div>
		</div>

		<!-- Claims Trend Chart -->
		<div class="chart-card chart-full">
			<h3 class="chart-title">Monthly Claims Trend (Last 12 Months)</h3>
			<div class="chart-container chart-trend">
				<canvas bind:this={trendChartCanvas}></canvas>
			</div>
		</div>

		<!-- Regional Performance & Top Dealers -->
		<div class="section-header">
			<h2>🌏 Regional & Dealer Performance</h2>
		</div>
		<div class="tables-row">
			<!-- Regional Performance -->
			{#if claimStats?.byDealerRegion?.length}
			<div class="table-card">
				<h3 class="table-title">Claims by Region</h3>
				<div class="table-scroll">
					<table class="data-table">
						<thead>
							<tr>
								<th>Region</th>
								<th class="text-right">Claims</th>
								<th class="text-right">Total Value</th>
							</tr>
						</thead>
						<tbody>
							{#each claimStats.byDealerRegion.slice(0, 10) as region}
							<tr>
								<td class="region-name">{region._id}</td>
								<td class="text-right">{formatNumber(region.count)}</td>
								<td class="text-right">{formatCurrency(region.totalValue)}</td>
							</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
			{/if}

			<!-- Top Dealers -->
			<div class="table-card table-wide">
				<h3 class="table-title">Top Dealers by Claims</h3>
				<div class="table-scroll">
					<table class="data-table">
						<thead>
							<tr>
								<th>#</th>
								<th>Dealer</th>
								<th>Region</th>
								<th class="text-right">Claims</th>
								<th class="text-right">Value</th>
								<th class="text-right">Approval</th>
							</tr>
						</thead>
						<tbody>
							{#each topDealers.slice(0, 10) as dealer, i}
							<tr>
								<td class="rank">
									{#if i === 0}🥇{:else if i === 1}🥈{:else if i === 2}🥉{:else}{i + 1}{/if}
								</td>
								<td class="dealer-name">{dealer.dealerName}</td>
								<td class="region-badge">{dealer.dealerRegion}</td>
								<td class="text-right">{formatNumber(dealer.totalClaims)}</td>
								<td class="text-right">{formatCurrency(dealer.totalClaimValue)}</td>
								<td class="text-right">
									<span class="approval-rate" class:high={dealer.approvalRate >= 0.8} class:low={dealer.approvalRate < 0.6}>
										{(dealer.approvalRate * 100).toFixed(0)}%
									</span>
								</td>
							</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		</div>

		<!-- Inventory Health -->
		<div class="section-header">
			<h2>📦 Inventory Health</h2>
		</div>
		<div class="charts-row">
			<div class="chart-card">
				<h3 class="chart-title">Products by Category</h3>
				<div class="chart-container chart-pie">
					<canvas bind:this={categoryChartCanvas}></canvas>
				</div>
			</div>

			<div class="chart-card">
				<h3 class="chart-title">Stock Status</h3>
				<div class="chart-container chart-stock">
					<canvas bind:this={stockChartCanvas}></canvas>
				</div>
				{#if productStats?.inventoryValue}
				<div class="inventory-summary">
					<div class="inv-stat">
						<span class="inv-label">Total Units</span>
						<span class="inv-value">{formatNumber(productStats.inventoryValue.totalUnits)}</span>
					</div>
					<div class="inv-stat">
						<span class="inv-label">Inventory Value</span>
						<span class="inv-value">{formatCurrency(productStats.inventoryValue.totalValue)}</span>
					</div>
					<div class="inv-stat">
						<span class="inv-label">Avg Unit Price</span>
						<span class="inv-value">{formatCurrency(productStats.inventoryValue.avgUnitPrice)}</span>
					</div>
				</div>
				{/if}
			</div>
		</div>

		<!-- Quick Links -->
		<div class="quick-links">
			<h2 class="section-title">Quick Access</h2>
			<div class="links-grid">
				<a href="/products" class="link-card link-products">
					<div class="link-icon">
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
						</svg>
					</div>
					<div class="link-content">
						<h3>Product Catalog</h3>
						<p>Search parts, accessories, and consumables</p>
					</div>
					<div class="link-arrow">
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
							<path d="m9 18 6-6-6-6"/>
						</svg>
					</div>
				</a>

				<a href="/claims" class="link-card link-claims">
					<div class="link-icon">
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
						</svg>
					</div>
					<div class="link-content">
						<h3>Warranty Claims</h3>
						<p>Submit and track warranty claims</p>
					</div>
					<div class="link-arrow">
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
							<path d="m9 18 6-6-6-6"/>
						</svg>
					</div>
				</a>
			</div>
		</div>

		<!-- Last Updated -->
		{#if productStats?.refreshedAt || claimStats?.refreshedAt}
			<div class="last-updated">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<circle cx="12" cy="12" r="10"/>
					<path d="M12 6v6l4 2"/>
				</svg>
				<span>Last updated: {new Date(productStats?.refreshedAt || claimStats?.refreshedAt || '').toLocaleString('en-MY')}</span>
			</div>
		{/if}
	{/if}
</div>

<style>
	.dashboard {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	/* Welcome Section */
	.welcome-section {
		background: linear-gradient(135deg, #0033A0 0%, #001a5c 100%);
		border-radius: 16px;
		padding: 2rem;
		position: relative;
		overflow: hidden;
	}

	.welcome-content {
		display: flex;
		align-items: center;
		gap: 1rem;
		position: relative;
		z-index: 1;
	}

	.welcome-icon {
		width: 3.5rem;
		height: 3.5rem;
		background: rgba(255, 255, 255, 0.15);
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.welcome-icon svg {
		width: 1.5rem;
		height: 1.5rem;
		color: white;
	}

	.welcome-title {
		font-size: 1.75rem;
		font-weight: 800;
		color: white;
		margin: 0;
		letter-spacing: -0.025em;
	}

	.welcome-subtitle {
		font-size: 0.9375rem;
		color: rgba(255, 255, 255, 0.75);
		margin-top: 0.25rem;
	}

	.welcome-decoration {
		position: absolute;
		top: -50%;
		right: -10%;
		width: 300px;
		height: 300px;
		background: radial-gradient(circle, rgba(230, 0, 18, 0.2) 0%, transparent 70%);
		border-radius: 50%;
	}

	/* Loading & Error States */
	.loading-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 300px;
		gap: 1rem;
	}

	.loading-spinner svg {
		width: 3rem;
		height: 3rem;
		color: #0033A0;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.loading-text {
		color: #64748b;
		font-size: 0.9375rem;
	}

	.error-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 200px;
		gap: 0.75rem;
		background: #fef2f2;
		border: 1px solid #fecaca;
		border-radius: 12px;
		padding: 2rem;
		color: #dc2626;
	}

	.error-state svg {
		width: 2rem;
		height: 2rem;
	}

	/* Stats Grid */
	.stats-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1rem;
	}

	@media (max-width: 1024px) {
		.stats-grid { grid-template-columns: repeat(2, 1fr); }
	}

	@media (max-width: 640px) {
		.stats-grid { grid-template-columns: 1fr; }
	}

	.stat-card {
		background: white;
		border-radius: 12px;
		padding: 1.25rem;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		position: relative;
		overflow: hidden;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
		border: 1px solid #e5e7eb;
		transition: all 0.2s;
	}

	.stat-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
	}

	.stat-icon {
		width: 2.25rem;
		height: 2.25rem;
		border-radius: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.stat-icon svg {
		width: 1.125rem;
		height: 1.125rem;
	}

	.stat-products .stat-icon { background: linear-gradient(135deg, #EBF4FF 0%, #dbeafe 100%); color: #0033A0; }
	.stat-warning .stat-icon { background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); color: #b45309; }
	.stat-claims .stat-icon { background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%); color: #7c3aed; }
	.stat-success .stat-icon { background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); color: #059669; }

	.stat-content { display: flex; flex-direction: column; gap: 0.125rem; }
	.stat-label { font-size: 0.75rem; font-weight: 500; color: #64748b; text-transform: uppercase; letter-spacing: 0.025em; }
	.stat-value { font-size: 1.5rem; font-weight: 800; color: #0f172a; letter-spacing: -0.025em; }
	.stat-sub { font-size: 0.6875rem; color: #94a3b8; }

	.stat-accent { position: absolute; top: 0; left: 0; right: 0; height: 3px; }
	.stat-products .stat-accent { background: linear-gradient(90deg, #0033A0, #0066ff); }
	.stat-warning .stat-accent { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
	.stat-claims .stat-accent { background: linear-gradient(90deg, #7c3aed, #a855f7); }
	.stat-success .stat-accent { background: linear-gradient(90deg, #059669, #10b981); }

	/* Metrics Row */
	.metrics-row {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1rem;
	}

	@media (max-width: 1024px) {
		.metrics-row { grid-template-columns: repeat(2, 1fr); }
	}

	@media (max-width: 640px) {
		.metrics-row { grid-template-columns: 1fr; }
	}

	.metric-card {
		background: white;
		border-radius: 12px;
		padding: 1rem 1.25rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
		border: 1px solid #e5e7eb;
	}

	.metric-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		color: #64748b;
		font-size: 0.75rem;
		font-weight: 500;
		margin-bottom: 0.5rem;
	}

	.metric-header svg { width: 0.875rem; height: 0.875rem; }
	.metric-value { font-size: 1.75rem; font-weight: 800; color: #0f172a; letter-spacing: -0.025em; }
	.metric-unit { font-size: 0.875rem; font-weight: 500; color: #94a3b8; margin-left: 0.25rem; }
	.metric-danger .metric-value { color: #E60012; }
	.metric-highlight .metric-value { color: #0033A0; }
	.metric-currency { font-size: 1.25rem; }

	/* Section Headers */
	.section-header {
		margin-top: 1rem;
		margin-bottom: 0.5rem;
	}

	.section-header h2 {
		font-size: 1.125rem;
		font-weight: 700;
		color: #0f172a;
		margin: 0;
	}

	/* Charts */
	.charts-row {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1rem;
	}

	@media (max-width: 768px) {
		.charts-row { grid-template-columns: 1fr; }
	}

	.chart-card {
		background: white;
		border-radius: 12px;
		padding: 1.25rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
		border: 1px solid #e5e7eb;
	}

	.chart-card.chart-full {
		grid-column: 1 / -1;
	}

	.chart-title {
		font-size: 0.875rem;
		font-weight: 600;
		color: #374151;
		margin: 0 0 1rem 0;
	}

	.chart-container {
		position: relative;
	}

	.chart-status { height: 220px; }
	.chart-doughnut { height: 220px; }
	.chart-trend { height: 280px; }
	.chart-pie { height: 200px; }
	.chart-stock { height: 180px; }

	/* Tables */
	.tables-row {
		display: grid;
		grid-template-columns: 1fr 2fr;
		gap: 1rem;
	}

	@media (max-width: 1024px) {
		.tables-row { grid-template-columns: 1fr; }
	}

	.table-card {
		background: white;
		border-radius: 12px;
		padding: 1.25rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
		border: 1px solid #e5e7eb;
	}

	.table-title {
		font-size: 0.875rem;
		font-weight: 600;
		color: #374151;
		margin: 0 0 1rem 0;
	}

	.table-scroll {
		overflow-x: auto;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.8125rem;
	}

	.data-table th {
		text-align: left;
		padding: 0.5rem 0.75rem;
		border-bottom: 2px solid #e5e7eb;
		color: #64748b;
		font-weight: 600;
		font-size: 0.6875rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.data-table td {
		padding: 0.625rem 0.75rem;
		border-bottom: 1px solid #f1f5f9;
		color: #374151;
	}

	.data-table tr:hover td {
		background: #f8fafc;
	}

	.text-right { text-align: right; }
	.rank { font-weight: 600; width: 2rem; }
	.dealer-name { font-weight: 500; max-width: 180px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.region-name { font-weight: 500; }
	.region-badge { 
		color: #6366f1; 
		font-size: 0.75rem;
		background: #eef2ff;
		padding: 0.125rem 0.5rem;
		border-radius: 4px;
		display: inline-block;
	}

	.approval-rate {
		font-weight: 600;
		padding: 0.125rem 0.375rem;
		border-radius: 4px;
		font-size: 0.75rem;
	}

	.approval-rate.high { background: #dcfce7; color: #166534; }
	.approval-rate.low { background: #fee2e2; color: #991b1b; }

	/* Inventory Summary */
	.inventory-summary {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.75rem;
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid #e5e7eb;
	}

	.inv-stat {
		display: flex;
		flex-direction: column;
		gap: 0.125rem;
		text-align: center;
	}

	.inv-label {
		font-size: 0.6875rem;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.025em;
	}

	.inv-value {
		font-size: 0.875rem;
		font-weight: 700;
		color: #0f172a;
	}

	/* Quick Links */
	.quick-links {
		margin-top: 0.5rem;
	}

	.section-title {
		font-size: 1.125rem;
		font-weight: 700;
		color: #0f172a;
		margin-bottom: 1rem;
	}

	.links-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1rem;
	}

	@media (max-width: 768px) {
		.links-grid { grid-template-columns: 1fr; }
	}

	.link-card {
		display: flex;
		align-items: center;
		gap: 1rem;
		background: white;
		border-radius: 12px;
		padding: 1.25rem;
		text-decoration: none;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
		border: 2px solid #e5e7eb;
		transition: all 0.2s;
	}

	.link-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
	}

	.link-products:hover { border-color: #0033A0; }
	.link-claims:hover { border-color: #7c3aed; }

	.link-icon {
		width: 2.75rem;
		height: 2.75rem;
		border-radius: 10px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.link-icon svg { width: 1.25rem; height: 1.25rem; }
	.link-products .link-icon { background: linear-gradient(135deg, #EBF4FF 0%, #dbeafe 100%); color: #0033A0; }
	.link-claims .link-icon { background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%); color: #7c3aed; }

	.link-content { flex: 1; }
	.link-content h3 { font-size: 0.9375rem; font-weight: 600; color: #0f172a; margin: 0; }
	.link-content p { font-size: 0.75rem; color: #64748b; margin-top: 0.125rem; }

	.link-arrow {
		width: 1.75rem;
		height: 1.75rem;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		background: #f1f5f9;
		color: #64748b;
		transition: all 0.2s;
	}

	.link-arrow svg { width: 0.875rem; height: 0.875rem; }
	.link-products:hover .link-arrow { background: #0033A0; color: white; }
	.link-claims:hover .link-arrow { background: #7c3aed; color: white; }

	/* Last Updated */
	.last-updated {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		font-size: 0.75rem;
		color: #94a3b8;
		margin-top: 0.5rem;
	}

	.last-updated svg { width: 0.75rem; height: 0.75rem; }
</style>
