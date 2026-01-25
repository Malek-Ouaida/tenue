import React, { useMemo, useState } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  TextInputProps,
  View,
} from 'react-native';

import { useTheme } from '../theme/ThemeProvider';

type FloatingInputProps = {
  label: string;
  type?: 'text' | 'password';
  error?: string;
} & TextInputProps;

export function FloatingInput({
  label,
  type = 'text',
  error,
  value,
  onFocus,
  onBlur,
  style,
  ...props
}: FloatingInputProps) {
  const { colors, fonts, radius } = useTheme();
  const [focused, setFocused] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const hasValue = !!value && String(value).length > 0;
  const isPassword = type === 'password';
  const secureTextEntry = isPassword && !showPassword;

  const labelStyle = useMemo(
    () => [
      styles.label,
      {
        color: colors.muted,
        fontFamily: fonts.sans,
      },
      (focused || hasValue) && styles.labelRaised,
    ],
    [colors.muted, focused, fonts.sans, hasValue],
  );

  return (
    <View style={styles.wrapper}>
      <View
        style={[
          styles.shell,
          {
            borderColor: error ? colors.danger : focused ? colors.ring : colors.border,
            backgroundColor: colors.card,
            borderRadius: radius.md,
          },
        ]}
      >
        <Text style={labelStyle}>{label}</Text>
        <TextInput
          value={value}
          placeholder=""
          placeholderTextColor={colors.muted}
          onFocus={(event) => {
            setFocused(true);
            onFocus?.(event);
          }}
          onBlur={(event) => {
            setFocused(false);
            onBlur?.(event);
          }}
          secureTextEntry={secureTextEntry}
          autoCapitalize="none"
          autoCorrect={false}
          {...props}
          style={[
            styles.input,
            {
              color: colors.text,
              fontFamily: fonts.sans,
            },
            style,
          ]}
        />

        {isPassword ? (
          <Pressable
            onPress={() => setShowPassword((prev) => !prev)}
            style={({ pressed }) => [
              styles.showToggle,
              { opacity: pressed ? 0.6 : 1 },
            ]}
          >
            <Text style={[styles.showLabel, { color: colors.muted }]}
            >
              {showPassword ? 'Hide' : 'Show'}
            </Text>
          </Pressable>
        ) : null}
      </View>
      {error ? <Text style={[styles.error, { color: colors.danger }]}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    gap: 6,
  },
  shell: {
    borderWidth: 1,
    paddingHorizontal: 16,
    paddingTop: 18,
    paddingBottom: 10,
    minHeight: 56,
    justifyContent: 'center',
    overflow: 'hidden',
  },
  label: {
    position: 'absolute',
    left: 16,
    top: 18,
    fontSize: 14,
  },
  labelRaised: {
    top: 8,
    fontSize: 11,
  },
  input: {
    fontSize: 14,
    paddingTop: 16,
    paddingBottom: 2,
    paddingRight: 52,
  },
  showToggle: {
    position: 'absolute',
    right: 12,
    top: 18,
    paddingHorizontal: 8,
    paddingVertical: 6,
    borderRadius: 12,
  },
  showLabel: {
    fontSize: 12,
    fontWeight: '600',
  },
  error: {
    fontSize: 12,
  },
});
