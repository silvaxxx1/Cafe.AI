import React, { useState } from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import SizesSection, { SIZE_MODIFIERS } from '../SizesSection';

// Controlled wrapper so we can test state changes
const Controlled = ({ initial = 'M' }: { initial?: string }) => {
  const [size, setSize] = useState(initial);
  return <SizesSection selectedSize={size} onSizeChange={setSize} />;
};

// ── SIZE_MODIFIERS constant ───────────────────────────────────────────────────

test('SIZE_MODIFIERS has correct values', () => {
  expect(SIZE_MODIFIERS.S).toBe(-0.5);
  expect(SIZE_MODIFIERS.M).toBe(0);
  expect(SIZE_MODIFIERS.L).toBe(0.5);
});

// ── rendering ─────────────────────────────────────────────────────────────────

test('renders all three size buttons', () => {
  const { getByText } = render(<Controlled />);
  expect(getByText('S')).toBeTruthy();
  expect(getByText('M')).toBeTruthy();
  expect(getByText('L')).toBeTruthy();
});

test('renders volume labels', () => {
  const { getByText } = render(<Controlled />);
  expect(getByText('8 oz')).toBeTruthy();
  expect(getByText('12 oz')).toBeTruthy();
  expect(getByText('16 oz')).toBeTruthy();
});

test('renders price modifier labels', () => {
  const { getByText } = render(<Controlled />);
  expect(getByText('-$0.50')).toBeTruthy();
  expect(getByText('base')).toBeTruthy();
  expect(getByText('+$0.50')).toBeTruthy();
});

// ── interaction ───────────────────────────────────────────────────────────────

test('calls onSizeChange when a size is tapped', () => {
  const onChange = jest.fn();
  const { getByText } = render(
    <SizesSection selectedSize="M" onSizeChange={onChange} />
  );
  fireEvent.press(getByText('L'));
  expect(onChange).toHaveBeenCalledWith('L');
});

test('calls onSizeChange with S when S is tapped', () => {
  const onChange = jest.fn();
  const { getByText } = render(
    <SizesSection selectedSize="M" onSizeChange={onChange} />
  );
  fireEvent.press(getByText('S'));
  expect(onChange).toHaveBeenCalledWith('S');
});

test('controlled — changing size updates the selected button', () => {
  const { getByText, rerender } = render(
    <SizesSection selectedSize="M" onSizeChange={jest.fn()} />
  );
  // Re-render with L selected — no crash, correct label still visible
  rerender(<SizesSection selectedSize="L" onSizeChange={jest.fn()} />);
  expect(getByText('L')).toBeTruthy();
});
