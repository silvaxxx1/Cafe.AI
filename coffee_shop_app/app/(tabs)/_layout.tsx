import React from 'react';
import { Tabs } from 'expo-router';
import { Platform } from 'react-native';
import Entypo from '@expo/vector-icons/Entypo';
import { FontAwesome6 } from '@expo/vector-icons';
import { useTheme } from '@/constants/theme';
import { useCart } from '@/components/CartContext';

const TabsLayout = () => {
  const theme = useTheme();
  const { cartItems } = useCart();
  const cartCount = Object.values(cartItems).reduce((sum, q) => sum + q, 0);

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: theme.accent,
        tabBarInactiveTintColor: theme.textFaint,
        tabBarStyle: {
          backgroundColor: theme.tabBar,
          borderTopColor: theme.tabBarBorder,
          borderTopWidth: 1,
          height: Platform.OS === 'ios' ? 84 : 64,
          paddingBottom: Platform.OS === 'ios' ? 28 : 10,
          paddingTop: 8,
          elevation: 0,
          shadowOpacity: 0,
        },
        tabBarLabelStyle: {
          fontFamily: 'Sora-Medium',
          fontSize: 11,
          letterSpacing: 0.2,
        },
        headerStyle: {
          backgroundColor: theme.surface,
          elevation: 0,
          shadowOpacity: 0,
          borderBottomWidth: 0,
        },
        headerTitleStyle: {
          fontFamily: 'Sora-SemiBold',
          color: theme.text,
        },
      }}
    >
      <Tabs.Screen
        name="home"
        options={{
          headerShown: false,
          title: 'Menu',
          tabBarIcon: ({ color }) => <Entypo name="home" size={22} color={color} />,
        }}
      />
      <Tabs.Screen
        name="chatRoom"
        options={{
          headerShown: false,
          tabBarStyle: { display: 'none' },
          title: 'Chat',
          tabBarIcon: ({ color }) => <FontAwesome6 name="robot" size={20} color={color} />,
        }}
      />
      <Tabs.Screen
        name="order"
        options={{
          headerShown: false,
          tabBarStyle: { display: 'none' },
          title: 'Bag',
          tabBarIcon: ({ color }) => <Entypo name="shopping-cart" size={22} color={color} />,
          tabBarBadge: cartCount > 0 ? cartCount : undefined,
          tabBarBadgeStyle: {
            backgroundColor: theme.accent,
            color: theme.onAccent,
            fontSize: 10,
            minWidth: 18,
            height: 18,
            borderRadius: 9,
            lineHeight: 13,
          },
        }}
      />
    </Tabs>
  );
};

export default TabsLayout;
