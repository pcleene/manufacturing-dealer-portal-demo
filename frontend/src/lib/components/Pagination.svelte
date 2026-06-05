<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let hasMore: boolean = false;
	export let totalCount: number | undefined = undefined;
	export let currentPage: number = 1;
	export let loading: boolean = false;
	export let pageSize: number = 20;

	const dispatch = createEventDispatcher();

	$: totalPages = totalCount ? Math.ceil(totalCount / pageSize) : undefined;
	$: startItem = (currentPage - 1) * pageSize + 1;
	$: endItem = totalCount 
		? Math.min(currentPage * pageSize, totalCount) 
		: currentPage * pageSize;

	function handleNext() {
		if (hasMore && !loading) {
			dispatch('next');
		}
	}

	function handlePrevious() {
		if (currentPage > 1 && !loading) {
			dispatch('previous');
		}
	}
</script>

{#if totalCount && totalCount > 0}
	<div class="pagination-container">
		<!-- Results Summary -->
		<div class="results-summary">
			<span class="results-text">
				Showing <span class="highlight">{startItem.toLocaleString()}</span>–<span class="highlight">{endItem.toLocaleString()}</span>
				{#if totalCount}
					of <span class="highlight">{totalCount.toLocaleString()}</span> results
				{/if}
			</span>
		</div>

		<!-- Page Navigation -->
		<div class="page-nav">
			<button
				on:click={handlePrevious}
				disabled={currentPage === 1 || loading}
				class="nav-btn"
				aria-label="Previous page"
			>
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
					<path d="m15 18-6-6 6-6"/>
				</svg>
				<span>Previous</span>
			</button>

			<div class="page-indicator">
				<span class="page-current">{currentPage}</span>
				{#if totalPages}
					<span class="page-separator">of</span>
					<span class="page-total">{totalPages}</span>
				{/if}
			</div>

			<button
				on:click={handleNext}
				disabled={!hasMore || loading}
				class="nav-btn nav-btn-primary"
				aria-label="Next page"
			>
				<span>Next</span>
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
					<path d="m9 18 6-6-6-6"/>
				</svg>
			</button>
		</div>

		<!-- Loading Indicator -->
		{#if loading}
			<div class="loading-indicator">
				<svg class="loading-spinner" viewBox="0 0 24 24" fill="none">
					<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-opacity="0.25"/>
					<path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
				</svg>
			</div>
		{/if}
	</div>
{/if}

<style>
	.pagination-container {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		margin-top: 1.5rem;
		padding: 1rem 1.25rem;
		background: white;
		border-radius: 12px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
		border: 1px solid #e5e7eb;
	}

	.results-summary {
		display: flex;
		align-items: center;
	}

	.results-text {
		font-size: 0.875rem;
		color: #6b7280;
	}

	.results-text .highlight {
		font-weight: 600;
		color: #1e293b;
	}

	.page-nav {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.nav-btn {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.5rem 1rem;
		font-size: 0.875rem;
		font-weight: 500;
		color: #374151;
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		transition: all 0.2s;
	}

	.nav-btn:hover:not(:disabled) {
		background: #f3f4f6;
		border-color: #d1d5db;
	}

	.nav-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.nav-btn svg {
		width: 1rem;
		height: 1rem;
	}

	.nav-btn-primary {
		background: linear-gradient(135deg, #0033A0 0%, #002277 100%);
		color: white;
		border-color: transparent;
		box-shadow: 0 2px 4px rgba(0, 51, 160, 0.2);
	}

	.nav-btn-primary:hover:not(:disabled) {
		background: linear-gradient(135deg, #002277 0%, #001a5c 100%);
		border-color: transparent;
		transform: translateY(-1px);
		box-shadow: 0 4px 8px rgba(0, 51, 160, 0.25);
	}

	.nav-btn-primary:disabled {
		background: #94a3b8;
		box-shadow: none;
	}

	.page-indicator {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0 0.75rem;
		font-size: 0.875rem;
	}

	.page-current {
		font-weight: 700;
		color: #0033A0;
		background: #EBF4FF;
		padding: 0.25rem 0.625rem;
		border-radius: 6px;
		min-width: 2rem;
		text-align: center;
	}

	.page-separator {
		color: #9ca3af;
	}

	.page-total {
		font-weight: 500;
		color: #6b7280;
	}

	.loading-indicator {
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.loading-spinner {
		width: 1.25rem;
		height: 1.25rem;
		color: #0033A0;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	/* Mobile Responsive */
	@media (max-width: 640px) {
		.pagination-container {
			flex-direction: column;
			gap: 0.75rem;
		}

		.nav-btn span {
			display: none;
		}

		.nav-btn {
			padding: 0.5rem 0.75rem;
		}
	}
</style>
