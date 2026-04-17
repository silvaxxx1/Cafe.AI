import { Text, View, Image, StyleSheet } from 'react-native';
import React from 'react';
import productImages from '@/constants/productImages';
import Octicons from '@expo/vector-icons/Octicons';
import { useTheme } from '@/constants/theme';

interface DetailsHeaderInterface {
  image_url: string;
  name: string;
  type: string;
  rating: number;
}

const DetailsHeader = ({ image_url, name, type, rating }: DetailsHeaderInterface) => {
  const theme = useTheme();

  return (
    <View style={styles.container}>
      <Image
        source={productImages[image_url]}
        style={styles.image}
        resizeMode="cover"
      />

      <View style={styles.info}>
        {/* Category pill */}
        <View style={[styles.typePill, { backgroundColor: theme.accentSubtle }]}>
          <Text style={[styles.typeText, { color: theme.accent }]}>{type}</Text>
        </View>

        {/* Product name */}
        <Text style={[styles.name, { color: theme.text }]}>{name}</Text>

        {/* Rating row */}
        <View style={styles.ratingRow}>
          <Octicons name="star-fill" size={16} color={theme.ratingGold} />
          <Text style={[styles.ratingValue, { color: theme.text }]}>{rating}</Text>
          <Text style={[styles.ratingCount, { color: theme.textFaint }]}>· 128 reviews</Text>
        </View>
      </View>

      <View style={[styles.divider, { backgroundColor: theme.border }]} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: '100%',
  },
  image: {
    width: '100%',
    height: 240,
    borderRadius: 20,
    marginTop: 8,
  },
  info: {
    paddingTop: 20,
    paddingBottom: 4,
    gap: 8,
  },
  typePill: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 20,
  },
  typeText: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 11,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  name: {
    fontFamily: 'Sora-ExtraBold',
    fontSize: 28,
    lineHeight: 34,
  },
  ratingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 4,
  },
  ratingValue: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 15,
  },
  ratingCount: {
    fontFamily: 'Sora-Regular',
    fontSize: 13,
  },
  divider: {
    height: 1,
    marginTop: 20,
    marginBottom: 4,
  },
});

export default DetailsHeader;
