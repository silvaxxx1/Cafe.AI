import { Text, View, StyleSheet } from 'react-native';
import React from 'react';
import { MessageInterface } from '@/types/types';
import { useTheme } from '@/constants/theme';
import { webSelectText } from '@/constants/responsive';

interface Message {
  message: MessageInterface;
}

const MessageItem = ({ message }: Message) => {
  const theme = useTheme();

  if (message?.role === 'user') {
    return (
      <View style={styles.userRow}>
        <View
          style={[
            styles.userBubble,
            { backgroundColor: theme.userBubble, borderColor: theme.userBubbleBorder },
          ]}
        >
          <Text style={[styles.userText, { color: theme.text }, webSelectText]}>{message?.content}</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.assistantRow}>
      {/* Barista avatar mark */}
      <View style={[styles.avatar, { backgroundColor: theme.accent }]}>
        <Text style={[styles.avatarText, { color: theme.onAccent }]}>F</Text>
      </View>

      <View style={[styles.assistantBubble, { backgroundColor: theme.assistantBubble }]}>
        <Text style={[styles.assistantLabel, { color: theme.accent }]}>Fero</Text>
        <Text style={[styles.assistantText, { color: theme.text }, webSelectText]}>{message?.content}</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  userRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginBottom: 12,
    marginRight: 16,
    marginLeft: 64,
  },
  userBubble: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 18,
    borderTopRightRadius: 4,
    borderWidth: 1,
    maxWidth: '100%',
  },
  userText: {
    fontFamily: 'Sora-Regular',
    fontSize: 15,
    lineHeight: 22,
  },
  assistantRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
    marginLeft: 16,
    marginRight: 48,
    gap: 10,
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
    flexShrink: 0,
  },
  avatarText: {
    fontFamily: 'Sora-Bold',
    fontSize: 14,
  },
  assistantBubble: {
    flex: 1,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 18,
    borderTopLeftRadius: 4,
  },
  assistantLabel: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 11,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  assistantText: {
    fontFamily: 'Sora-Regular',
    fontSize: 15,
    lineHeight: 23,
  },
});

export default MessageItem;
