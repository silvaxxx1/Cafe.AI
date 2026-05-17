import { Text, View, TouchableOpacity, StyleSheet } from 'react-native';
import React from 'react';
import { useTheme } from '@/constants/theme';

export const SIZE_MODIFIERS: Record<string, number> = { S: -0.5, M: 0, L: 0.5 };

const SIZES = [
  { id: 'S', vol: '8 oz' },
  { id: 'M', vol: '12 oz' },
  { id: 'L', vol: '16 oz' },
] as const;

interface SizesSectionProps {
  selectedSize: string;
  onSizeChange: (size: string) => void;
}

const modifierLabel = (mod: number) => {
  if (mod === 0) return 'base';
  return mod > 0 ? `+$${mod.toFixed(2)}` : `-$${Math.abs(mod).toFixed(2)}`;
};

const SizesSection = ({ selectedSize, onSizeChange }: SizesSectionProps) => {
  const theme = useTheme();

  return (
    <View style={styles.container}>
      <Text style={[styles.label, { color: theme.text }]}>Size</Text>
      <View style={styles.row}>
        {SIZES.map((size) => {
          const active = selectedSize === size.id;
          const mod = SIZE_MODIFIERS[size.id];
          return (
            <TouchableOpacity
              key={size.id}
              onPress={() => onSizeChange(size.id)}
              style={[
                styles.sizeOption,
                {
                  backgroundColor: active ? theme.accent : theme.surfaceAlt,
                  borderColor: active ? theme.accent : theme.border,
                },
              ]}
              activeOpacity={0.8}
              accessibilityRole="button"
              accessibilityLabel={`${size.id} – ${size.vol}`}
              accessibilityState={{ selected: active }}
            >
              <Text style={[styles.sizeLetter, { color: active ? theme.onAccent : theme.text }]}>
                {size.id}
              </Text>
              <Text style={[styles.sizeVol, { color: active ? theme.onAccent : theme.textFaint }]}>
                {size.vol}
              </Text>
              <Text style={[styles.sizeMod, { color: active ? theme.onAccent : theme.textMuted }]}>
                {modifierLabel(mod)}
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
    gap: 3,
  },
  sizeLetter: {
    fontFamily: 'Sora-Bold',
    fontSize: 18,
  },
  sizeVol: {
    fontFamily: 'Sora-Regular',
    fontSize: 11,
  },
  sizeMod: {
    fontFamily: 'Sora-Medium',
    fontSize: 10,
    letterSpacing: 0.2,
  },
});

export default SizesSection;
