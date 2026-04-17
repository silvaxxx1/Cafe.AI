import { Text, View, StatusBar, StyleSheet } from 'react-native';
import React from 'react';
import { TouchableOpacity, GestureHandlerRootView } from 'react-native-gesture-handler';
import { router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '@/constants/theme';

const ThankyouPage = () => {
  const theme = useTheme();

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <StatusBar barStyle={theme.statusBar} backgroundColor={theme.bg} />
      <SafeAreaView style={[styles.safe, { backgroundColor: theme.bg }]}>
        <View style={styles.content}>

          {/* Success ring */}
          <View style={[styles.iconRing, { backgroundColor: theme.successSubtle }]}>
            <View style={[styles.iconInner, { backgroundColor: theme.success }]}>
              <Text style={styles.emoji}>☕</Text>
            </View>
          </View>

          <View style={styles.textBlock}>
            <Text style={[styles.title, { color: theme.text }]}>Order placed!</Text>
            <Text style={[styles.subtitle, { color: theme.textMuted }]}>
              Your drink is being crafted with care.{'\n'}We'll have it ready shortly.
            </Text>
          </View>

          <TouchableOpacity
            style={[styles.btn, { backgroundColor: theme.accent }]}
            onPress={() => router.push('/(tabs)/home')}
            activeOpacity={0.85}
            accessibilityRole="button"
            accessibilityLabel="Back to menu"
          >
            <Text style={[styles.btnText, { color: theme.onAccent }]}>Back to Menu</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.chatLink}
            onPress={() => router.push('/(tabs)/chatRoom')}
            accessibilityRole="link"
          >
            <Text style={[styles.chatLinkText, { color: theme.textMuted }]}>
              Chat with Fero about your order →
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
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 40,
    gap: 20,
  },
  iconRing: {
    width: 120,
    height: 120,
    borderRadius: 60,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  iconInner: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emoji: {
    fontSize: 34,
  },
  textBlock: {
    alignItems: 'center',
    gap: 10,
  },
  title: {
    fontFamily: 'Sora-ExtraBold',
    fontSize: 32,
    textAlign: 'center',
  },
  subtitle: {
    fontFamily: 'Sora-Regular',
    fontSize: 15,
    lineHeight: 24,
    textAlign: 'center',
  },
  btn: {
    paddingVertical: 18,
    paddingHorizontal: 48,
    borderRadius: 16,
    alignItems: 'center',
    width: '100%',
    marginTop: 8,
  },
  btnText: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 16,
    letterSpacing: 0.2,
  },
  chatLink: {
    paddingVertical: 8,
  },
  chatLinkText: {
    fontFamily: 'Sora-Regular',
    fontSize: 14,
  },
});

export default ThankyouPage;
