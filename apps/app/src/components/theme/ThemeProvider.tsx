import React, { createContext, useContext, useMemo, useState } from 'react';
import { Platform, ViewStyle } from 'react-native';

export type ThemeName = 'dark' | 'light';

export type ThemeColors = {
  background: string;
  surface: string;
  surface2: string;
  card: string;
  card2: string;
  text: string;
  muted: string;
  border: string;
  accent: string;
  accent2: string;
  ring: string;
  danger: string;
  success: string;
};

export type ThemeFonts = {
  sans: string;
  mono: string;
};

export type ThemeSpacing = {
  xs: number;
  sm: number;
  md: number;
  lg: number;
  xl: number;
};

export type ThemeRadius = {
  sm: number;
  md: number;
  lg: number;
};

export type ThemeShadows = {
  card: ViewStyle;
  soft: ViewStyle;
};

const themes: Record<ThemeName, ThemeColors> = {
  dark: {
    background: '#070B18',
    surface: '#0B1224',
    surface2: '#0A0F20',
    card: '#0E1429',
    card2: '#111A33',
    text: '#EAF0FF',
    muted: '#A6B3D1',
    border: '#1B2A55',
    accent: '#7AA7FF',
    accent2: '#9BC5FF',
    ring: '#93B4FF',
    danger: '#F28FA6',
    success: '#7EE0B5',
  },
  light: {
    background: '#F4F6F8',
    surface: '#F5F7FA',
    surface2: '#EFF2F7',
    card: '#FBFCFE',
    card2: '#F0F4F8',
    text: '#09090B',
    muted: '#5A667A',
    border: '#DCE2EA',
    accent: '#0A667E',
    accent2: '#10A28C',
    ring: '#0E7490',
    danger: '#C23B55',
    success: '#1F8A6A',
  },
};

const fonts: ThemeFonts = {
  sans: Platform.select({ ios: 'System', android: 'System', default: 'System' }) ?? 'System',
  mono: Platform.select({ ios: 'Menlo', android: 'monospace', default: 'monospace' }) ?? 'monospace',
};

const spacing: ThemeSpacing = {
  xs: 8,
  sm: 12,
  md: 16,
  lg: 20,
  xl: 24,
};

const radius: ThemeRadius = {
  sm: 12,
  md: 16,
  lg: 20,
};

const shadows: ThemeShadows = {
  card:
    Platform.select<ViewStyle>({
      ios: {
        shadowColor: '#000000',
        shadowOpacity: 0.16,
        shadowRadius: 22,
        shadowOffset: { width: 0, height: 12 },
      },
      android: {
        elevation: 5,
      },
      default: {},
    }) ?? {},
  soft:
    Platform.select<ViewStyle>({
      ios: {
        shadowColor: '#000000',
        shadowOpacity: 0.08,
        shadowRadius: 14,
        shadowOffset: { width: 0, height: 8 },
      },
      android: {
        elevation: 2,
      },
      default: {},
    }) ?? {},
};

type ThemeContextValue = {
  theme: ThemeName;
  colors: ThemeColors;
  fonts: ThemeFonts;
  spacing: ThemeSpacing;
  radius: ThemeRadius;
  shadows: ThemeShadows;
  setTheme: (theme: ThemeName) => void;
  toggleTheme: () => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<ThemeName>('dark');

  const value = useMemo<ThemeContextValue>(
    () => ({
      theme,
      colors: themes[theme],
      fonts,
      spacing,
      radius,
      shadows,
      setTheme,
      toggleTheme: () => setTheme(theme === 'dark' ? 'light' : 'dark'),
    }),
    [theme],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return ctx;
}
