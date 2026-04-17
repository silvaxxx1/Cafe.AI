import { Text, View, TouchableOpacity, ScrollView, StatusBar, StyleSheet } from 'react-native';
import React from 'react';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { router } from 'expo-router';
import { useLocalSearchParams } from 'expo-router';
import PageHeader from '@/components/PageHeader';
import { useCart } from '@/components/CartContext';
import Toast from 'react-native-root-toast';
import DescriptionSection from '@/components/DescriptionSection';
import SizesSection from '@/components/SizesSection';
import DetailsHeader from '@/components/DetailsHeader';
import { useTheme } from '@/constants/theme';

const DetailsPage = () => {
  const { addToCart } = useCart();
  const theme = useTheme();

  const { name, image_url, type, description, price, rating } = useLocalSearchParams() as {
    name: string;
    image_url: string;
    type: string;
    description: string;
    price: string;
    rating: string;
  };

  const handleAddToBag = () => {
    addToCart(name, 1);
    Toast.show(`${name} added to your bag`, { duration: Toast.durations.SHORT });
    router.back();
  };

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <StatusBar barStyle={theme.statusBar} backgroundColor={theme.surface} />
      <PageHeader title={type} showHeaderRight={true} bgColor={theme.surface} />

      <View style={[styles.container, { backgroundColor: theme.bg }]}>
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          <DetailsHeader
            image_url={image_url}
            name={name}
            type={type}
            rating={Number(rating)}
          />
          <DescriptionSection description={description} />
          <SizesSection />
          <View style={{ height: 120 }} />
        </ScrollView>

        {/* Fixed bottom action bar */}
        <View style={[styles.actionBar, { backgroundColor: theme.surface, borderTopColor: theme.border }]}>
          <View>
            <Text style={[styles.priceLabel, { color: theme.textFaint }]}>Price</Text>
            <Text style={[styles.priceValue, { color: theme.accent }]}>${price}</Text>
          </View>

          <TouchableOpacity
            style={[styles.addBtn, { backgroundColor: theme.accent }]}
            onPress={handleAddToBag}
            activeOpacity={0.85}
            accessibilityRole="button"
            accessibilityLabel={`Add ${name} to bag`}
          >
            <Text style={[styles.addBtnText, { color: theme.onAccent }]}>Add to Bag</Text>
          </TouchableOpacity>
        </View>
      </View>
    </GestureHandlerRootView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 4,
  },
  actionBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 36,
    borderTopWidth: 1,
  },
  priceLabel: {
    fontFamily: 'Sora-Regular',
    fontSize: 12,
    letterSpacing: 0.3,
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  priceValue: {
    fontFamily: 'Sora-ExtraBold',
    fontSize: 26,
  },
  addBtn: {
    paddingVertical: 16,
    paddingHorizontal: 36,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  addBtnText: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 16,
    letterSpacing: 0.2,
  },
});

export default DetailsPage;
