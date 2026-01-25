import { Pressable, StyleSheet, View } from 'react-native';
import { Moon, Sun } from 'lucide-react-native';

import { useTheme } from './ThemeProvider';

type ThemeToggleProps = {
  size?: 'sm' | 'md';
};

export function ThemeToggle({ size = 'md' }: ThemeToggleProps) {
  const { theme, toggleTheme, colors, shadows } = useTheme();
  const isDark = theme === 'dark';
  const diameter = size === 'sm' ? 44 : 52;
  const Icon = isDark ? Sun : Moon;

  return (
    <Pressable
      onPress={toggleTheme}
      accessibilityRole="button"
      accessibilityLabel="Toggle theme"
      style={({ pressed }) => [
        styles.button,
        {
          width: diameter,
          height: diameter,
          backgroundColor: colors.card,
          borderColor: colors.border,
          borderRadius: diameter / 2,
        },
        shadows.soft,
        pressed && { opacity: 0.8 },
      ]}
    >
      <View style={styles.iconWrap}>
        <Icon size={size === 'sm' ? 16 : 18} color={colors.text} />
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconWrap: {
    alignItems: 'center',
    justifyContent: 'center',
  },
});
