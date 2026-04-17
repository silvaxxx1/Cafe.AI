import { useEffect, useState, useCallback } from 'react';
import { Product, ProductCategory } from '@/types/types';
import { fetchProducts } from '@/services/productService';
import { Text, View, Image, FlatList, StatusBar, StyleSheet, ActivityIndicator } from 'react-native';
import React from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { GestureHandlerRootView, TouchableOpacity } from "react-native-gesture-handler";
import { router } from "expo-router";
import AntDesign from '@expo/vector-icons/AntDesign';
import Toast from 'react-native-root-toast';
import { useCart } from '@/components/CartContext';
import Banner from '@/components/Banner';
import SearchArea from '@/components/SearchArea';
import productImages from '@/constants/productImages';
import { useTheme } from '@/constants/theme';
import { useGridColumns, webPointer } from '@/constants/responsive';

const Home = () => {
  const { addToCart } = useCart();
  const theme = useTheme();
  const numColumns = useGridColumns();

  const [products, setProducts] = useState<Product[]>([]);
  const [shownProducts, setShownProducts] = useState<Product[]>([]);
  const [productCategories, setProductCatgories] = useState<ProductCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    const uniqueCategories = productCategories.map((category) => ({
      id: category.id,
      selected: selectedCategory === category.id,
    }));
    setProductCatgories(uniqueCategories);

    if (selectedCategory === 'All') {
      setShownProducts(products);
    } else {
      setShownProducts(products.filter((p) => p.category === selectedCategory));
    }
  }, [selectedCategory]);

  useEffect(() => {
    const loadProducts = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchProducts();
        const cats = data.map((p) => p.category);
        cats.unshift('All');
        const unique = Array.from(new Set(cats)).map((c) => ({ id: c, selected: selectedCategory === c }));
        setProducts(data);
        setShownProducts(data);
        setProductCatgories(unique);
      } catch (err) {
        setError("Couldn't load the menu. Check your connection and try again.");
      } finally {
        setLoading(false);
      }
    };
    loadProducts();
  }, [retryCount]);

  const handleAdd = useCallback((name: string) => {
    addToCart(name, 1);
    Toast.show(`${name} added`, { duration: Toast.durations.SHORT });
  }, [addToCart]);

  const renderItem = useCallback(({ item }: { item: Product }) => (
    <TouchableOpacity
      style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }, webPointer]}
      onPress={() =>
        router.push({
          pathname: '/details',
          params: {
            name: item.name,
            image_url: item.image_url,
            type: item.category,
            price: item.price,
            rating: item.rating,
            description: item.description,
          },
        })
      }
      activeOpacity={0.85}
    >
      <Image
        source={productImages[item.image_url]}
        style={[styles.cardImage, numColumns > 2 && styles.cardImageNarrow]}
        resizeMode="cover"
        accessibilityLabel={`${item.name} product photo`}
      />
      <View style={styles.cardBody}>
        <Text style={[styles.cardCategory, { color: theme.textFaint }]}>{item.category}</Text>
        <Text style={[styles.cardName, { color: theme.text }]} numberOfLines={2}>
          {item.name}
        </Text>
        <View style={styles.cardFooter}>
          <Text style={[styles.cardPrice, { color: theme.accent }]}>${item.price}</Text>
          <TouchableOpacity
            onPress={() => handleAdd(item.name)}
            style={[styles.addBtn, { backgroundColor: theme.accent }]}
            activeOpacity={0.8}
            hitSlop={{ top: 6, bottom: 6, left: 6, right: 6 }}
            accessibilityLabel={`Add ${item.name} to bag`}
            accessibilityRole="button"
          >
            <AntDesign name="plus" size={16} color={theme.onAccent} />
          </TouchableOpacity>
        </View>
      </View>
    </TouchableOpacity>
  ), [theme, numColumns, handleAdd]);

  const renderHeader = useCallback(() => (
    <View>
      <SearchArea />
      <Banner />

      <View style={[styles.categoryRow, { backgroundColor: theme.bg }]}>
        <FlatList
          data={productCategories}
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.categoryContent}
          keyExtractor={(cat) => cat.id}
          renderItem={({ item: cat }) => (
            <TouchableOpacity
              onPress={() => setSelectedCategory(cat.id)}
              activeOpacity={0.7}
              accessibilityRole="button"
              accessibilityLabel={`Filter by ${cat.id}`}
              accessibilityState={{ selected: cat.selected }}
              style={[
                styles.chip,
                cat.selected
                  ? { backgroundColor: theme.accent }
                  : { backgroundColor: theme.surfaceAlt, borderColor: theme.border },
                webPointer,
              ]}
            >
              <Text style={[styles.chipText, { color: cat.selected ? theme.onAccent : theme.textMuted }]}>
                {cat.id}
              </Text>
            </TouchableOpacity>
          )}
        />
      </View>

      <View style={[styles.sectionHeader, { backgroundColor: theme.bg }]}>
        <Text style={[styles.sectionTitle, { color: theme.text }]}>
          {selectedCategory === 'All' ? 'All Items' : selectedCategory}
        </Text>
        <Text style={[styles.sectionCount, { color: theme.textFaint }]}>
          {shownProducts.length} items
        </Text>
      </View>
    </View>
  ), [productCategories, selectedCategory, shownProducts.length, theme]);

  if (loading) {
    return (
      <View style={[styles.centered, { backgroundColor: theme.bg }]}>
        <ActivityIndicator size="large" color={theme.accent} />
        <Text style={[styles.loadingText, { color: theme.textMuted }]}>Loading menu…</Text>
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
          accessibilityRole="button"
          accessibilityLabel="Retry loading menu"
        >
          <Text style={[styles.retryText, { color: theme.accent }]}>Try again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <StatusBar
        barStyle={theme.statusBar}
        backgroundColor={theme.surface}
      />
      <SafeAreaView style={[styles.safe, { backgroundColor: theme.surface }]} edges={['top']}>
        <FlatList
          key={numColumns}
          style={{ backgroundColor: theme.bg }}
          horizontal={false}
          numColumns={numColumns}
          columnWrapperStyle={numColumns === 2 ? styles.columnWrapper2 : styles.columnWrapper3}
          keyExtractor={(item) => item.name}
          data={shownProducts}
          renderItem={renderItem}
          showsVerticalScrollIndicator={false}
          removeClippedSubviews
          maxToRenderPerBatch={8}
          windowSize={5}
          ListHeaderComponent={renderHeader}
          keyboardShouldPersistTaps="handled"
          ListFooterComponent={<View style={{ height: 24 }} />}
        />
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
    gap: 12,
  },
  loadingText: {
    fontFamily: 'Sora-Regular',
    fontSize: 14,
    marginTop: 12,
  },
  errorText: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 16,
    textAlign: 'center',
    paddingHorizontal: 32,
    marginBottom: 16,
  },
  retryBtn: {
    paddingVertical: 12,
    paddingHorizontal: 28,
    borderRadius: 12,
    borderWidth: 1,
  },
  retryText: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 15,
  },
  columnWrapper2: {
    paddingHorizontal: 16,
    gap: 12,
    marginTop: 12,
  },
  columnWrapper3: {
    paddingHorizontal: 12,
    gap: 10,
    marginTop: 12,
  },
  card: {
    flex: 1,
    borderRadius: 18,
    overflow: 'hidden',
    borderWidth: 1,
  },
  cardImage: {
    width: '100%',
    height: 130,
  },
  cardImageNarrow: {
    height: 100,
  },
  cardBody: {
    padding: 12,
  },
  cardCategory: {
    fontFamily: 'Sora-Regular',
    fontSize: 10,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  cardName: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardPrice: {
    fontFamily: 'Sora-Bold',
    fontSize: 16,
  },
  addBtn: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  categoryRow: {
    paddingTop: 20,
    paddingBottom: 4,
  },
  categoryContent: {
    paddingHorizontal: 20,
    gap: 8,
  },
  chip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  chipText: {
    fontFamily: 'Sora-Medium',
    fontSize: 13,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 4,
  },
  sectionTitle: {
    fontFamily: 'Sora-Bold',
    fontSize: 18,
  },
  sectionCount: {
    fontFamily: 'Sora-Regular',
    fontSize: 12,
  },
});

export default Home;
