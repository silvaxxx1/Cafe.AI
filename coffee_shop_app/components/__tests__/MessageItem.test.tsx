import React from 'react';
import { render } from '@testing-library/react-native';
import MessageItem from '../MessageItem';

// ── user messages ─────────────────────────────────────────────────────────────

test('renders user message content', () => {
  const { getByText } = render(
    <MessageItem message={{ role: 'user', content: 'I want a latte' }} />
  );
  expect(getByText('I want a latte')).toBeTruthy();
});

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

test('user message does not show the Fero label', () => {
  const { queryByText } = render(
    <MessageItem message={{ role: 'user', content: 'Hello' }} />
  );
  expect(queryByText('Fero')).toBeNull();
});
