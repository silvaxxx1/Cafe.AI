import { useWindowDimensions, Platform } from 'react-native';

export function useResponsive() {
  const { width, height } = useWindowDimensions();
  const isTablet = width >= 768;
  const isWeb = Platform.OS === 'web';
  const isLandscape = width > height;
  return { width, height, isTablet, isWeb, isLandscape };
}

/** Number of product grid columns for current screen width. */
export function useGridColumns(): number {
  const { width } = useWindowDimensions();
  if (width >= 900) return 4;
  if (width >= 600) return 3;
  return 2;
}

/**
 * Spread onto TouchableOpacity/Pressable style props to get a pointer cursor on web.
 * Ignored on iOS/Android (no cursor concept).
 */
export const webPointer = Platform.OS === 'web'
  ? ({ cursor: 'pointer' } as object)
  : {};

/**
 * Spread onto Text style props to allow selection on web (copy-paste).
 * Ignored on iOS/Android.
 */
export const webSelectText = Platform.OS === 'web'
  ? ({ userSelect: 'text' } as object)
  : {};
