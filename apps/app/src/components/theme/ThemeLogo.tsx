import { Image, StyleSheet, View } from 'react-native';

import { useTheme } from './ThemeProvider';

const wordmarkLight = require('../../../assets/brand/tenue_black.png');
const wordmarkDark = require('../../../assets/brand/tenue_white.png');
const markLight = require('../../../assets/brand/t_black.png');
const markDark = require('../../../assets/brand/t_white.png');

type ThemeLogoProps = {
  size?: number;
  variant?: 'wordmark' | 'mark';
};

export function ThemeLogo({ size = 24, variant = 'wordmark' }: ThemeLogoProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const source =
    variant === 'mark'
      ? isDark
        ? markDark
        : markLight
      : isDark
        ? wordmarkDark
        : wordmarkLight;

  return (
    <View style={styles.container} accessibilityRole="header">
      <Image
        source={source}
        resizeMode="contain"
        style={variant === 'mark' ? { width: size, height: size } : { width: size * 4.5, height: size }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
  },
});
