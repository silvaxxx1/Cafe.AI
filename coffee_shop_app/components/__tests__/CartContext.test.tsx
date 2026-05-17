import React from 'react';
import { renderHook, act } from '@testing-library/react-native';
import { CartProvider, useCart } from '../CartContext';

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <CartProvider>{children}</CartProvider>
);

// ── addToCart ────────────────────────────────────────────────────────────────

test('addToCart adds item with correct quantity', () => {
  const { result } = renderHook(() => useCart(), { wrapper });
  act(() => result.current.addToCart('Cappuccino', 2));
  expect(result.current.cartItems['cappuccino']).toBe(2);
});

test('addToCart normalises keys — titlecase and lowercase land in same slot', () => {
  const { result } = renderHook(() => useCart(), { wrapper });
  act(() => result.current.addToCart('Latte', 1));
  act(() => result.current.addToCart('latte', 1));
  act(() => result.current.addToCart('LATTE ', 1));
  expect(result.current.cartItems['latte']).toBe(3);
});

test('addToCart merges duplicate entries', () => {
  const { result } = renderHook(() => useCart(), { wrapper });
  act(() => result.current.addToCart('Latte', 1));
  act(() => result.current.addToCart('Latte', 1));
  expect(result.current.cartItems['latte']).toBe(2);
});

test('addToCart keeps independent items separate', () => {
  const { result } = renderHook(() => useCart(), { wrapper });
  act(() => result.current.addToCart('Latte', 1));
  act(() => result.current.addToCart('Croissant', 1));
  expect(result.current.cartItems['latte']).toBe(1);
  expect(result.current.cartItems['croissant']).toBe(1);
});

// ── emptyCart ────────────────────────────────────────────────────────────────

test('emptyCart clears all items', () => {
  const { result } = renderHook(() => useCart(), { wrapper });
  act(() => result.current.addToCart('Espresso shot', 1));
  act(() => result.current.emptyCart());
  expect(Object.keys(result.current.cartItems)).toHaveLength(0);
});

// ── syncCartFromOrder ────────────────────────────────────────────────────────

test('syncCartFromOrder sets LLM order items to exact quantities', () => {
  const { result } = renderHook(() => useCart(), { wrapper });
  act(() => result.current.syncCartFromOrder([
    { item: 'Cappuccino', quantity: 2 },
    { item: 'Croissant', quantity: 1 },
  ]));
  expect(result.current.cartItems['cappuccino']).toBe(2);
  expect(result.current.cartItems['croissant']).toBe(1);
});

test('syncCartFromOrder preserves manually-added items', () => {
  const { result } = renderHook(() => useCart(), { wrapper });
  act(() => result.current.addToCart('Latte', 1));
  act(() => result.current.syncCartFromOrder([{ item: 'Cappuccino', quantity: 1 }]));
  expect(result.current.cartItems['latte']).toBe(1);
  expect(result.current.cartItems['cappuccino']).toBe(1);
});

test('syncCartFromOrder removes LLM items dropped from the next order', () => {
  const { result } = renderHook(() => useCart(), { wrapper });
  act(() => result.current.syncCartFromOrder([
    { item: 'Cappuccino', quantity: 1 },
    { item: 'Croissant', quantity: 1 },
  ]));
  act(() => result.current.syncCartFromOrder([{ item: 'Cappuccino', quantity: 1 }]));
  expect(result.current.cartItems['cappuccino']).toBe(1);
  expect(result.current.cartItems['croissant']).toBeUndefined();
});

test('syncCartFromOrder does not remove manually-added items on subsequent sync', () => {
  const { result } = renderHook(() => useCart(), { wrapper });
  act(() => result.current.addToCart('Latte', 1));
  act(() => result.current.syncCartFromOrder([{ item: 'Cappuccino', quantity: 1 }]));
  act(() => result.current.syncCartFromOrder([{ item: 'Cappuccino', quantity: 2 }]));
  expect(result.current.cartItems['latte']).toBe(1);
  expect(result.current.cartItems['cappuccino']).toBe(2);
});

// ── price overrides ───────────────────────────────────────────────────────────

test('addToCart stores price override in cartPrices', () => {
  const { result } = renderHook(() => useCart(), { wrapper });
  act(() => result.current.addToCart('Cappuccino', 1, 5.00));
  expect(result.current.cartPrices['cappuccino']).toBe(5.00);
});

test('addToCart without price leaves cartPrices unchanged', () => {
  const { result } = renderHook(() => useCart(), { wrapper });
  act(() => result.current.addToCart('Latte', 1));
  expect(result.current.cartPrices['latte']).toBeUndefined();
});

test('emptyCart clears cartPrices', () => {
  const { result } = renderHook(() => useCart(), { wrapper });
  act(() => result.current.addToCart('Cappuccino', 1, 5.00));
  act(() => result.current.emptyCart());
  expect(result.current.cartPrices).toEqual({});
});

test('emptyCart resets LLM tracking so next sync starts clean', () => {
  const { result } = renderHook(() => useCart(), { wrapper });
  act(() => result.current.syncCartFromOrder([{ item: 'Cappuccino', quantity: 1 }]));
  act(() => result.current.emptyCart());
  act(() => result.current.syncCartFromOrder([{ item: 'Latte', quantity: 1 }]));
  expect(result.current.cartItems['latte']).toBe(1);
  expect(result.current.cartItems['cappuccino']).toBeUndefined();
});
