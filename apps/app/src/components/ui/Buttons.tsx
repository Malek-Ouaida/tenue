import React from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

import { useTheme } from '../theme/ThemeProvider';

type ButtonProps = {
  children: React.ReactNode;
  onPress?: () => void;
  disabled?: boolean;
  loading?: boolean;
};

export function PrimaryButton({ children, onPress, disabled, loading }: ButtonProps) {
  const { colors, fonts, theme, radius, shadows } = useTheme();
  const textColor = theme === 'dark' ? colors.surface : '#FFFFFF';
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled || loading}
      style={({ pressed }) => [
        styles.base,
        { opacity: disabled || loading ? 0.6 : pressed ? 0.92 : 1, borderRadius: radius.md },
        shadows.soft,
      ]}
    >
      <LinearGradient
        colors={[colors.accent, colors.accent2]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={[styles.gradient, { borderColor: colors.accent2, borderRadius: radius.md }]}
      >
        {loading ? (
          <ActivityIndicator color={textColor} />
        ) : (
          <Text style={[styles.label, { color: textColor, fontFamily: fonts.sans }]}>
            {children}
          </Text>
        )}
      </LinearGradient>
    </Pressable>
  );
}

export function SecondaryButton({ children, onPress, disabled, loading }: ButtonProps) {
  const { colors, fonts, radius, shadows } = useTheme();
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled || loading}
      style={({ pressed }) => [
        styles.base,
        {
          backgroundColor: colors.card,
          borderColor: colors.border,
          borderWidth: 1,
          borderRadius: radius.md,
          opacity: disabled || loading ? 0.6 : pressed ? 0.92 : 1,
        },
        shadows.soft,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={colors.text} />
      ) : (
        <Text style={[styles.label, { color: colors.text, fontFamily: fonts.sans }]}>
          {children}
        </Text>
      )}
    </Pressable>
  );
}

export function ButtonRow({ children }: { children: React.ReactNode }) {
  return <View style={styles.row}>{children}</View>;
}

const styles = StyleSheet.create({
  base: {
    height: 48,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 0,
  },
  gradient: {
    height: '100%',
    width: '100%',
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 18,
  },
  label: {
    fontSize: 15,
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  row: {
    flexDirection: 'row',
    gap: 12,
  },
});
