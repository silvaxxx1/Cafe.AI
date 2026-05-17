// Mock Firebase before importing productService.
// firebase/database ships as ESM and can't be parsed by Jest's CommonJS transform.
jest.mock('firebase/database', () => ({ ref: jest.fn(), get: jest.fn() }));
jest.mock('../../config/firebaseConfig', () => ({ fireBaseDB: null }));

import { fetchProducts, clearProductCache } from '../productService';

beforeEach(() => {
  clearProductCache();
});

test('returns empty array when Firebase is not configured', async () => {
  const products = await fetchProducts();
  expect(products).toEqual([]);
});

test('second call returns same array reference (cache hit)', async () => {
  const first = await fetchProducts();
  const second = await fetchProducts();
  expect(second).toBe(first);
});

test('two simultaneous calls resolve to the same promise (in-flight dedup)', async () => {
  const p1 = fetchProducts();
  const p2 = fetchProducts();
  const [r1, r2] = await Promise.all([p1, p2]);
  expect(r1).toBe(r2);
});

test('clearProductCache forces a fresh fetch on next call', async () => {
  const first = await fetchProducts();
  clearProductCache();
  const second = await fetchProducts();
  // Both return [] (Firebase not configured), but they are different array instances
  expect(second).not.toBe(first);
  expect(second).toEqual([]);
});
