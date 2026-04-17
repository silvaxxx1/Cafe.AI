import { Text, View, TouchableOpacity, StyleSheet } from 'react-native';
import React, { useState } from 'react';
import { useTheme } from '@/constants/theme';

const SizesSection = () => {
  const theme = useTheme();
  const [selectedSize, setSelectedSize] = useState('M');
  const sizes = [
    { id: 'S', label: 'Small', vol: '8 oz' },
    { id: 'M', label: 'Medium', vol: '12 oz' },
    { id: 'L', label: 'Large', vol: '16 oz' },
  ];

  return (
    <View style={styles.container}>
      <Text style={[styles.label, { color: theme.text }]}>Size</Text>
      <View style={styles.row}>
        {sizes.map((size) => {
          const active = selectedSize === size.id;
          return (
            <TouchableOpacity
              key={size.id}
              onPress={() => setSelectedSize(size.id)}
              style={[
                styles.sizeOption,
                {
                  backgroundColor: active ? theme.accent : theme.surfaceAlt,
                  borderColor: active ? theme.accent : theme.border,
                },
              ]}
              activeOpacity={0.8}
            >
              <Text style={[styles.sizeLetter, { color: active ? theme.onAccent : theme.text }]}>
                {size.id}
              </Text>
              <Text style={[styles.sizeLabel, { color: active ? theme.onAccent : theme.textFaint }]}>
                {size.vol}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: '100%',
    marginTop: 20,
    marginBottom: 8,
  },
  label: {
    fontFamily: 'Sora-Bold',
    fontSize: 16,
    marginBottom: 14,
  },
  row: {
    flexDirection: 'row',
    gap: 10,
  },
  sizeOption: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 14,
    borderWidth: 1,
    alignItems: 'center',
    gap: 4,
  },
  sizeLetter: {
    fontFamily: 'Sora-Bold',
    fontSize: 18,
  },
  sizeLabel: {
    fontFamily: 'Sora-Regular',
    fontSize: 11,
  },
});

export default SizesSection;
