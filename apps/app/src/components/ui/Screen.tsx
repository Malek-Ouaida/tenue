import React from 'react';
import { StyleSheet, View, ViewStyle } from 'react-native';
import { SafeAreaView, Edge } from 'react-native-safe-area-context';

import { useTheme } from '../theme/ThemeProvider';

type ScreenProps = {
  children: React.ReactNode;
  style?: ViewStyle;
  contentStyle?: ViewStyle;
  edges?: Edge[];
};

export function Screen({ children, style, contentStyle, edges = ['top', 'bottom'] }: ScreenProps) {
  const { colors, spacing } = useTheme();

  return (
    <SafeAreaView style={[styles.root, { backgroundColor: colors.background }, style]} edges={edges}>
      <View style={[styles.content, { paddingHorizontal: spacing.xl }, contentStyle]}>{children}</View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
  content: {
    flex: 1,
  },
});
