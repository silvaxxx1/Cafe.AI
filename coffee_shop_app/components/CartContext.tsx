import React, { createContext, useContext, useState, useCallback, useMemo, useRef, ReactNode } from 'react';

const normaliseKey = (key: string) => key.trim().toLowerCase();

type CartItems = { [key: string]: number };

interface OrderItem { item: string; quantity: number }

interface CartContextType {
  cartItems: CartItems;
  addToCart: (itemKey: string, quantity: number) => void;
  SetQuantityCart: (itemKey: string, delta: number) => void;
  emptyCart: () => void;
  syncCartFromOrder: (order: OrderItem[]) => void;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export const CartProvider = ({ children }: { children: ReactNode }) => {
  const [cartItems, setCartItems] = useState<CartItems>({});
  // tracks which keys were last synced from an LLM order response
  const llmManagedKeys = useRef<Set<string>>(new Set());

  const addToCart = useCallback((itemKey: string, quantity: number) => {
    const key = normaliseKey(itemKey);
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
    llmManagedKeys.current = new Set();
  }, []);

  // Merges an LLM order into the cart without wiping manually-added items.
  // Items previously synced from LLM that are no longer in the new order are removed.
  // Items added manually from the browse screen are left untouched.
  const syncCartFromOrder = useCallback((order: OrderItem[]) => {
    const newKeys = new Set(order.map((o) => normaliseKey(o.item)));
    // Snapshot the current LLM keys before updating the ref, because React
    // runs the setCartItems callback asynchronously — if we updated the ref
    // first, the functional update would read the wrong (already-replaced) set.
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
  }, []);

  const value = useMemo(
    () => ({ cartItems, addToCart, SetQuantityCart, emptyCart, syncCartFromOrder }),
    [cartItems, addToCart, SetQuantityCart, emptyCart, syncCartFromOrder]
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
