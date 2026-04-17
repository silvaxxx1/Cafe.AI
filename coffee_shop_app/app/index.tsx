/// <reference types="nativewind/types" />
import { Text, View, StatusBar, ImageBackground, StyleSheet } from "react-native";
import { GestureHandlerRootView, TouchableOpacity } from "react-native-gesture-handler";
import { router } from "expo-router";
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '@/constants/theme';

export default function Index() {
  const theme = useTheme();

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ImageBackground
        source={require('../assets/images/index_bg_image.png')}
        style={styles.bg}
        resizeMode="cover"
      >
        {/* Gradient overlay — bottom-weighted dark to transparent */}
        <View style={styles.overlay} />

        <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
          <View style={styles.content}>

            {/* Eyebrow label */}
            <Text style={styles.eyebrow}>FERO CAFE</Text>

            {/* Big display headline */}
            <Text style={styles.headline}>Your cup,{'\n'}your way.</Text>

            {/* Tagline */}
            <Text style={styles.tagline}>
              Every drink crafted to order.{'\n'}Tell us what you're in the mood for.
            </Text>

            {/* CTA */}
            <TouchableOpacity
              style={[styles.cta, { backgroundColor: theme.accent }]}
              onPress={() => router.push("/(tabs)/home")}
              activeOpacity={0.85}
            >
              <Text style={[styles.ctaText, { color: theme.onAccent }]}>Explore the menu</Text>
            </TouchableOpacity>

            {/* Chat CTA */}
            <TouchableOpacity
              style={styles.ctaSecondary}
              onPress={() => router.push("/(tabs)/chatRoom")}
              activeOpacity={0.7}
            >
              <Text style={[styles.ctaSecondaryText, { color: theme.accent }]}>Or chat with our AI barista →</Text>
            </TouchableOpacity>

          </View>
        </SafeAreaView>
      </ImageBackground>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  bg: {
    flex: 1,
    width: '100%',
    height: '100%',
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(22, 12, 8, 0.55)',
  },
  safe: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  content: {
    paddingHorizontal: 32,
    paddingBottom: 48,
  },
  eyebrow: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 11,
    letterSpacing: 3,
    color: '#D4896A',
    marginBottom: 16,
    textTransform: 'uppercase',
  },
  headline: {
    fontFamily: 'Sora-ExtraBold',
    fontSize: 52,
    lineHeight: 58,
    color: '#F5EDE4',
    marginBottom: 20,
  },
  tagline: {
    fontFamily: 'Sora-Regular',
    fontSize: 15,
    lineHeight: 24,
    color: 'rgba(245, 237, 228, 0.7)',
    marginBottom: 40,
  },
  cta: {
    paddingVertical: 18,
    paddingHorizontal: 32,
    borderRadius: 14,
    alignItems: 'center',
    marginBottom: 16,
  },
  ctaText: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 17,
    letterSpacing: 0.3,
  },
  ctaSecondary: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  ctaSecondaryText: {
    fontFamily: 'Sora-Regular',
    fontSize: 14,
    letterSpacing: 0.2,
  },
});
