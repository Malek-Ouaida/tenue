import React from 'react';
import { StyleSheet, View, ViewStyle } from 'react-native';

import { useTheme } from '../theme/ThemeProvider';

type CardProps = {
  children: React.ReactNode;
  style?: ViewStyle;
  variant?: 'surface' | 'card';
};

export function Card({ children, style, variant = 'card' }: CardProps) {
  const { colors, radius, spacing, shadows } = useTheme();
  const backgroundColor = variant === 'surface' ? colors.surface : colors.card;

  return (
    <View
      style={[
        styles.base,
        {
          backgroundColor,
          borderColor: colors.border,
          borderRadius: radius.lg,
          padding: spacing.lg,
        },
        shadows.card,
        style,
      ]}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  base: {
    borderWidth: 1,
  },
});
