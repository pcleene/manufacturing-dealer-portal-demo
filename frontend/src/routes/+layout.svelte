<script lang="ts">
	import '../app.css';
	import { page } from '$app/stores';
	import { cart, cartItemCount, cartTotal, toasts, type CartItem } from '$lib/stores/cart';
	import { formatCurrency } from '$lib/api';

	const navLinks = [
		{ href: '/', label: 'Dashboard', icon: 'dashboard' },
		{ href: '/products', label: 'Products', icon: 'products' },
		{ href: '/claims', label: 'Warranty Claims', icon: 'claims' }
	];

	// Use a reactive function that directly accesses $page for each check
	function isActive(href: string, currentPath: string): boolean {
		if (href === '/') return currentPath === '/';
		return currentPath.startsWith(href);
	}

	// Cart dropdown state
	let cartOpen = false;

	function toggleCart() {
		cartOpen = !cartOpen;
	}

	function closeCart() {
		cartOpen = false;
	}

	function removeFromCart(partNumber: string) {
		cart.removeItem(partNumber);
	}

	function updateQuantity(partNumber: string, delta: number) {
		const currentQty = cart.getItemQuantity(partNumber);
		cart.updateQuantity(partNumber, currentQty + delta);
	}
</script>

<div class="app-container">
	<!-- Header -->
	<header class="header">
		<div class="header-inner">
			<!-- Logo & Brand -->
			<a href="/" class="brand">
				<div class="brand-icon">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
					</svg>
				</div>
				<div class="brand-text">
					<span class="brand-name">OEMPartner</span>
					<span class="brand-sub">Dealer Portal</span>
				</div>
				<div class="brand-badge">MFG</div>
			</a>

			<!-- Navigation -->
			<nav class="nav">
				{#each navLinks as link}
					<a 
						href={link.href} 
						class="nav-link"
						class:active={isActive(link.href, $page.url.pathname)}
					>
						{#if link.icon === 'dashboard'}
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<rect x="3" y="3" width="7" height="9" rx="1"/>
								<rect x="14" y="3" width="7" height="5" rx="1"/>
								<rect x="14" y="12" width="7" height="9" rx="1"/>
								<rect x="3" y="16" width="7" height="5" rx="1"/>
							</svg>
						{:else if link.icon === 'products'}
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
							</svg>
						{:else if link.icon === 'claims'}
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
							</svg>
						{/if}
						<span>{link.label}</span>
					</a>
				{/each}
			</nav>

			<!-- Cart & User Menu -->
			<div class="user-area">
				<!-- Shopping Cart -->
				<div class="cart-container">
					<button class="cart-button" on:click={toggleCart} aria-label="Shopping cart">
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path d="M6 6h15l-1.5 9h-12L6 6zM6 6L5 3H2"/>
							<circle cx="9" cy="20" r="1"/>
							<circle cx="18" cy="20" r="1"/>
						</svg>
						{#if $cartItemCount > 0}
							<span class="cart-badge">{$cartItemCount > 99 ? '99+' : $cartItemCount}</span>
						{/if}
					</button>

					<!-- Cart Dropdown -->
					{#if cartOpen}
						<div class="cart-dropdown">
							<div class="cart-dropdown-header">
								<h3>Shopping Cart</h3>
								<button class="close-cart" on:click={closeCart} aria-label="Close cart">
									<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
										<path d="M6 18L18 6M6 6l12 12"/>
									</svg>
								</button>
							</div>

							{#if $cart.items.length === 0}
								<div class="cart-empty">
									<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
										<path d="M6 6h15l-1.5 9h-12L6 6zM6 6L5 3H2"/>
										<circle cx="9" cy="20" r="1"/>
										<circle cx="18" cy="20" r="1"/>
									</svg>
									<p>Your cart is empty</p>
									<a href="/products" class="browse-link" on:click={closeCart}>Browse Products</a>
								</div>
							{:else}
								<div class="cart-items">
									{#each $cart.items as item (item.partNumber)}
										<div class="cart-item">
											<div class="cart-item-info">
												<span class="cart-item-part">{item.partNumber}</span>
												<span class="cart-item-name">{item.name}</span>
												<span class="cart-item-price">{formatCurrency(item.unitPrice)}</span>
											</div>
											<div class="cart-item-actions">
												<div class="quantity-control">
													<button on:click={() => updateQuantity(item.partNumber, -1)} aria-label="Decrease quantity">−</button>
													<span>{item.quantity}</span>
													<button on:click={() => updateQuantity(item.partNumber, 1)} aria-label="Increase quantity">+</button>
												</div>
												<button class="remove-item" on:click={() => removeFromCart(item.partNumber)} aria-label="Remove item">
													<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
														<path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
													</svg>
												</button>
											</div>
										</div>
									{/each}
								</div>

								<div class="cart-footer">
									<div class="cart-total">
										<span>Total (Dealer Price)</span>
										<span class="total-amount">{formatCurrency($cartTotal)}</span>
									</div>
									<div class="cart-actions">
										<button class="clear-cart" on:click={() => cart.clearCart()}>Clear Cart</button>
										<button class="checkout-btn" disabled>
											<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
												<path d="M5 13l4 4L19 7"/>
											</svg>
											Checkout (Demo)
										</button>
									</div>
									<p class="demo-notice">This is a visual demo only. No actual orders will be placed.</p>
								</div>
							{/if}
						</div>
						<!-- svelte-ignore a11y-no-static-element-interactions -->
						<!-- svelte-ignore a11y-click-events-have-key-events -->
						<div class="cart-overlay" on:click={closeCart}></div>
					{/if}
				</div>

				<!-- User Avatar -->
				<div class="user-avatar">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
						<circle cx="12" cy="7" r="4"/>
					</svg>
				</div>
			</div>
		</div>

		<!-- Accent Line -->
		<div class="header-accent"></div>
	</header>

	<!-- Main Content -->
	<main class="main">
		<div class="main-inner">
			<slot />
		</div>
	</main>

	<!-- Toast Notifications -->
	{#if $toasts.length > 0}
		<div class="toast-container">
			{#each $toasts as toast (toast.id)}
				<div class="toast toast-{toast.type}">
					{#if toast.type === 'success'}
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path d="M5 13l4 4L19 7"/>
						</svg>
					{:else if toast.type === 'error'}
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path d="M6 18L18 6M6 6l12 12"/>
						</svg>
					{:else}
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
						</svg>
					{/if}
					<span>{toast.message}</span>
					<button on:click={() => toasts.dismiss(toast.id)} aria-label="Dismiss">
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path d="M6 18L18 6M6 6l12 12"/>
						</svg>
					</button>
				</div>
			{/each}
		</div>
	{/if}

	<!-- Footer -->
	<footer class="footer">
		<div class="footer-inner">
			<div class="footer-brand">
				<span class="footer-logo">MFG</span>
				<span class="footer-text">Manufacturing Group Malaysia Sdn Bhd</span>
			</div>
			<div class="footer-links">
				<span class="footer-copy">&copy; {new Date().getFullYear()} OEMPartner Dealer Portal</span>
				<span class="footer-divider">•</span>
				<span class="footer-notice">Internal Use Only</span>
			</div>
		</div>
	</footer>
</div>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		min-height: 100vh;
	}

	.app-container {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
		background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
	}

	/* Header */
	.header {
		position: sticky;
		top: 0;
		z-index: 100;
		background: linear-gradient(135deg, #0033A0 0%, #001a5c 100%);
		box-shadow: 0 4px 20px rgba(0, 51, 160, 0.25);
	}

	.header-inner {
		max-width: 1400px;
		margin: 0 auto;
		padding: 0 1.5rem;
		display: flex;
		align-items: center;
		justify-content: space-between;
		height: 4rem;
		gap: 2rem;
	}

	.header-accent {
		height: 3px;
		background: linear-gradient(90deg, #E60012 0%, #E60012 30%, transparent 30%);
	}

	/* Brand */
	.brand {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		text-decoration: none;
		color: white;
	}

	.brand-icon {
		width: 2.25rem;
		height: 2.25rem;
		background: rgba(255, 255, 255, 0.15);
		border-radius: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.brand-icon svg {
		width: 1.25rem;
		height: 1.25rem;
	}

	.brand-text {
		display: flex;
		flex-direction: column;
		line-height: 1.1;
	}

	.brand-name {
		font-size: 1.125rem;
		font-weight: 700;
		letter-spacing: 0.05em;
	}

	.brand-sub {
		font-size: 0.6875rem;
		font-weight: 500;
		opacity: 0.75;
		letter-spacing: 0.025em;
	}

	.brand-badge {
		background: #E60012;
		color: white;
		font-size: 0.625rem;
		font-weight: 700;
		padding: 0.125rem 0.375rem;
		border-radius: 4px;
		letter-spacing: 0.05em;
	}

	/* Navigation */
	.nav {
		display: flex;
		align-items: center;
		gap: 0.25rem;
	}

	.nav-link {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		color: rgba(255, 255, 255, 0.8);
		text-decoration: none;
		font-size: 0.875rem;
		font-weight: 500;
		border-radius: 8px;
		transition: all 0.2s;
	}

	.nav-link:hover {
		color: white;
		background: rgba(255, 255, 255, 0.1);
	}

	.nav-link.active {
		color: white;
		background: rgba(255, 255, 255, 0.15);
		box-shadow: inset 0 -2px 0 0 #E60012;
	}

	.nav-link svg {
		width: 1.125rem;
		height: 1.125rem;
	}

	/* User Area */
	.user-area {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	/* Cart Button */
	.cart-container {
		position: relative;
	}

	.cart-button {
		position: relative;
		width: 2.25rem;
		height: 2.25rem;
		background: rgba(255, 255, 255, 0.15);
		border: none;
		border-radius: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: white;
		cursor: pointer;
		transition: all 0.2s;
	}

	.cart-button:hover {
		background: rgba(255, 255, 255, 0.25);
	}

	.cart-button svg {
		width: 1.125rem;
		height: 1.125rem;
	}

	.cart-badge {
		position: absolute;
		top: -4px;
		right: -4px;
		min-width: 18px;
		height: 18px;
		background: #E60012;
		color: white;
		font-size: 0.625rem;
		font-weight: 700;
		border-radius: 9px;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0 4px;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
	}

	/* Cart Dropdown */
	.cart-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.3);
		z-index: 199;
	}

	.cart-dropdown {
		position: absolute;
		top: calc(100% + 12px);
		right: 0;
		width: 380px;
		max-height: 80vh;
		background: white;
		border-radius: 12px;
		box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
		z-index: 200;
		overflow: hidden;
		animation: slideDown 0.2s ease-out;
	}

	@keyframes slideDown {
		from {
			opacity: 0;
			transform: translateY(-8px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.cart-dropdown-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 1.25rem;
		background: linear-gradient(135deg, #0033A0 0%, #002277 100%);
		color: white;
	}

	.cart-dropdown-header h3 {
		margin: 0;
		font-size: 1rem;
		font-weight: 700;
	}

	.close-cart {
		background: rgba(255, 255, 255, 0.15);
		border: none;
		border-radius: 6px;
		width: 28px;
		height: 28px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: white;
		cursor: pointer;
		transition: background 0.2s;
	}

	.close-cart:hover {
		background: rgba(255, 255, 255, 0.25);
	}

	.close-cart svg {
		width: 16px;
		height: 16px;
	}

	/* Cart Empty State */
	.cart-empty {
		padding: 2.5rem 1.5rem;
		text-align: center;
	}

	.cart-empty svg {
		width: 3rem;
		height: 3rem;
		color: #cbd5e1;
		margin-bottom: 1rem;
	}

	.cart-empty p {
		color: #64748b;
		margin: 0 0 1rem 0;
		font-size: 0.9375rem;
	}

	.browse-link {
		color: #0033A0;
		font-weight: 600;
		text-decoration: none;
		font-size: 0.875rem;
	}

	.browse-link:hover {
		text-decoration: underline;
	}

	/* Cart Items */
	.cart-items {
		max-height: 300px;
		overflow-y: auto;
	}

	.cart-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.875rem 1.25rem;
		border-bottom: 1px solid #f1f5f9;
	}

	.cart-item:hover {
		background: #f8fafc;
	}

	.cart-item-info {
		display: flex;
		flex-direction: column;
		gap: 0.125rem;
		flex: 1;
		min-width: 0;
	}

	.cart-item-part {
		font-size: 0.6875rem;
		font-weight: 600;
		color: #0033A0;
		font-family: 'SF Mono', Monaco, monospace;
	}

	.cart-item-name {
		font-size: 0.8125rem;
		font-weight: 500;
		color: #1e293b;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.cart-item-price {
		font-size: 0.75rem;
		color: #64748b;
	}

	.cart-item-actions {
		display: flex;
		align-items: center;
		gap: 0.625rem;
		margin-left: 0.75rem;
	}

	.quantity-control {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		background: #f1f5f9;
		border-radius: 6px;
		padding: 0.125rem;
	}

	.quantity-control button {
		width: 24px;
		height: 24px;
		border: none;
		background: transparent;
		color: #64748b;
		font-size: 0.875rem;
		font-weight: 600;
		cursor: pointer;
		border-radius: 4px;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.15s;
	}

	.quantity-control button:hover {
		background: #e2e8f0;
		color: #0033A0;
	}

	.quantity-control span {
		width: 24px;
		text-align: center;
		font-size: 0.8125rem;
		font-weight: 600;
		color: #1e293b;
	}

	.remove-item {
		width: 28px;
		height: 28px;
		border: none;
		background: transparent;
		color: #94a3b8;
		cursor: pointer;
		border-radius: 6px;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.15s;
	}

	.remove-item:hover {
		background: #fef2f2;
		color: #ef4444;
	}

	.remove-item svg {
		width: 16px;
		height: 16px;
	}

	/* Cart Footer */
	.cart-footer {
		padding: 1rem 1.25rem;
		background: #f8fafc;
		border-top: 1px solid #e2e8f0;
	}

	.cart-total {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.875rem;
	}

	.cart-total span:first-child {
		font-size: 0.8125rem;
		color: #64748b;
	}

	.total-amount {
		font-size: 1.125rem;
		font-weight: 700;
		color: #0f172a;
	}

	.cart-actions {
		display: flex;
		gap: 0.5rem;
	}

	.clear-cart {
		flex: 1;
		padding: 0.625rem 1rem;
		background: white;
		border: 1px solid #e2e8f0;
		border-radius: 8px;
		color: #64748b;
		font-size: 0.8125rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.15s;
	}

	.clear-cart:hover {
		background: #f8fafc;
		border-color: #cbd5e1;
	}

	.checkout-btn {
		flex: 2;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		padding: 0.625rem 1rem;
		background: linear-gradient(135deg, #0033A0 0%, #002277 100%);
		border: none;
		border-radius: 8px;
		color: white;
		font-size: 0.8125rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.15s;
	}

	.checkout-btn:disabled {
		opacity: 0.7;
		cursor: not-allowed;
	}

	.checkout-btn svg {
		width: 16px;
		height: 16px;
	}

	.demo-notice {
		margin: 0.75rem 0 0 0;
		font-size: 0.6875rem;
		color: #94a3b8;
		text-align: center;
	}

	/* Toast Notifications */
	.toast-container {
		position: fixed;
		bottom: 1.5rem;
		right: 1.5rem;
		z-index: 1000;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.toast {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.875rem 1rem;
		background: white;
		border-radius: 10px;
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
		animation: toastSlide 0.3s ease-out;
		min-width: 280px;
	}

	@keyframes toastSlide {
		from {
			opacity: 0;
			transform: translateX(100%);
		}
		to {
			opacity: 1;
			transform: translateX(0);
		}
	}

	.toast svg {
		width: 1.25rem;
		height: 1.25rem;
		flex-shrink: 0;
	}

	.toast span {
		flex: 1;
		font-size: 0.875rem;
		font-weight: 500;
		color: #1e293b;
	}

	.toast button {
		background: transparent;
		border: none;
		padding: 0.25rem;
		cursor: pointer;
		color: #94a3b8;
		border-radius: 4px;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.15s;
	}

	.toast button:hover {
		background: #f1f5f9;
		color: #64748b;
	}

	.toast button svg {
		width: 1rem;
		height: 1rem;
	}

	.toast-success {
		border-left: 4px solid #10b981;
	}

	.toast-success svg:first-child {
		color: #10b981;
	}

	.toast-error {
		border-left: 4px solid #ef4444;
	}

	.toast-error svg:first-child {
		color: #ef4444;
	}

	.toast-info {
		border-left: 4px solid #0033A0;
	}

	.toast-info svg:first-child {
		color: #0033A0;
	}

	.user-avatar {
		width: 2.25rem;
		height: 2.25rem;
		background: rgba(255, 255, 255, 0.15);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		color: white;
		cursor: pointer;
		transition: all 0.2s;
	}

	.user-avatar:hover {
		background: rgba(255, 255, 255, 0.25);
	}

	.user-avatar svg {
		width: 1.125rem;
		height: 1.125rem;
	}

	/* Main Content */
	.main {
		flex: 1;
		padding: 2rem 1.5rem;
	}

	.main-inner {
		max-width: 1400px;
		margin: 0 auto;
	}

	/* Footer */
	.footer {
		background: white;
		border-top: 1px solid #e2e8f0;
		padding: 1rem 1.5rem;
	}

	.footer-inner {
		max-width: 1400px;
		margin: 0 auto;
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.footer-brand {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.footer-logo {
		background: #0033A0;
		color: white;
		font-size: 0.625rem;
		font-weight: 700;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		letter-spacing: 0.05em;
	}

	.footer-text {
		font-size: 0.8125rem;
		color: #64748b;
		font-weight: 500;
	}

	.footer-links {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		font-size: 0.75rem;
		color: #94a3b8;
	}

	.footer-divider {
		color: #e2e8f0;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.header-inner {
			padding: 0 1rem;
		}

		.brand-text,
		.brand-badge {
			display: none;
		}

		.nav-link span {
			display: none;
		}

		.nav-link {
			padding: 0.5rem;
		}

		.main {
			padding: 1.5rem 1rem;
		}

		.footer-inner {
			flex-direction: column;
			text-align: center;
		}

		/* Cart responsive */
		.cart-dropdown {
			position: fixed;
			top: auto;
			bottom: 0;
			left: 0;
			right: 0;
			width: 100%;
			max-height: 70vh;
			border-radius: 16px 16px 0 0;
			animation: slideUp 0.3s ease-out;
		}

		@keyframes slideUp {
			from {
				opacity: 0;
				transform: translateY(100%);
			}
			to {
				opacity: 1;
				transform: translateY(0);
			}
		}

		/* Toast responsive */
		.toast-container {
			left: 1rem;
			right: 1rem;
			bottom: 1rem;
		}

		.toast {
			min-width: auto;
		}
	}
</style>
