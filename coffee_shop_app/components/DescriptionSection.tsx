import { Text, View, StyleSheet } from 'react-native';
import { useState } from 'react';
import React from 'react';
import { TouchableOpacity } from 'react-native-gesture-handler';
import { useTheme } from '@/constants/theme';

interface DetailsInterface {
  description: string;
}

const DescriptionSection = ({ description }: DetailsInterface) => {
  const theme = useTheme();
  const [expanded, setExpanded] = useState(false);

  const preview = description.length > 120 ? description.slice(0, 120) : description;
  const hasMore = description.length > 120;

  return (
    <View style={styles.container}>
      <Text style={[styles.label, { color: theme.text }]}>About</Text>
      <Text style={[styles.body, { color: theme.textMuted }]}>
        {expanded ? description : preview}
        {hasMore && !expanded ? '…' : ''}
      </Text>
      {hasMore && (
        <TouchableOpacity
          onPress={() => setExpanded((v) => !v)}
          activeOpacity={0.7}
          hitSlop={{ top: 8, bottom: 8, left: 0, right: 0 }}
          accessibilityRole="button"
          accessibilityLabel={expanded ? 'Show less description' : 'Read full description'}
          style={styles.toggleBtn}
        >
          <Text style={[styles.toggle, { color: theme.accent }]}>
            {expanded ? 'Show less' : 'Read more'}
          </Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: '100%',
    marginTop: 20,
  },
  label: {
    fontFamily: 'Sora-Bold',
    fontSize: 16,
    marginBottom: 10,
  },
  body: {
    fontFamily: 'Sora-Regular',
    fontSize: 14,
    lineHeight: 23,
  },
  toggleBtn: {
    marginTop: 6,
    alignSelf: 'flex-start',
  },
  toggle: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 14,
  },
});

export default DescriptionSection;
