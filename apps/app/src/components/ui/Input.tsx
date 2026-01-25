import React from 'react';
import { StyleSheet, TextInput, TextInputProps } from 'react-native';

import { useTheme } from '../theme/ThemeProvider';

export function Input(props: TextInputProps) {
  const { colors, fonts, radius } = useTheme();
  return (
    <TextInput
      placeholderTextColor={colors.muted}
      {...props}
      style={[
        styles.input,
        {
          backgroundColor: colors.card,
          borderColor: colors.border,
          color: colors.text,
          fontFamily: fonts.sans,
          borderRadius: radius.md,
        },
        props.style,
      ]}
    />
  );
}

const styles = StyleSheet.create({
  input: {
    height: 48,
    borderWidth: 1,
    paddingHorizontal: 14,
    fontSize: 14,
  },
});
