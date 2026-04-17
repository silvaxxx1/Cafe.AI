import { fireBaseDB } from '../config/firebaseConfig';
import { Product } from '../types/types';
import { ref, get } from 'firebase/database';

let cache: Product[] | null = null;
let inflight: Promise<Product[]> | null = null;

const fetchProducts = async (): Promise<Product[]> => {
  if (cache !== null) return cache;
  if (inflight) return inflight;

  inflight = (async () => {
    if (!fireBaseDB) {
      console.warn('[productService] Firebase not configured — returning empty product list.');
      return [];
    }
    const snapshot = await get(ref(fireBaseDB, 'products'));
    const data = snapshot.val();
    const products: Product[] = [];
    if (data) {
      for (const key in data) {
        if (Object.prototype.hasOwnProperty.call(data, key)) {
          products.push({ ...data[key] });
        }
      }
    }
    cache = products;
    inflight = null;
    return products;
  })();

  return inflight;
};

/** Call during logout or pull-to-refresh to force a fresh fetch. */
const clearProductCache = () => {
  cache = null;
  inflight = null;
};

export { fetchProducts, clearProductCache };
