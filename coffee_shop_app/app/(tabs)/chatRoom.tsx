import { TouchableOpacity, View, Text, KeyboardAvoidingView, Platform, StyleSheet, StatusBar } from 'react-native';
import React, { useEffect, useRef, useState } from 'react';
import MessageList from '@/components/MessageList';
import { MessageInterface } from '@/types/types';
import { GestureHandlerRootView, TextInput } from 'react-native-gesture-handler';
import { Ionicons } from '@expo/vector-icons';
import { callChatBotStreamAPI, clearSession, getSessionId, loadSession } from '@/services/chatBot';
import { useCart } from '@/components/CartContext';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { useTheme } from '@/constants/theme';
import { webPointer } from '@/constants/responsive';

const ChatRoom = () => {
  const { addToCart, emptyCart } = useCart();
  const theme = useTheme();

  const [messages, setMessages] = useState<MessageInterface[]>([]);
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [sessionLoading, setSessionLoading] = useState<boolean>(true);
  const textRef = useRef('');
  const inputRef = useRef<TextInput>(null);
  const sessionIdRef = useRef<string>(getSessionId());

  useEffect(() => {
    loadSession().then((saved) => {
      if (saved.length > 0) setMessages(saved);
      setSessionLoading(false);
    });
  }, []);

  const handleSendMessage = async () => {
    const message = textRef.current.trim();
    if (!message || sessionLoading) return;
    try {
      const inputMessages = [...messages, { content: message, role: 'user' }];
      setMessages(inputMessages);
      textRef.current = '';
      inputRef?.current?.clear();
      setIsTyping(true);

      // Append an empty assistant bubble that we fill in as tokens arrive
      setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);
      setIsTyping(false);

      let fullContent = '';
      let memory: any = undefined;

      for await (const event of callChatBotStreamAPI(inputMessages, sessionIdRef.current)) {
        if (event.type === 'token') {
          fullContent += event.delta;
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = { role: 'assistant', content: fullContent };
            return next;
          });
        } else if (event.type === 'done') {
          memory = event.memory;
        } else if (event.type === 'error') {
          throw new Error(event.message);
        }
      }

      // Attach memory to the final message so cart sync works
      if (memory !== undefined) {
        setMessages((prev) => {
          const next = [...prev];
          next[next.length - 1] = { role: 'assistant', content: fullContent, memory };
          return next;
        });
      }

      if (memory?.order) {
        emptyCart();
        memory.order.forEach((item: any) => addToCart(item.item, item.quantity));
      }
    } catch (err: any) {
      setIsTyping(false);
      const errMsg = err?.message ?? 'Something went wrong. Please try again.';
      setMessages((prev) => {
        // Replace empty streaming bubble (if present) or append error
        const last = prev[prev.length - 1];
        if (last?.role === 'assistant' && last.content === '') {
          const next = [...prev];
          next[next.length - 1] = { role: 'assistant', content: `⚠️ ${errMsg}` };
          return next;
        }
        return [...prev, { role: 'assistant', content: `⚠️ ${errMsg}` }];
      });
    }
  };

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <StatusBar barStyle={theme.statusBar} backgroundColor={theme.surface} />
      <SafeAreaView style={[styles.safe, { backgroundColor: theme.surface }]} edges={['top']}>

        {/* Header */}
        <View style={[styles.header, { backgroundColor: theme.surface, borderBottomColor: theme.border }]}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backBtn} activeOpacity={0.7} hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}>
            <Ionicons name="arrow-back" size={22} color={theme.text} />
          </TouchableOpacity>

          <View style={styles.headerCenter}>
            <View style={[styles.headerAvatar, { backgroundColor: theme.accent }]}>
              <Text style={[styles.headerAvatarText, { color: theme.onAccent }]}>F</Text>
            </View>
            <View>
              <Text style={[styles.headerName, { color: theme.text }]}>Fero</Text>
              <Text style={[styles.headerSub, { color: theme.success }]}>● Online</Text>
            </View>
          </View>

          <TouchableOpacity
            onPress={async () => {
              await clearSession();
              setMessages([]);
            }}
            style={styles.backBtn}
            activeOpacity={0.7}
            hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
            accessibilityLabel="New chat"
          >
            <Ionicons name="create-outline" size={22} color={theme.textMuted} />
          </TouchableOpacity>
        </View>

        {/* Messages */}
        <KeyboardAvoidingView
          style={[styles.body, { backgroundColor: theme.chatBg }]}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
        >
          <View style={{ flex: 1 }}>
            {messages.length === 0 && !isTyping && !sessionLoading && (
              <View style={styles.emptyState}>
                <Text style={[styles.emptyTitle, { color: theme.text }]}>Hey there 👋</Text>
                <Text style={[styles.emptyBody, { color: theme.textMuted }]}>
                  Ask me about our menu, get recommendations, or place an order. I'm here to help.
                </Text>
              </View>
            )}
            <MessageList messages={messages} isTyping={isTyping} />
          </View>

          {/* Input bar */}
          <View style={[styles.inputWrapper, { backgroundColor: theme.surface, borderTopColor: theme.border }]}>
            <View style={[styles.inputContainer, { backgroundColor: theme.inputBg, borderColor: theme.border }]}>
              <TextInput
                ref={inputRef}
                onChangeText={(val) => (textRef.current = val)}
                placeholder="Ask about our menu…"
                placeholderTextColor={theme.textFaint}
                style={[styles.input, { color: theme.text }]}
                multiline
                maxLength={1000}
                returnKeyType="send"
                onSubmitEditing={handleSendMessage}
                accessibilityLabel="Message input"
                accessibilityHint="Type a message and tap send"
              />
              <TouchableOpacity
                onPress={handleSendMessage}
                disabled={isTyping}
                style={[styles.sendBtn, { backgroundColor: isTyping ? theme.border : theme.accent }, webPointer]}
                activeOpacity={0.8}
                accessibilityLabel="Send message"
                accessibilityRole="button"
                accessibilityState={{ disabled: isTyping }}
              >
                <Ionicons name="send" size={16} color={isTyping ? theme.textFaint : theme.onAccent} />
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>

      </SafeAreaView>
    </GestureHandlerRootView>
  );
};

const styles = StyleSheet.create({
  safe: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
  },
  backBtn: {
    width: 40,
    alignItems: 'flex-start',
  },
  headerCenter: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  headerAvatar: {
    width: 36,
    height: 36,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerAvatarText: {
    fontFamily: 'Sora-ExtraBold',
    fontSize: 16,
  },
  headerName: {
    fontFamily: 'Sora-SemiBold',
    fontSize: 16,
  },
  headerSub: {
    fontFamily: 'Sora-Regular',
    fontSize: 11,
  },
  body: {
    flex: 1,
  },
  emptyState: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 40,
  },
  emptyTitle: {
    fontFamily: 'Sora-ExtraBold',
    fontSize: 24,
    marginBottom: 12,
    textAlign: 'center',
  },
  emptyBody: {
    fontFamily: 'Sora-Regular',
    fontSize: 15,
    lineHeight: 24,
    textAlign: 'center',
  },
  inputWrapper: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: Platform.OS === 'ios' ? 28 : 16,
    borderTopWidth: 1,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    borderWidth: 1,
    borderRadius: 16,
    paddingLeft: 16,
    paddingRight: 6,
    paddingVertical: 8,
    gap: 8,
  },
  input: {
    flex: 1,
    fontFamily: 'Sora-Regular',
    fontSize: 15,
    lineHeight: 22,
    maxHeight: 120,
    paddingVertical: 4,
  },
  sendBtn: {
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
});

export default ChatRoom;
