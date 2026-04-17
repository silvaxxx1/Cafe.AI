import React, { useEffect } from 'react';
import { View, Text, StyleSheet, useColorScheme, AccessibilityInfo } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withSequence,
  withDelay,
  withTiming,
  Easing,
} from 'react-native-reanimated';
import { useTheme } from '@/constants/theme';

const Dot = ({ delay, reduceMotion }: { delay: number; reduceMotion: boolean }) => {
  const theme = useTheme();
  const opacity = useSharedValue(reduceMotion ? 0.7 : 0.3);

  useEffect(() => {
    if (reduceMotion) {
      opacity.value = 0.7;
      return;
    }
    opacity.value = withDelay(
      delay,
      withRepeat(
        withSequence(
          withTiming(1, { duration: 300, easing: Easing.out(Easing.quad) }),
          withTiming(0.3, { duration: 300, easing: Easing.in(Easing.quad) }),
        ),
        -1,
        false
      )
    );
  }, [delay, reduceMotion]);

  const style = useAnimatedStyle(() => ({ opacity: opacity.value }));

  return <Animated.View style={[styles.dot, { backgroundColor: theme.accent }, style]} />;
};

const TypingIndicator: React.FC = () => {
  const [reduceMotion, setReduceMotion] = React.useState(false);

  useEffect(() => {
    AccessibilityInfo.isReduceMotionEnabled().then(setReduceMotion);
    const sub = AccessibilityInfo.addEventListener('reduceMotionChanged', setReduceMotion);
    return () => sub.remove();
  }, []);

  return (
    <View
      style={styles.container}
      accessibilityLabel="Fero is typing"
      accessibilityRole="text"
    >
      <Dot delay={0} reduceMotion={reduceMotion} />
      <Dot delay={150} reduceMotion={reduceMotion} />
      <Dot delay={300} reduceMotion={reduceMotion} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingVertical: 2,
  },
  dot: {
    width: 7,
    height: 7,
    borderRadius: 4,
  },
});

export default TypingIndicator;
