import { Text, View, Image, StyleSheet } from 'react-native';
import React from 'react';
import { useTheme } from '@/constants/theme';

const Banner = () => {
  const theme = useTheme();

  return (
    <View style={[styles.wrapper, { backgroundColor: theme.surface }]}>
      <View style={styles.imageContainer}>
        <Image
          source={require('../assets/images/banner.png')}
          style={styles.image}
          resizeMode="cover"
        />
        {/* Overlay with promo text */}
        <View style={styles.overlay}>
          <View style={[styles.badge, { backgroundColor: '#ED5151' }]}>
            <Text style={styles.badgeText} accessibilityLabel="Promotion">PROMO</Text>
          </View>
          <Text style={[styles.promoLine, { color: theme.onAccent }]}>Buy one</Text>
          <Text style={[styles.promoLineAccent, { color: theme.accent }]}>get one FREE</Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 4,
  },
  imageContainer: {
    borderRadius: 20,
    overflow: 'hidden',
    height: 140,
  },
  image: {
    width: '100%',
    height: '100%',
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    paddingLeft: 24,
    backgroundColor: 'rgba(26, 18, 16, 0.45)',
  },
  badge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    marginBottom: 10,
  },
  badgeText: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 10,
    letterSpacing: 1.5,
    color: '#fff',
  },
  promoLine: {
    fontFamily: 'Sora-ExtraBold',
    fontSize: 26,
    lineHeight: 30,
  },
  promoLineAccent: {
    fontFamily: 'Sora-ExtraBold',
    fontSize: 26,
    lineHeight: 32,
  },
});

export default React.memo(Banner);
