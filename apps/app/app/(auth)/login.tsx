import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import axios from 'axios';

import { AuthShell } from '../../src/components/auth/AuthShell';
import { PrimaryButton } from '../../src/components/ui/Buttons';
import { FloatingInput } from '../../src/components/ui/FloatingInput';
import { useTheme } from '../../src/components/theme/ThemeProvider';
import { login } from '../../src/lib/api';

export default function LoginScreen() {
  const { colors, fonts } = useTheme();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      await login({ email: email.trim(), password });
      router.replace('/(app)/me');
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        if (typeof detail === 'string') {
          setError(detail);
        } else if (detail?.error) {
          setError(String(detail.error));
        } else if (detail?.message) {
          setError(String(detail.message));
        } else {
          setError('Unable to log in. Please try again.');
        }
      } else {
        setError('Unable to log in. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell mode="login">
      <View style={styles.form}>
        <FloatingInput
          label="Email"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoComplete="email"
          textContentType="emailAddress"
        />
        <FloatingInput
          label="Password"
          type="password"
          value={password}
          onChangeText={setPassword}
          textContentType="password"
        />
        <Pressable
          onPress={() => {}}
          style={({ pressed }) => [styles.forgot, pressed && { opacity: 0.7 }]}
        >
          <Text style={[styles.forgotText, { color: colors.muted, fontFamily: fonts.sans }]}>
            Forgot password?
          </Text>
        </Pressable>

        {error ? (
          <Text style={[styles.error, { color: colors.danger, fontFamily: fonts.sans }]}>
            {error}
          </Text>
        ) : null}

        <PrimaryButton
          onPress={handleSubmit}
          loading={loading}
          disabled={!email || !password || loading}
        >
          Log in
        </PrimaryButton>

        <Pressable
          onPress={() => router.push('/(auth)/register')}
          style={({ pressed }) => [styles.linkButton, pressed && { opacity: 0.7 }]}
        >
          <Text style={[styles.linkText, { color: colors.muted, fontFamily: fonts.sans }]}>
            New here?{' '}
            <Text style={[styles.linkAccent, { color: colors.accent, fontFamily: fonts.sans }]}>
              Create an account
            </Text>
          </Text>
        </Pressable>
      </View>
    </AuthShell>
  );
}

const styles = StyleSheet.create({
  form: {
    gap: 14,
  },
  error: {
    fontSize: 12,
  },
  forgot: {
    alignItems: 'flex-end',
    justifyContent: 'center',
    minHeight: 44,
  },
  forgotText: {
    fontSize: 12,
  },
  linkButton: {
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 44,
  },
  linkText: {
    fontSize: 13,
  },
  linkAccent: {
    fontWeight: '600',
  },
});
