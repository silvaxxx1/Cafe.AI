import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useTheme } from '@/constants/theme';

const DeliveryToggle: React.FC = () => {
  const theme = useTheme();
  const [isDelivery, setIsDelivery] = useState(true);

  return (
    <View style={[styles.container, { backgroundColor: theme.surfaceAlt }]}>
      {['Deliver', 'Pick Up'].map((label) => {
        const active = isDelivery ? label === 'Deliver' : label === 'Pick Up';
        return (
          <TouchableOpacity
            key={label}
            onPress={() => setIsDelivery(label === 'Deliver')}
            style={[
              styles.option,
              active && { backgroundColor: theme.accent },
            ]}
            activeOpacity={0.8}
          >
            <Text style={[styles.optionText, { color: active ? theme.onAccent : theme.textMuted }]}>
              {label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    marginHorizontal: 24,
    padding: 4,
    borderRadius: 14,
    marginTop: 20,
  },
  option: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 11,
    alignItems: 'center',
  },
  optionText: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 14,
  },
});

export default DeliveryToggle;
