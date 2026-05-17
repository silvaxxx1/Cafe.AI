import React, { createContext, useContext, useState, useCallback, useMemo, useRef, ReactNode } from 'react';

const normaliseKey = (key: string) => key.trim().toLowerCase();

type CartItems = { [key: string]: number };
type CartPrices = { [key: string]: number };

interface OrderItem { item: string; quantity: number; price?: number }

interface CartContextType {
  cartItems: CartItems;
  cartPrices: CartPrices;
  addToCart: (itemKey: string, quantity: number, price?: number) => void;
  SetQuantityCart: (itemKey: string, delta: number) => void;
  emptyCart: () => void;
  syncCartFromOrder: (order: OrderItem[]) => void;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export const CartProvider = ({ children }: { children: ReactNode }) => {
  const [cartItems, setCartItems] = useState<CartItems>({});
  // Price overrides: set when a size-adjusted price is used (details screen).
  // Falls back to the product catalog price when unset.
  const [cartPrices, setCartPrices] = useState<CartPrices>({});
  const llmManagedKeys = useRef<Set<string>>(new Set());

  const addToCart = useCallback((itemKey: string, quantity: number, price?: number) => {
    const key = normaliseKey(itemKey);
    if (price !== undefined) {
      setCartPrices((prev) => ({ ...prev, [key]: price }));
    }
    setCartItems((prev) => ({
      ...prev,
      [key]: (prev[key] || 0) + quantity,
    }));
  }, []);

  const SetQuantityCart = useCallback((itemKey: string, delta: number) => {
    const key = normaliseKey(itemKey);
    setCartItems((prev) => ({
      ...prev,
      [key]: Math.max((prev[key] || 0) + delta, 0),
    }));
  }, []);

  const emptyCart = useCallback(() => {
    setCartItems({});
    setCartPrices({});
    llmManagedKeys.current = new Set();
  }, []);

  // Merges an LLM order into the cart without wiping manually-added items.
  // Items previously synced from LLM that are no longer in the new order are removed.
  // Items added manually from the browse screen are left untouched.
  const syncCartFromOrder = useCallback((order: OrderItem[]) => {
    const newKeys = new Set(order.map((o) => normaliseKey(o.item)));
    const prevKeys = new Set(llmManagedKeys.current);
    llmManagedKeys.current = newKeys;
    setCartItems((prev) => {
      const next = { ...prev };
      for (const key of prevKeys) {
        if (!newKeys.has(key)) delete next[key];
      }
      for (const { item, quantity } of order) {
        next[normaliseKey(item)] = quantity;
      }
      return next;
    });
    // Store LLM-provided prices so the cart total reflects the agent's prices
    setCartPrices((prev) => {
      const next = { ...prev };
      for (const { item, price } of order) {
        if (price !== undefined) next[normaliseKey(item)] = price;
      }
      return next;
    });
  }, []);

  const value = useMemo(
    () => ({ cartItems, cartPrices, addToCart, SetQuantityCart, emptyCart, syncCartFromOrder }),
    [cartItems, cartPrices, addToCart, SetQuantityCart, emptyCart, syncCartFromOrder]
  );

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
};

export const useCart = (): CartContextType => {
  const context = useContext(CartContext);
  if (!context) throw new Error('useCart must be used within a CartProvider');
  return context;
};
