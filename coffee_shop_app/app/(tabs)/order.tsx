import { Text, View, StatusBar, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { useEffect, useState, useMemo, useCallback } from 'react';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import React from 'react';
import Ionicons from '@expo/vector-icons/Ionicons';
import { Product } from '@/types/types';
import { fetchProducts } from '@/services/productService';
import ProductList from '@/components/CartProductList';
import { useCart } from '@/components/CartContext';
import Toast from 'react-native-root-toast';
import { router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '@/constants/theme';

const Order = () => {
  const { cartItems, SetQuantityCart, emptyCart } = useCart();
  const theme = useTheme();

  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const totalPrice = useMemo(
    () => products.reduce((total, p) => total + p.price * (cartItems[p.name] || 0), 0),
    [products, cartItems]
  );

  const itemCount = useMemo(
    () => Object.values(cartItems).reduce((sum, q) => sum + q, 0),
    [cartItems]
  );

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchProducts()
      .then(setProducts)
      .catch(() => setError("Couldn't load the menu. Check your connection and try again."))
      .finally(() => setLoading(false));
  }, [retryCount]);

  const orderNow = useCallback(() => {
    emptyCart();
    Toast.show('Order placed!', { duration: Toast.durations.SHORT });
    router.push('/thankyou');
  }, [emptyCart]);

  if (loading) {
    return (
      <View style={[styles.centered, { backgroundColor: theme.bg }]}>
        <ActivityIndicator size="large" color={theme.accent} />
      </View>
    );
  }

  if (error) {
    return (
      <View style={[styles.centered, { backgroundColor: theme.bg }]}>
        <Text style={[styles.errorText, { color: theme.text }]}>{error}</Text>
        <TouchableOpacity
          onPress={() => setRetryCount((c) => c + 1)}
          style={[styles.retryBtn, { borderColor: theme.accent }]}
          activeOpacity={0.8}
          accessibilityRole="button"
          accessibilityLabel="Retry loading menu"
        >
          <Text style={[styles.retryBtnText, { color: theme.accent }]}>Try again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <StatusBar barStyle={theme.statusBar} backgroundColor={theme.surface} />
      <SafeAreaView style={[styles.safe, { backgroundColor: theme.bg }]} edges={['top']}>

        {/* Header */}
        <View style={[styles.header, { backgroundColor: theme.surface, borderBottomColor: theme.border }]}>
          <View>
            <Text style={[styles.headerTitle, { color: theme.text }]}>Your Bag</Text>
            <Text style={[styles.headerSub, { color: theme.textMuted }]}>
              {itemCount === 0 ? 'Nothing here yet' : `${itemCount} item${itemCount !== 1 ? 's' : ''}`}
            </Text>
          </View>
          {itemCount > 0 && (
            <TouchableOpacity
              onPress={emptyCart}
              style={[styles.clearBtn, { borderColor: theme.destructive }]}
              activeOpacity={0.7}
              accessibilityLabel="Clear all items from bag"
              accessibilityRole="button"
            >
              <Text style={[styles.clearBtnText, { color: theme.destructive }]}>Clear</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Product list */}
        <View style={[styles.listArea, { backgroundColor: theme.bg }]}>
          <ProductList
            products={products}
            quantities={cartItems}
            setQuantities={SetQuantityCart}
          />
        </View>

        {/* Footer */}
        <View style={[styles.footer, { backgroundColor: theme.surface, borderTopColor: theme.border }]}>

          {totalPrice > 0 && (
            <View style={styles.summaryRows}>
              <View style={styles.summaryRow}>
                <Text style={[styles.summaryLabel, { color: theme.textMuted }]}>Subtotal</Text>
                <Text style={[styles.summaryValue, { color: theme.text }]}>${totalPrice.toFixed(2)}</Text>
              </View>
              <View style={styles.summaryRow}>
                <Text style={[styles.summaryLabel, { color: theme.textMuted }]}>Delivery</Text>
                <Text style={[styles.summaryValue, { color: theme.text }]}>$1.00</Text>
              </View>
              <View style={[styles.summaryDivider, { backgroundColor: theme.border }]} />
              <View style={styles.summaryRow}>
                <Text style={[styles.totalLabel, { color: theme.text }]}>Total</Text>
                <Text style={[styles.totalValue, { color: theme.accent }]}>${(totalPrice + 1).toFixed(2)}</Text>
              </View>
            </View>
          )}

          {totalPrice > 0 && (
            <View style={[styles.paymentRow, { borderColor: theme.border }]}>
              <Ionicons name="wallet-outline" size={20} color={theme.accent} />
              <Text style={[styles.paymentText, { color: theme.text }]}>Cash / Wallet</Text>
            </View>
          )}

          <TouchableOpacity
            style={[
              styles.orderBtn,
              { backgroundColor: totalPrice === 0 ? theme.surfaceAlt : theme.accent },
            ]}
            disabled={totalPrice === 0}
            onPress={orderNow}
            activeOpacity={0.85}
            accessibilityRole="button"
            accessibilityLabel={totalPrice === 0 ? 'Add items to order' : `Place order for $${(totalPrice + 1).toFixed(2)}`}
            accessibilityState={{ disabled: totalPrice === 0 }}
          >
            <Text style={[styles.orderBtnText, { color: totalPrice === 0 ? theme.textFaint : theme.onAccent }]}>
              {totalPrice === 0 ? 'Add items to order' : `Place order · $${(totalPrice + 1).toFixed(2)}`}
            </Text>
          </TouchableOpacity>

        </View>
      </SafeAreaView>
    </GestureHandlerRootView>
  );
};

const styles = StyleSheet.create({
  safe: {
    flex: 1,
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
    paddingHorizontal: 32,
  },
  errorText: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
  },
  retryBtn: {
    paddingVertical: 12,
    paddingHorizontal: 28,
    borderRadius: 12,
    borderWidth: 1,
  },
  retryBtnText: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 15,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingVertical: 20,
    borderBottomWidth: 1,
  },
  headerTitle: {
    fontFamily: 'Sora-ExtraBold',
    fontSize: 26,
  },
  headerSub: {
    fontFamily: 'Sora-Regular',
    fontSize: 13,
    marginTop: 2,
  },
  clearBtn: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 10,
    borderWidth: 1,
  },
  clearBtnText: {
    fontFamily: 'Sora-Medium',
    fontSize: 13,
  },
  listArea: {
    flex: 1,
  },
  footer: {
    paddingHorizontal: 24,
    paddingTop: 20,
    paddingBottom: 32,
    borderTopWidth: 1,
    gap: 12,
  },
  summaryRows: {
    gap: 10,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  summaryLabel: {
    fontFamily: 'Sora-Regular',
    fontSize: 14,
  },
  summaryValue: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 14,
  },
  summaryDivider: {
    height: 1,
    marginVertical: 4,
  },
  totalLabel: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 16,
  },
  totalValue: {
    fontFamily: 'Sora-Bold',
    fontSize: 20,
  },
  paymentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  paymentText: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 14,
  },
  orderBtn: {
    paddingVertical: 18,
    borderRadius: 16,
    alignItems: 'center',
    marginTop: 4,
  },
  orderBtnText: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 16,
    letterSpacing: 0.2,
  },
});

export default Order;
