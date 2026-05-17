import { Text, View, StyleSheet, TextInput } from 'react-native';
import React, { useMemo } from 'react';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '@/constants/theme';

const getGreeting = (): string => {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning ☕';
  if (hour < 17) return 'Good afternoon ☕';
  return 'Good evening ☕';
};

interface SearchAreaProps {
  onSearch: (text: string) => void;
}

const SearchArea = ({ onSearch }: SearchAreaProps) => {
  const theme = useTheme();
  const greeting = useMemo(getGreeting, []);

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderBottomColor: theme.border }]}>
      <View style={styles.inner}>

        {/* Location row */}
        <View style={styles.locationRow}>
          <Ionicons name="location-outline" size={13} color={theme.accent} />
          <Text style={[styles.locationLabel, { color: theme.textFaint }]}>  Bilzen, Tanjungbalai</Text>
        </View>

        {/* Page title */}
        <Text style={[styles.title, { color: theme.text }]}>{greeting}</Text>
        <Text style={[styles.subtitle, { color: theme.textMuted }]}>What are you having today?</Text>

        {/* Search input */}
        <View style={[styles.searchRow, { backgroundColor: theme.inputBg, borderColor: theme.border }]}>
          <Ionicons name="search-outline" size={16} color={theme.textFaint} />
          <TextInput
            onChangeText={onSearch}
            placeholder="Search menu…"
            placeholderTextColor={theme.textFaint}
            style={[styles.searchInput, { color: theme.text }]}
            returnKeyType="search"
            clearButtonMode="while-editing"
            accessibilityLabel="Search menu items"
          />
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderBottomWidth: 1,
    paddingBottom: 20,
  },
  inner: {
    paddingHorizontal: 24,
    paddingTop: 20,
  },
  locationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  locationLabel: {
    fontFamily: 'Sora-Regular',
    fontSize: 12,
    letterSpacing: 0.2,
  },
  title: {
    fontFamily: 'Sora-ExtraBold',
    fontSize: 28,
    lineHeight: 34,
    marginBottom: 4,
  },
  subtitle: {
    fontFamily: 'Sora-Regular',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 16,
  },
  searchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 10,
    gap: 10,
  },
  searchInput: {
    flex: 1,
    fontFamily: 'Sora-Regular',
    fontSize: 14,
    padding: 0,
  },
});

export default React.memo(SearchArea);
