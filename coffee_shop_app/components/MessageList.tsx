import { ScrollView, View, Text, StyleSheet } from 'react-native';
import React, { useRef, useEffect } from 'react';
import MessageItem from './MessageItem';
import { MessageInterface } from '@/types/types';
import TypingIndicator from '@/components/TypingIndicator';
import { useTheme } from '@/constants/theme';

interface MessageListProps {
  messages: MessageInterface[];
  isTyping: boolean;
}

const MessageList = ({ messages, isTyping = false }: MessageListProps) => {
  const scrollViewRef = useRef<ScrollView | null>(null);
  const theme = useTheme();

  useEffect(() => {
    scrollViewRef.current?.scrollToEnd({ animated: true });
  }, [messages, isTyping]);

  return (
    <ScrollView
      ref={scrollViewRef}
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.content}
    >
      {messages.map((message, index) => (
        <MessageItem key={index} message={message} />
      ))}

      {isTyping && (
        <View style={styles.typingRow}>
          <View style={[styles.avatar, { backgroundColor: theme.accent }]}>
            <Text style={[styles.avatarLabel, { color: theme.onAccent }]}>F</Text>
          </View>
          <View style={[styles.typingBubble, { backgroundColor: theme.assistantBubble }]}>
            <TypingIndicator />
          </View>
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  content: {
    paddingTop: 20,
    paddingBottom: 12,
  },
  typingRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    marginLeft: 16,
    marginBottom: 8,
    gap: 10,
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  avatarLabel: {
    fontFamily: 'Sora-Bold',
    fontSize: 13,
    lineHeight: 16,
  },
  typingBubble: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 18,
    borderTopLeftRadius: 4,
  },
});

export default MessageList;
