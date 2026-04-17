import React from 'react';
import { View, Text, Image, TouchableOpacity, FlatList, StyleSheet } from 'react-native';
import { Product } from '@/types/types';
import productImages from '@/constants/productImages';
import { useTheme } from '@/constants/theme';

interface ProductListProps {
  products: Product[];
  quantities: { [key: string]: number };
  setQuantities: (itemKey: string, delta: number) => void;
}

const ProductList: React.FC<ProductListProps> = ({ products, quantities, setQuantities }) => {
  const theme = useTheme();
  const filteredProducts = products.filter((p) => (quantities[p.name] || 0) > 0);

  const renderItem = ({ item }: { item: Product }) => (
    <View style={[styles.row, { borderBottomColor: theme.border }]}>
      <Image
        source={productImages[item.image_url]}
        style={styles.image}
        resizeMode="cover"
      />
      <View style={styles.info}>
        <Text style={[styles.name, { color: theme.text }]} numberOfLines={2}>{item.name}</Text>
        <Text style={[styles.category, { color: theme.textFaint }]}>{item.category}</Text>
        <Text style={[styles.price, { color: theme.accent }]}>${(item.price * (quantities[item.name] || 0)).toFixed(2)}</Text>
      </View>
      <View style={styles.qtyControls}>
        <TouchableOpacity
          onPress={() => setQuantities(item.name, -1)}
          style={[styles.qtyBtn, { borderColor: theme.border }]}
          accessibilityLabel={`Remove one ${item.name}`}
          accessibilityRole="button"
          hitSlop={{ top: 4, bottom: 4, left: 4, right: 4 }}
        >
          <Text style={[styles.qtyBtnText, { color: theme.text }]}>−</Text>
        </TouchableOpacity>
        <Text
          style={[styles.qtyCount, { color: theme.text }]}
          accessibilityLabel={`${quantities[item.name] || 0} in bag`}
        >
          {quantities[item.name] || 0}
        </Text>
        <TouchableOpacity
          onPress={() => setQuantities(item.name, 1)}
          style={[styles.qtyBtn, { backgroundColor: theme.accent, borderColor: theme.accent }]}
          accessibilityLabel={`Add one more ${item.name}`}
          accessibilityRole="button"
          hitSlop={{ top: 4, bottom: 4, left: 4, right: 4 }}
        >
          <Text style={[styles.qtyBtnText, { color: theme.onAccent }]}>+</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  if (filteredProducts.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={[styles.emptyIcon]}>☕</Text>
        <Text style={[styles.emptyTitle, { color: theme.text }]}>Your bag is empty</Text>
        <Text style={[styles.emptyBody, { color: theme.textMuted }]}>
          Browse the menu or chat with Fero to discover something great.
        </Text>
      </View>
    );
  }

  return (
    <FlatList
      data={filteredProducts}
      renderItem={renderItem}
      keyExtractor={(item) => item.name}
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.list}
    />
  );
};

const styles = StyleSheet.create({
  list: {
    paddingTop: 8,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 16,
    borderBottomWidth: 1,
    gap: 14,
  },
  image: {
    width: 64,
    height: 64,
    borderRadius: 12,
    flexShrink: 0,
  },
  info: {
    flex: 1,
    gap: 3,
  },
  name: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 14,
    lineHeight: 20,
  },
  category: {
    fontFamily: 'Sora-Regular',
    fontSize: 11,
    letterSpacing: 0.3,
    textTransform: 'uppercase',
  },
  price: {
    fontFamily: 'Sora-Bold',
    fontSize: 15,
    marginTop: 2,
  },
  qtyControls: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flexShrink: 0,
  },
  qtyBtn: {
    width: 40,
    height: 40,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  qtyBtnText: {
    fontFamily: 'Sora-Bold',
    fontSize: 16,
    lineHeight: 20,
  },
  qtyCount: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 15,
    minWidth: 20,
    textAlign: 'center',
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 40,
    paddingVertical: 60,
    gap: 12,
  },
  emptyIcon: {
    fontSize: 40,
    marginBottom: 8,
  },
  emptyTitle: {
    fontFamily: 'Sora-ExtraBold',
    fontSize: 22,
    textAlign: 'center',
  },
  emptyBody: {
    fontFamily: 'Sora-Regular',
    fontSize: 15,
    lineHeight: 24,
    textAlign: 'center',
  },
});

export default ProductList;
