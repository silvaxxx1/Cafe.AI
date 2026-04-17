import React, { createContext, useContext, useState, useCallback, useMemo, ReactNode } from 'react';

type CartItems = { [key: string]: number };

interface CartContextType {
  cartItems: CartItems;
  addToCart: (itemKey: string, quantity: number) => void;
  SetQuantityCart: (itemKey: string, delta: number) => void;
  emptyCart: () => void;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export const CartProvider = ({ children }: { children: ReactNode }) => {
  const [cartItems, setCartItems] = useState<CartItems>({});

  const addToCart = useCallback((itemKey: string, quantity: number) => {
    setCartItems((prev) => ({
      ...prev,
      [itemKey]: (prev[itemKey] || 0) + quantity,
    }));
  }, []);

  const SetQuantityCart = useCallback((itemKey: string, delta: number) => {
    setCartItems((prev) => ({
      ...prev,
      [itemKey]: Math.max((prev[itemKey] || 0) + delta, 0),
    }));
  }, []);

  const emptyCart = useCallback(() => {
    setCartItems({});
  }, []);

  const value = useMemo(
    () => ({ cartItems, addToCart, SetQuantityCart, emptyCart }),
    [cartItems, addToCart, SetQuantityCart, emptyCart]
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
