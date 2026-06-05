<script lang="ts">
	import { createEventDispatcher, onMount, onDestroy } from 'svelte';

	export let placeholder: string = 'Search...';
	export let value: string = '';
	export let loading: boolean = false;
	export let autocompleteEnabled: boolean = false;
	export let autocompleteFunction: ((query: string) => Promise<Array<{ partNumber?: string; name: string; category?: string; claimId?: string }>>) | null = null;

	const dispatch = createEventDispatcher();

	let suggestions: Array<{ partNumber?: string; name: string; category?: string; claimId?: string }> = [];
	let showSuggestions = false;
	let selectedIndex = -1;
	let inputElement: HTMLInputElement;
	let debounceTimer: ReturnType<typeof setTimeout>;
	let isFocused = false;

	async function fetchSuggestions(query: string) {
		if (!autocompleteEnabled || !autocompleteFunction || query.length < 2) {
			suggestions = [];
			showSuggestions = false;
			return;
		}

		try {
			suggestions = await autocompleteFunction(query);
			showSuggestions = suggestions.length > 0 && isFocused;
		} catch (err) {
			console.error('Autocomplete error:', err);
			suggestions = [];
			showSuggestions = false;
		}
	}

	function handleInput() {
		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => {
			fetchSuggestions(value);
		}, 200);
	}

	function handleSearch() {
		showSuggestions = false;
		dispatch('search', value);
	}

	function handleClear() {
		value = '';
		suggestions = [];
		showSuggestions = false;
		dispatch('clear');
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			if (selectedIndex >= 0 && suggestions[selectedIndex]) {
				selectSuggestion(suggestions[selectedIndex]);
			} else {
				handleSearch();
			}
		} else if (event.key === 'ArrowDown') {
			event.preventDefault();
			if (showSuggestions) {
				selectedIndex = Math.min(selectedIndex + 1, suggestions.length - 1);
			}
		} else if (event.key === 'ArrowUp') {
			event.preventDefault();
			if (showSuggestions) {
				selectedIndex = Math.max(selectedIndex - 1, -1);
			}
		} else if (event.key === 'Escape') {
			showSuggestions = false;
			selectedIndex = -1;
		}
	}

	function selectSuggestion(suggestion: { partNumber?: string; name: string; category?: string; claimId?: string }) {
		value = suggestion.partNumber || suggestion.claimId || suggestion.name;
		showSuggestions = false;
		selectedIndex = -1;
		dispatch('search', value);
		dispatch('select', suggestion);
	}

	function handleFocus() {
		isFocused = true;
		if (suggestions.length > 0) {
			showSuggestions = true;
		}
	}

	function handleBlur() {
		// Delay to allow click on suggestion
		setTimeout(() => {
			isFocused = false;
			showSuggestions = false;
			selectedIndex = -1;
		}, 200);
	}

	onDestroy(() => {
		clearTimeout(debounceTimer);
	});
</script>

<div class="search-container">
	<div class="search-wrapper" class:focused={isFocused} class:has-value={value.length > 0}>
		<!-- Search Icon -->
		<div class="search-icon">
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
				<circle cx="11" cy="11" r="8"/>
				<path d="m21 21-4.35-4.35"/>
			</svg>
		</div>

		<!-- Input Field -->
		<input
			bind:this={inputElement}
			type="text"
			bind:value
			on:input={handleInput}
			on:keydown={handleKeydown}
			on:focus={handleFocus}
			on:blur={handleBlur}
			{placeholder}
			disabled={loading}
			class="search-input"
			autocomplete="off"
			spellcheck="false"
		/>

		<!-- Actions -->
		<div class="search-actions">
			{#if value && !loading}
				<button
					type="button"
					on:click={handleClear}
					class="clear-btn"
					aria-label="Clear search"
				>
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
						<path d="M18 6 6 18M6 6l12 12"/>
					</svg>
				</button>
			{/if}

			<button
				type="button"
				on:click={handleSearch}
				disabled={loading}
				class="search-btn"
			>
				{#if loading}
					<svg class="loading-spinner" viewBox="0 0 24 24" fill="none">
						<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-opacity="0.25"/>
						<path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
					</svg>
					<span>Searching...</span>
				{:else}
					<span>Search</span>
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
						<path d="m9 18 6-6-6-6"/>
					</svg>
				{/if}
			</button>
		</div>

		<!-- Autocomplete Dropdown -->
		{#if showSuggestions && suggestions.length > 0}
			<div class="suggestions-dropdown">
				{#each suggestions as suggestion, index}
					<button
						class="suggestion-item"
						class:selected={index === selectedIndex}
						on:click={() => selectSuggestion(suggestion)}
						on:mouseenter={() => selectedIndex = index}
					>
						<div class="suggestion-icon">
							{#if suggestion.partNumber}
								<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
									<path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
								</svg>
							{:else if suggestion.claimId}
								<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
									<path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
								</svg>
							{:else}
								<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
									<circle cx="11" cy="11" r="8"/>
									<path d="m21 21-4.35-4.35"/>
								</svg>
							{/if}
						</div>
						<div class="suggestion-content">
							<span class="suggestion-name">{suggestion.name}</span>
							{#if suggestion.partNumber}
								<span class="suggestion-meta">{suggestion.partNumber}</span>
							{:else if suggestion.claimId}
								<span class="suggestion-meta">{suggestion.claimId}</span>
							{/if}
							{#if suggestion.category}
								<span class="suggestion-category">{suggestion.category}</span>
							{/if}
						</div>
					</button>
				{/each}
			</div>
		{/if}
	</div>

	<!-- Search hint -->
	<div class="search-hint">
		<kbd>Enter</kbd> to search
		{#if autocompleteEnabled}
			<span class="hint-divider">•</span>
			<kbd>↑</kbd><kbd>↓</kbd> to navigate
		{/if}
	</div>
</div>

<style>
	.search-container {
		width: 100%;
		position: relative;
	}

	.search-wrapper {
		position: relative;
		display: flex;
		align-items: center;
		background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
		border: 2px solid #e2e8f0;
		border-radius: 12px;
		padding: 0.25rem;
		transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
	}

	.search-wrapper:hover {
		border-color: #cbd5e1;
		box-shadow: 0 2px 8px rgba(0, 51, 160, 0.08);
	}

	.search-wrapper.focused {
		border-color: #0033A0;
		box-shadow: 0 0 0 4px rgba(0, 51, 160, 0.12), 0 4px 12px rgba(0, 51, 160, 0.15);
		background: white;
	}

	.search-wrapper.has-value {
		background: white;
	}

	.search-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 2.75rem;
		height: 2.75rem;
		color: #94a3b8;
		flex-shrink: 0;
		transition: color 0.2s;
	}

	.search-wrapper.focused .search-icon {
		color: #0033A0;
	}

	.search-icon svg {
		width: 1.25rem;
		height: 1.25rem;
	}

	.search-input {
		flex: 1;
		height: 2.75rem;
		border: none;
		background: transparent;
		font-size: 0.9375rem;
		color: #1e293b;
		outline: none;
		padding: 0 0.5rem;
		min-width: 0;
	}

	.search-input::placeholder {
		color: #94a3b8;
	}

	.search-input:disabled {
		cursor: not-allowed;
		opacity: 0.6;
	}

	.search-actions {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding-right: 0.25rem;
	}

	.clear-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 2rem;
		height: 2rem;
		border-radius: 8px;
		color: #94a3b8;
		transition: all 0.15s;
		flex-shrink: 0;
	}

	.clear-btn:hover {
		background: #f1f5f9;
		color: #64748b;
	}

	.clear-btn svg {
		width: 1rem;
		height: 1rem;
	}

	.search-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.375rem;
		height: 2.5rem;
		padding: 0 1.25rem;
		background: linear-gradient(135deg, #0033A0 0%, #002277 100%);
		color: white;
		font-weight: 600;
		font-size: 0.875rem;
		border-radius: 8px;
		transition: all 0.2s;
		flex-shrink: 0;
		box-shadow: 0 2px 4px rgba(0, 51, 160, 0.25);
	}

	.search-btn:hover:not(:disabled) {
		background: linear-gradient(135deg, #002277 0%, #001a5c 100%);
		transform: translateY(-1px);
		box-shadow: 0 4px 8px rgba(0, 51, 160, 0.3);
	}

	.search-btn:active:not(:disabled) {
		transform: translateY(0);
	}

	.search-btn:disabled {
		opacity: 0.7;
		cursor: not-allowed;
	}

	.search-btn svg {
		width: 1rem;
		height: 1rem;
	}

	.loading-spinner {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	/* Suggestions Dropdown */
	.suggestions-dropdown {
		position: absolute;
		top: calc(100% + 0.5rem);
		left: 0;
		right: 0;
		background: white;
		border: 1px solid #e2e8f0;
		border-radius: 12px;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.08);
		max-height: 320px;
		overflow-y: auto;
		z-index: 50;
		padding: 0.5rem;
	}

	.suggestion-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		width: 100%;
		padding: 0.75rem;
		border-radius: 8px;
		text-align: left;
		transition: all 0.15s;
		cursor: pointer;
	}

	.suggestion-item:hover,
	.suggestion-item.selected {
		background: #f8fafc;
	}

	.suggestion-item.selected {
		background: #EBF4FF;
	}

	.suggestion-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 2.25rem;
		height: 2.25rem;
		background: #f1f5f9;
		border-radius: 8px;
		color: #64748b;
		flex-shrink: 0;
	}

	.suggestion-item.selected .suggestion-icon {
		background: #0033A0;
		color: white;
	}

	.suggestion-icon svg {
		width: 1rem;
		height: 1rem;
	}

	.suggestion-content {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.375rem;
	}

	.suggestion-name {
		font-size: 0.875rem;
		font-weight: 500;
		color: #1e293b;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.suggestion-meta {
		font-size: 0.75rem;
		color: #0033A0;
		font-weight: 600;
		background: #EBF4FF;
		padding: 0.125rem 0.5rem;
		border-radius: 4px;
	}

	.suggestion-category {
		font-size: 0.6875rem;
		color: #64748b;
		margin-left: auto;
	}

	/* Search Hint */
	.search-hint {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		margin-top: 0.625rem;
		font-size: 0.6875rem;
		color: #94a3b8;
	}

	.search-hint kbd {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 1.25rem;
		height: 1.25rem;
		padding: 0 0.375rem;
		background: #f1f5f9;
		border: 1px solid #e2e8f0;
		border-radius: 4px;
		font-family: inherit;
		font-size: 0.625rem;
		font-weight: 500;
		color: #64748b;
	}

	.hint-divider {
		color: #cbd5e1;
	}

	/* Responsive */
	@media (max-width: 640px) {
		.search-btn span {
			display: none;
		}

		.search-btn {
			padding: 0 0.75rem;
		}

		.search-hint {
			display: none;
		}
	}
</style>
