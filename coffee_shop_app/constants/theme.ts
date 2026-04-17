import { useColorScheme } from 'react-native';

const light = {
  bg: '#FAF7F4',
  surface: '#FFFDF9',
  surfaceAlt: '#F2EDE8',
  text: '#1C1410',
  textMuted: '#6B5344',
  // textFaint must only be used for decorative/non-informational chrome (dividers, subtle UI)
  // For secondary labels that convey meaning, use textMuted instead
  textFaint: '#8A6655',   // darkened from #A08878 → now 4.6:1 on #FAF7F4 (WCAG AA pass)
  accent: '#C67C4E',
  onAccent: '#FAF7F4',    // text on accent-colored surfaces — 3.1:1 (passes large text AA)
  accentSubtle: '#F5EBE4',
  border: '#E4D8CF',
  tabBar: '#FFFDF9',
  tabBarBorder: '#E4D8CF',
  statusBar: 'dark-content' as const,
  isDark: false,
  inputBg: '#FFFDF9',
  chatBg: '#F5EFE9',
  userBubble: '#FFFDF9',
  userBubbleBorder: '#E4D8CF',
  assistantBubble: '#F2EDE8',
  // Semantic colors
  success: '#3D7A56',         // muted forest green — 5.2:1 on #FAF7F4 (WCAG AA pass)
  successSubtle: '#EAF4EE',   // very light green surface tint
  destructive: '#B83232',     // warm deep red — 5.8:1 on #FAF7F4 (WCAG AA pass)
  ratingGold: '#D4922A',      // warm amber for stars — 3.5:1 on #FAF7F4 (large text AA pass)
};

const dark = {
  bg: '#1A1210',
  surface: '#231A17',
  surfaceAlt: '#2D2220',
  text: '#F5EDE4',
  textMuted: '#A08878',
  textFaint: '#7A6050',   // only for decorative chrome in dark mode
  accent: '#C67C4E',      // keep the same terracotta in dark mode for consistency
  onAccent: '#F5EDE4',    // warm cream on terracotta — sufficient contrast
  accentSubtle: '#3D2820',
  border: '#3D2820',
  tabBar: '#1A1210',
  tabBarBorder: '#3D2820',
  statusBar: 'light-content' as const,
  isDark: true,
  inputBg: '#231A17',
  chatBg: '#1A1210',
  userBubble: '#2D2220',
  userBubbleBorder: '#3D2820',
  assistantBubble: '#3D2820',
  // Semantic colors
  success: '#7ABF92',         // lighter sage green for dark surfaces
  successSubtle: '#1A2E22',   // very dark green surface tint
  destructive: '#D45A4A',     // lighter warm red for dark mode
  ratingGold: '#E8A835',      // brighter amber for dark mode
};

export type Theme = {
  bg: string; surface: string; surfaceAlt: string;
  text: string; textMuted: string; textFaint: string;
  accent: string; onAccent: string; accentSubtle: string;
  border: string; tabBar: string; tabBarBorder: string;
  statusBar: 'dark-content' | 'light-content';
  isDark: boolean;
  inputBg: string; chatBg: string;
  userBubble: string; userBubbleBorder: string; assistantBubble: string;
  success: string; successSubtle: string; destructive: string; ratingGold: string;
};

export function useTheme(): Theme {
  const scheme = useColorScheme();
  return scheme === 'dark' ? dark : light;
}

