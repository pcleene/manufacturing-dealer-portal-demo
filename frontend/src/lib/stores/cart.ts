/**
 * Shopping Cart Store - Visual Demo Only
 * Manufacturing Group Manufacturing OEMPartner Dealer Portal
 * 
 * This is a frontend-only cart for demonstration purposes.
 * No backend API or checkout flow - just for showing the e-commerce potential.
 */
import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';

// ============================================================================
// TYPES
// ============================================================================

export interface CartItem {
	partNumber: string;
	sku: string;
	name: string;
	category: string;
	subcategory: string;
	unitPrice: number;  // Dealer price
	msrp: number;
	quantity: number;
	addedAt: string;
}

export interface Cart {
	items: CartItem[];
	updatedAt: string;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const CART_STORAGE_KEY = 'OEMPartner_dealer_cart';
const MAX_QUANTITY_PER_ITEM = 99;

// ============================================================================
// INITIAL STATE
// ============================================================================

function getInitialCart(): Cart {
	if (browser) {
		try {
			const stored = localStorage.getItem(CART_STORAGE_KEY);
			if (stored) {
				return JSON.parse(stored);
			}
		} catch (e) {
			console.error('Failed to parse cart from localStorage:', e);
		}
	}
	return {
		items: [],
		updatedAt: new Date().toISOString()
	};
}

// ============================================================================
// STORE
// ============================================================================

function createCartStore() {
	const { subscribe, set, update } = writable<Cart>(getInitialCart());

	// Persist to localStorage whenever cart changes
	function persist(cart: Cart) {
		if (browser) {
			try {
				localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
			} catch (e) {
				console.error('Failed to save cart to localStorage:', e);
			}
		}
	}

	return {
		subscribe,

		/**
		 * Add an item to the cart
		 */
		addItem: (item: Omit<CartItem, 'quantity' | 'addedAt'>, quantity: number = 1) => {
			update(cart => {
				const existingIndex = cart.items.findIndex(i => i.partNumber === item.partNumber);
				
				let newItems: CartItem[];
				
				if (existingIndex >= 0) {
					// Update existing item quantity
					newItems = cart.items.map((i, idx) => {
						if (idx === existingIndex) {
							const newQty = Math.min(i.quantity + quantity, MAX_QUANTITY_PER_ITEM);
							return { ...i, quantity: newQty };
						}
						return i;
					});
				} else {
					// Add new item
					newItems = [
						...cart.items,
						{
							...item,
							quantity: Math.min(quantity, MAX_QUANTITY_PER_ITEM),
							addedAt: new Date().toISOString()
						}
					];
				}

				const newCart = {
					items: newItems,
					updatedAt: new Date().toISOString()
				};
				
				persist(newCart);
				return newCart;
			});
		},

		/**
		 * Update item quantity
		 */
		updateQuantity: (partNumber: string, quantity: number) => {
			update(cart => {
				if (quantity <= 0) {
					// Remove item if quantity is 0 or less
					const newCart = {
						items: cart.items.filter(i => i.partNumber !== partNumber),
						updatedAt: new Date().toISOString()
					};
					persist(newCart);
					return newCart;
				}

				const newCart = {
					items: cart.items.map(i => {
						if (i.partNumber === partNumber) {
							return { ...i, quantity: Math.min(quantity, MAX_QUANTITY_PER_ITEM) };
						}
						return i;
					}),
					updatedAt: new Date().toISOString()
				};
				
				persist(newCart);
				return newCart;
			});
		},

		/**
		 * Remove an item from the cart
		 */
		removeItem: (partNumber: string) => {
			update(cart => {
				const newCart = {
					items: cart.items.filter(i => i.partNumber !== partNumber),
					updatedAt: new Date().toISOString()
				};
				persist(newCart);
				return newCart;
			});
		},

		/**
		 * Clear all items from the cart
		 */
		clearCart: () => {
			const emptyCart = {
				items: [],
				updatedAt: new Date().toISOString()
			};
			persist(emptyCart);
			set(emptyCart);
		},

		/**
		 * Check if an item is in the cart
		 */
		hasItem: (partNumber: string): boolean => {
			const cart = get({ subscribe });
			return cart.items.some(i => i.partNumber === partNumber);
		},

		/**
		 * Get quantity of a specific item
		 */
		getItemQuantity: (partNumber: string): number => {
			const cart = get({ subscribe });
			const item = cart.items.find(i => i.partNumber === partNumber);
			return item?.quantity || 0;
		}
	};
}

export const cart = createCartStore();

// ============================================================================
// DERIVED STORES
// ============================================================================

/**
 * Total number of items in cart
 */
export const cartItemCount = derived(cart, ($cart) => 
	$cart.items.reduce((sum, item) => sum + item.quantity, 0)
);

/**
 * Total value of cart (dealer price)
 */
export const cartTotal = derived(cart, ($cart) => 
	$cart.items.reduce((sum, item) => sum + (item.unitPrice * item.quantity), 0)
);

/**
 * Total MSRP value of cart
 */
export const cartMsrpTotal = derived(cart, ($cart) => 
	$cart.items.reduce((sum, item) => sum + (item.msrp * item.quantity), 0)
);

/**
 * Number of unique items in cart
 */
export const cartUniqueItemCount = derived(cart, ($cart) => $cart.items.length);

/**
 * Is cart empty?
 */
export const isCartEmpty = derived(cart, ($cart) => $cart.items.length === 0);

// ============================================================================
// TOAST NOTIFICATION STORE
// ============================================================================

export interface Toast {
	id: string;
	message: string;
	type: 'success' | 'error' | 'info';
	duration: number;
}

function createToastStore() {
	const { subscribe, update } = writable<Toast[]>([]);

	return {
		subscribe,

		show: (message: string, type: 'success' | 'error' | 'info' = 'success', duration: number = 3000) => {
			const id = Math.random().toString(36).substring(2, 9);
			const toast: Toast = { id, message, type, duration };

			update(toasts => [...toasts, toast]);

			// Auto-remove after duration
			setTimeout(() => {
				update(toasts => toasts.filter(t => t.id !== id));
			}, duration);

			return id;
		},

		dismiss: (id: string) => {
			update(toasts => toasts.filter(t => t.id !== id));
		},

		clear: () => {
			update(() => []);
		}
	};
}

export const toasts = createToastStore();

