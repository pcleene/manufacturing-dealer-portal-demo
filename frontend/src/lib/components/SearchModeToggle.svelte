<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let mode: 'standard' | 'semantic' = 'standard';
	export let disabled: boolean = false;

	const dispatch = createEventDispatcher();

	function handleModeChange(newMode: 'standard' | 'semantic') {
		if (mode !== newMode && !disabled) {
			mode = newMode;
			dispatch('change', mode);
		}
	}
</script>

<div class="search-mode-toggle">
	<div class="toggle-container" class:disabled>
		<button
			type="button"
			class="toggle-option"
			class:active={mode === 'standard'}
			on:click={() => handleModeChange('standard')}
			{disabled}
		>
			<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
				/>
			</svg>
			<span>Standard</span>
		</button>
		<button
			type="button"
			class="toggle-option"
			class:active={mode === 'semantic'}
			on:click={() => handleModeChange('semantic')}
			{disabled}
		>
			<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
				/>
			</svg>
			<span>Semantic AI</span>
		</button>
		<div class="toggle-slider" class:semantic={mode === 'semantic'}></div>
	</div>
	<div class="mode-hint">
		{#if mode === 'standard'}
			<span class="hint-text">Keyword matching • Exact filters • Fast results</span>
		{:else}
			<span class="hint-text semantic-hint">
				<svg class="w-3.5 h-3.5 inline-block mr-1" fill="currentColor" viewBox="0 0 24 24">
					<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
				</svg>
				Natural language • Meaning-based • Powered by Voyage AI
			</span>
		{/if}
	</div>
</div>

<style>
	.search-mode-toggle {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.toggle-container {
		display: flex;
		position: relative;
		background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
		border: 1px solid #e2e8f0;
		border-radius: 0.75rem;
		padding: 0.25rem;
		width: fit-content;
		box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.05);
	}

	.toggle-container.disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.toggle-option {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.625rem 1rem;
		font-size: 0.875rem;
		font-weight: 500;
		color: #64748b;
		background: transparent;
		border: none;
		border-radius: 0.5rem;
		cursor: pointer;
		transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
		position: relative;
		z-index: 2;
		white-space: nowrap;
	}

	.toggle-option:hover:not(:disabled):not(.active) {
		color: #475569;
	}

	.toggle-option.active {
		color: #1e40af;
	}

	.toggle-option:disabled {
		cursor: not-allowed;
	}

	.toggle-slider {
		position: absolute;
		top: 0.25rem;
		left: 0.25rem;
		height: calc(100% - 0.5rem);
		width: calc(50% - 0.25rem);
		background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
		border-radius: 0.5rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
		transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		z-index: 1;
	}

	.toggle-slider.semantic {
		transform: translateX(100%);
		background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
		box-shadow: 0 1px 3px rgba(79, 70, 229, 0.2), 0 1px 2px rgba(79, 70, 229, 0.1);
	}

	.mode-hint {
		min-height: 1.25rem;
	}

	.hint-text {
		font-size: 0.75rem;
		color: #94a3b8;
		display: flex;
		align-items: center;
		animation: fadeIn 0.2s ease-in-out;
	}

	.hint-text.semantic-hint {
		color: #6366f1;
		font-weight: 500;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
			transform: translateY(-2px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	/* Responsive */
	@media (max-width: 640px) {
		.toggle-option span {
			display: none;
		}
		
		.toggle-option {
			padding: 0.625rem 0.875rem;
		}
		
		.hint-text {
			font-size: 0.6875rem;
		}
	}
</style>

