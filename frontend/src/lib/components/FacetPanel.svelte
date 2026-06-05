<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let facets: Array<{
		field: string;      // Display label (e.g., "Category")
		fieldKey: string;   // Filter key for API (e.g., "category")
		buckets: Array<{ value: string; count: number }>;
	}> = [];

	export let selectedFilters: Record<string, string[]> = {};

	const dispatch = createEventDispatcher();

	function toggleFilter(fieldKey: string, value: string) {
		const currentFilters = selectedFilters[fieldKey] || [];
		let newFilters: string[];

		if (currentFilters.includes(value)) {
			newFilters = currentFilters.filter((v) => v !== value);
		} else {
			newFilters = [...currentFilters, value];
		}

		dispatch('filterChange', {
			field: fieldKey,
			values: newFilters
		});
	}

	function clearFilters() {
		dispatch('clearFilters');
	}

	function isSelected(fieldKey: string, value: string): boolean {
		return (selectedFilters[fieldKey] || []).includes(value);
	}

	function hasActiveFilters(): boolean {
		return Object.values(selectedFilters).some((filters) => filters.length > 0);
	}
</script>

<div class="facet-panel">
	<div class="facet-header">
		<h3 class="facet-title">Filters</h3>
		{#if hasActiveFilters()}
			<button on:click={clearFilters} class="clear-btn">
				Clear All
			</button>
		{/if}
	</div>

	{#if facets.length === 0}
		<p class="no-filters">No filters available</p>
	{:else}
		<div class="facet-groups">
			{#each facets as facet}
				<div class="facet-group">
					<h4 class="facet-group-title">{facet.field}</h4>
					<div class="facet-options">
						{#each facet.buckets as bucket}
							<label class="facet-option">
								<input
									type="checkbox"
									checked={isSelected(facet.fieldKey, bucket.value)}
									on:change={() => toggleFilter(facet.fieldKey, bucket.value)}
									class="facet-checkbox"
								/>
								<span class="facet-label">{bucket.value || 'N/A'}</span>
								<span class="facet-count">{bucket.count.toLocaleString()}</span>
							</label>
						{/each}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.facet-panel {
		background: white;
		border-radius: 12px;
		padding: 1.25rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.06);
		border: 1px solid #e5e7eb;
	}

	.facet-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1rem;
		padding-bottom: 0.75rem;
		border-bottom: 2px solid #0033A0;
	}

	.facet-title {
		font-size: 1rem;
		font-weight: 700;
		color: #0033A0;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.clear-btn {
		font-size: 0.75rem;
		font-weight: 600;
		color: #E60012;
		transition: all 0.2s;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
	}

	.clear-btn:hover {
		background: #FEE2E2;
		color: #B91C1C;
	}

	.no-filters {
		font-size: 0.875rem;
		color: #6B7280;
		text-align: center;
		padding: 1rem 0;
	}

	.facet-groups {
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.facet-group {
		padding-bottom: 1rem;
		border-bottom: 1px solid #E5E7EB;
	}

	.facet-group:last-child {
		border-bottom: none;
		padding-bottom: 0;
	}

	.facet-group-title {
		font-size: 0.8125rem;
		font-weight: 600;
		color: #374151;
		margin-bottom: 0.625rem;
		text-transform: uppercase;
		letter-spacing: 0.025em;
	}

	.facet-options {
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
		max-height: 14rem;
		overflow-y: auto;
		scrollbar-width: thin;
		scrollbar-color: #CBD5E1 transparent;
	}

	.facet-options::-webkit-scrollbar {
		width: 4px;
	}

	.facet-options::-webkit-scrollbar-track {
		background: transparent;
	}

	.facet-options::-webkit-scrollbar-thumb {
		background-color: #CBD5E1;
		border-radius: 4px;
	}

	.facet-option {
		display: flex;
		align-items: center;
		cursor: pointer;
		padding: 0.5rem 0.625rem;
		border-radius: 6px;
		transition: all 0.15s;
		gap: 0.5rem;
	}

	.facet-option:hover {
		background: #F3F4F6;
	}

	.facet-checkbox {
		width: 1rem;
		height: 1rem;
		border: 2px solid #D1D5DB;
		border-radius: 4px;
		flex-shrink: 0;
		accent-color: #0033A0;
	}

	.facet-checkbox:checked {
		border-color: #0033A0;
	}

	.facet-label {
		flex: 1;
		font-size: 0.8125rem;
		color: #4B5563;
		line-height: 1.25;
	}

	.facet-count {
		font-size: 0.6875rem;
		color: #9CA3AF;
		font-weight: 500;
		background: #F3F4F6;
		padding: 0.125rem 0.375rem;
		border-radius: 9999px;
	}
</style>
