import React from 'react';
import { render } from '@testing-library/react-native';
import MessageItem from '../MessageItem';
import { Product } from '@/types/types';

const makeProduct = (name: string): Product => ({
  id: name,
  name,
  category: 'Coffee',
  description: 'A fine coffee.',
  image_url: 'cappuccino.jpg',
  price: 4.5,
  rating: 4.8,
});

const productMap = {
  cappuccino: makeProduct('Cappuccino'),
  latte: makeProduct('Latte'),
  croissant: { ...makeProduct('Croissant'), category: 'Bakery', image_url: 'Croissant.jpg' },
};

// ── user messages ─────────────────────────────────────────────────────────────

test('renders user message content', () => {
  const { getByText } = render(
    <MessageItem message={{ role: 'user', content: 'I want a latte' }} />
  );
  expect(getByText('I want a latte')).toBeTruthy();
});

test('user message does not show the Fero label', () => {
  const { queryByText } = render(
    <MessageItem message={{ role: 'user', content: 'Hello' }} />
  );
  expect(queryByText('Fero')).toBeNull();
});

// ── assistant messages ────────────────────────────────────────────────────────

test('renders assistant message content', () => {
  const { getByText } = render(
    <MessageItem message={{ role: 'assistant', content: 'Sure! One latte coming up.' }} />
  );
  expect(getByText('Sure! One latte coming up.')).toBeTruthy();
});

test('assistant bubble shows the Fero label', () => {
  const { getByText } = render(
    <MessageItem message={{ role: 'assistant', content: 'Hello' }} />
  );
  expect(getByText('Fero')).toBeTruthy();
});

// ── product image cards — recommendation agent ────────────────────────────────

test('shows product name cards for recommendation_agent memory', () => {
  const { getByText } = render(
    <MessageItem
      message={{
        role: 'assistant',
        content: 'Here are my picks!',
        memory: { agent: 'recommendation_agent', last_recommendations: ['Cappuccino', 'Latte'] },
      }}
      productMap={productMap}
    />
  );
  expect(getByText('Cappuccino')).toBeTruthy();
  expect(getByText('Latte')).toBeTruthy();
});

test('shows no cards when last_recommendations is empty', () => {
  const { queryByText } = render(
    <MessageItem
      message={{
        role: 'assistant',
        content: 'Nothing to suggest right now.',
        memory: { agent: 'recommendation_agent', last_recommendations: [] },
      }}
      productMap={productMap}
    />
  );
  expect(queryByText('Cappuccino')).toBeNull();
});

test('silently skips products not found in productMap', () => {
  const { queryByText } = render(
    <MessageItem
      message={{
        role: 'assistant',
        content: 'Check this out!',
        memory: { agent: 'recommendation_agent', last_recommendations: ['UnknownItem'] },
      }}
      productMap={productMap}
    />
  );
  expect(queryByText('UnknownItem')).toBeNull();
});

// ── product image cards — order agent ────────────────────────────────────────

test('shows order items on step 6 (final order summary)', () => {
  const { getByText } = render(
    <MessageItem
      message={{
        role: 'assistant',
        content: 'Your order is confirmed!',
        memory: {
          agent: 'order_taking_agent',
          'step number': '6',
          order: [
            { item: 'Cappuccino', quantity: 1, price: 4.5 },
            { item: 'Croissant', quantity: 1, price: 3.25 },
          ],
          asked_recommendation_before: true,
        },
      }}
      productMap={productMap}
    />
  );
  expect(getByText('Cappuccino')).toBeTruthy();
  expect(getByText('Croissant')).toBeTruthy();
});

test('does not show order items on intermediate steps', () => {
  const { queryByText } = render(
    <MessageItem
      message={{
        role: 'assistant',
        content: 'What else would you like?',
        memory: {
          agent: 'order_taking_agent',
          'step number': '3',
          order: [{ item: 'Cappuccino', quantity: 1, price: 4.5 }],
          asked_recommendation_before: false,
        },
      }}
      productMap={productMap}
    />
  );
  expect(queryByText('Cappuccino')).toBeNull();
});

test('no cards rendered when no memory is set', () => {
  const { queryByText } = render(
    <MessageItem
      message={{ role: 'assistant', content: 'How can I help?' }}
      productMap={productMap}
    />
  );
  // Only "Fero" label should exist — no product names
  expect(queryByText('Cappuccino')).toBeNull();
  expect(queryByText('Latte')).toBeNull();
});
