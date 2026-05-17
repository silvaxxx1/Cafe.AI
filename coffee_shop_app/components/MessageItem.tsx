import { Text, View, Image, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import React from 'react';
import { MessageInterface, Product, OrderMemory, RecommendationMemory } from '@/types/types';
import { useTheme } from '@/constants/theme';
import { webSelectText } from '@/constants/responsive';
import productImages from '@/constants/productImages';
import { router } from 'expo-router';

interface MessageItemProps {
  message: MessageInterface;
  productMap?: Record<string, Product>;
}

// Returns product names to show as image cards beneath the bubble, or empty array.
function getProductsToShow(message: MessageInterface): string[] {
  const mem = message.memory;
  if (!mem) return [];

  if (mem.agent === 'recommendation_agent') {
    return (mem as RecommendationMemory).last_recommendations ?? [];
  }

  if (mem.agent === 'order_taking_agent') {
    const orderMem = mem as OrderMemory;
    // Only show on the final step — when the agent closes the order with a total
    if (orderMem['step number'] === '6') {
      return (orderMem.order ?? []).map((o) => o.item);
    }
  }

  return [];
}

const ProductCard = ({ product }: { product: Product }) => {
  const theme = useTheme();
  const image = productImages[product.image_url];

  const handlePress = () => {
    router.push({
      pathname: '/details',
      params: {
        name: product.name,
        image_url: product.image_url,
        type: product.category,
        price: String(product.price),
        rating: String(product.rating ?? 4.5),
        description: product.description ?? '',
      },
    });
  };

  return (
    <TouchableOpacity
      onPress={handlePress}
      style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}
      activeOpacity={0.8}
      accessibilityRole="button"
      accessibilityLabel={`View ${product.name}`}
    >
      {image && (
        <Image source={image} style={styles.cardImage} resizeMode="cover" />
      )}
      <Text style={[styles.cardName, { color: theme.text }]} numberOfLines={2}>
        {product.name}
      </Text>
      <Text style={[styles.cardPrice, { color: theme.accent }]}>${product.price.toFixed(2)}</Text>
    </TouchableOpacity>
  );
};

const MessageItem = ({ message, productMap = {} }: MessageItemProps) => {
  const theme = useTheme();

  if (message?.role === 'user') {
    return (
      <View style={styles.userRow}>
        <View
          style={[
            styles.userBubble,
            { backgroundColor: theme.userBubble, borderColor: theme.userBubbleBorder },
          ]}
        >
          <Text style={[styles.userText, { color: theme.text }, webSelectText]}>{message?.content}</Text>
        </View>
      </View>
    );
  }

  const productNames = getProductsToShow(message);
  const products = productNames
    .map((name) => productMap[name.trim().toLowerCase()])
    .filter((p): p is Product => p !== undefined);

  return (
    <View style={styles.assistantRow}>
      {/* Barista avatar mark */}
      <View style={[styles.avatar, { backgroundColor: theme.accent }]}>
        <Text style={[styles.avatarText, { color: theme.onAccent }]}>F</Text>
      </View>

      <View style={styles.assistantContent}>
        <View style={[styles.assistantBubble, { backgroundColor: theme.assistantBubble }]}>
          <Text style={[styles.assistantLabel, { color: theme.accent }]}>Fero</Text>
          <Text style={[styles.assistantText, { color: theme.text }, webSelectText]}>{message?.content}</Text>
        </View>

        {products.length > 0 && (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.cardStrip}
          >
            {products.map((p) => (
              <ProductCard key={p.name} product={p} />
            ))}
          </ScrollView>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  userRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginBottom: 12,
    marginRight: 16,
    marginLeft: 64,
  },
  userBubble: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 18,
    borderTopRightRadius: 4,
    borderWidth: 1,
    maxWidth: '100%',
  },
  userText: {
    fontFamily: 'Sora-Regular',
    fontSize: 15,
    lineHeight: 22,
  },
  assistantRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
    marginLeft: 16,
    marginRight: 16,
    gap: 10,
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
    flexShrink: 0,
  },
  avatarText: {
    fontFamily: 'Sora-Bold',
    fontSize: 14,
  },
  assistantContent: {
    flex: 1,
    gap: 10,
  },
  assistantBubble: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 18,
    borderTopLeftRadius: 4,
  },
  assistantLabel: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 11,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  assistantText: {
    fontFamily: 'Sora-Regular',
    fontSize: 15,
    lineHeight: 23,
  },
  cardStrip: {
    gap: 10,
    paddingRight: 8,
  },
  card: {
    width: 120,
    borderRadius: 14,
    borderWidth: 1,
    overflow: 'hidden',
    padding: 8,
    gap: 6,
  },
  cardImage: {
    width: '100%',
    height: 80,
    borderRadius: 8,
  },
  cardName: {
    fontFamily: 'Sora-Medium',
    fontSize: 11,
    lineHeight: 15,
  },
  cardPrice: {
    fontFamily: 'Sora-Bold',
    fontSize: 12,
  },
});

export default MessageItem;
