import { fireBaseDB } from '../config/firebaseConfig';
import { Product } from '../types/types';
import { ref, get } from 'firebase/database';

const fetchProducts = async (): Promise<Product[]> => {
  if (!fireBaseDB) {
    console.warn('[productService] Firebase not configured — returning empty product list.');
    return [];
  }

  const productsRef = ref(fireBaseDB, 'products');
  const snapshot = await get(productsRef);
  const data = snapshot.val();

  const products: Product[] = [];
  if (data) {
    for (const key in data) {
      if (data.hasOwnProperty(key)) {
        products.push({ ...data[key] });
      }
    }
  }

  return products;
};

export { fetchProducts };