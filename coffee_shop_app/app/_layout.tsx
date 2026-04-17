import '../polyfills';
import { CartProvider } from '@/components/CartContext';
import { Stack } from 'expo-router/stack';
import { RootSiblingParent } from 'react-native-root-siblings';
import { useFonts } from "expo-font";
import { NativeWindStyleSheet } from "nativewind";
import { Platform, View, StyleSheet, useColorScheme } from 'react-native';

NativeWindStyleSheet.setOutput({
  default: "native",
});

export default function RootLayout() {
  const [fontsLoaded] = useFonts({
    "Sora-Regular": require("../assets/fonts/Sora-Regular.ttf"),
    "Sora-Medium": require("../assets/fonts/Sora-Medium.ttf"),
    "Sora-SemiBold": require("../assets/fonts/Sora-SemiBold.ttf"),
    "Sora-Bold": require("../assets/fonts/Sora-Bold.ttf"),
    "Sora-ExtraBold": require("../assets/fonts/Sora-ExtraBold.ttf"),
  });

  const scheme = useColorScheme();

  if (!fontsLoaded) {
    return undefined;
  }

  const nav = (
    <Stack>
      <Stack.Screen name="index" options={{ headerShown: false }} />
      <Stack.Screen name="details" options={{ headerShown: true }} />
      <Stack.Screen name="thankyou" options={{ headerShown: false }} />
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
    </Stack>
  );

  return (
    <CartProvider>
      <RootSiblingParent>
        {Platform.OS === 'web' ? (
          <View
            style={[
              styles.webOuter,
              { backgroundColor: scheme === 'dark' ? '#0D0A09' : '#D9D3CC' },
            ]}
          >
            <View style={styles.webFrame}>
              {nav}
            </View>
          </View>
        ) : nav}
      </RootSiblingParent>
    </CartProvider>
  );
}

const styles = StyleSheet.create({
  webOuter: {
    flex: 1,
    alignItems: 'center',
  },
  webFrame: {
    flex: 1,
    width: '100%',
    maxWidth: 480,
  },
});
