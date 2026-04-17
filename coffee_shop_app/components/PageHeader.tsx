import React from 'react';
import { Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { router, Stack } from 'expo-router';
import { useTheme } from '@/constants/theme';

interface HeaderProps {
  title: string;
  showHeaderRight: boolean;
  bgColor?: string;
}

const PageHeader: React.FC<HeaderProps> = ({ title, showHeaderRight, bgColor }) => {
  const theme = useTheme();
  const bg = bgColor ?? theme.surface;

  return (
    <Stack.Screen
      options={{
        headerShadowVisible: false,
        headerStyle: {
          backgroundColor: bg,
        },
        headerTitleAlign: 'center',
        headerTitle: () => (
          <Text style={[styles.title, { color: theme.text }]}>{title}</Text>
        ),
        headerRight: showHeaderRight
          ? () => (
              <Feather
                style={{ marginRight: 10 }}
                name="heart"
                size={22}
                color={theme.text}
              />
            )
          : undefined,
        headerBackVisible: false,
        headerLeft: () => (
          <GestureHandlerRootView style={styles.backContainer}>
            <TouchableOpacity
              onPress={() => router.back()}
              style={styles.backBtn}
              activeOpacity={0.7}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              accessibilityRole="button"
              accessibilityLabel="Go back"
            >
              <Feather name="arrow-left" size={22} color={theme.text} />
            </TouchableOpacity>
          </GestureHandlerRootView>
        ),
      }}
    />
  );
};

const styles = StyleSheet.create({
  title: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 17,
  },
  backContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  backBtn: {
    paddingLeft: 8,
    paddingVertical: 4,
  },
});

export default PageHeader;
