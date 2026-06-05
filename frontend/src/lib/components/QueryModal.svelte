<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let show = false;
	export let query = '';

	const dispatch = createEventDispatcher();

	function close() {
		show = false;
		dispatch('close');
	}

	function copyToClipboard() {
		navigator.clipboard.writeText(query);
		// Show brief feedback
		const btn = document.getElementById('copy-btn');
		if (btn) {
			btn.textContent = '✓ Copied!';
			setTimeout(() => {
				btn.textContent = '📋 Copy';
			}, 2000);
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			close();
		}
	}
</script>

<svelte:window on:keydown={handleKeydown} />

{#if show}
	<div class="modal-backdrop" on:click={close} on:keydown={handleKeydown} role="button" tabindex="0">
		<div class="modal-container" on:click|stopPropagation on:keydown|stopPropagation role="dialog" aria-modal="true">
			<div class="modal-header">
				<div class="header-title">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
					</svg>
					<span>MongoDB Query</span>
				</div>
				<button class="close-btn" on:click={close} aria-label="Close">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>
			
			<div class="modal-body">
				<div class="code-header">
					<span class="lang-badge">Python</span>
					<button id="copy-btn" class="copy-btn" on:click={copyToClipboard}>
						📋 Copy
					</button>
				</div>
				<pre class="code-block"><code>{query}</code></pre>
			</div>

			<div class="modal-footer">
				<p class="hint">
					💡 This is the actual aggregation pipeline being executed on MongoDB Atlas
				</p>
			</div>
		</div>
	</div>
{/if}

<style>
	.modal-backdrop {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.6);
		backdrop-filter: blur(4px);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		animation: fadeIn 0.15s ease-out;
	}

	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}

	.modal-container {
		background: #1e1e1e;
		border-radius: 16px;
		width: 90%;
		max-width: 800px;
		max-height: 85vh;
		display: flex;
		flex-direction: column;
		box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
		animation: slideUp 0.2s ease-out;
		overflow: hidden;
	}

	@keyframes slideUp {
		from { 
			opacity: 0;
			transform: translateY(20px) scale(0.95);
		}
		to { 
			opacity: 1;
			transform: translateY(0) scale(1);
		}
	}

	.modal-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1rem 1.25rem;
		background: linear-gradient(135deg, #0033A0 0%, #001a5c 100%);
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}

	.header-title {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		color: white;
		font-weight: 600;
		font-size: 1rem;
	}

	.header-title svg {
		width: 1.25rem;
		height: 1.25rem;
		opacity: 0.9;
	}

	.close-btn {
		background: rgba(255, 255, 255, 0.1);
		border: none;
		border-radius: 8px;
		padding: 0.5rem;
		cursor: pointer;
		color: white;
		transition: all 0.15s;
	}

	.close-btn:hover {
		background: rgba(255, 255, 255, 0.2);
	}

	.close-btn svg {
		width: 1.25rem;
		height: 1.25rem;
	}

	.modal-body {
		flex: 1;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}

	.code-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.75rem 1.25rem;
		background: #2d2d2d;
		border-bottom: 1px solid #3d3d3d;
	}

	.lang-badge {
		font-size: 0.75rem;
		font-weight: 600;
		color: #569cd6;
		background: rgba(86, 156, 214, 0.15);
		padding: 0.25rem 0.75rem;
		border-radius: 4px;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.copy-btn {
		background: #3d3d3d;
		border: none;
		border-radius: 6px;
		padding: 0.375rem 0.75rem;
		font-size: 0.8125rem;
		color: #d4d4d4;
		cursor: pointer;
		transition: all 0.15s;
	}

	.copy-btn:hover {
		background: #4d4d4d;
		color: white;
	}

	.code-block {
		flex: 1;
		overflow: auto;
		margin: 0;
		padding: 1.25rem;
		background: #1e1e1e;
		font-family: 'SF Mono', 'Fira Code', 'Monaco', monospace;
		font-size: 0.8125rem;
		line-height: 1.6;
		color: #d4d4d4;
		white-space: pre;
		tab-size: 4;
	}

	.code-block code {
		color: inherit;
	}

	.modal-footer {
		padding: 0.875rem 1.25rem;
		background: #252525;
		border-top: 1px solid #3d3d3d;
	}

	.hint {
		margin: 0;
		font-size: 0.75rem;
		color: #808080;
	}

	@media (max-width: 640px) {
		.modal-container {
			width: 95%;
			max-height: 90vh;
		}

		.code-block {
			font-size: 0.75rem;
			padding: 1rem;
		}
	}
</style>

