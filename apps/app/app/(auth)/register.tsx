import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import axios from 'axios';

import { AuthShell } from '../../src/components/auth/AuthShell';
import { PrimaryButton } from '../../src/components/ui/Buttons';
import { FloatingInput } from '../../src/components/ui/FloatingInput';
import { useTheme } from '../../src/components/theme/ThemeProvider';
import { register } from '../../src/lib/api';

export default function RegisterScreen() {
  const { colors, fonts } = useTheme();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      await register({
        username: username.trim(),
        email: email.trim(),
        password,
      });
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
          setError('Unable to register. Please try again.');
        }
      } else {
        setError('Unable to register. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell mode="register">
      <View style={styles.form}>
        <FloatingInput
          label="Username"
          value={username}
          onChangeText={setUsername}
          autoComplete="username"
          textContentType="username"
        />
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
          textContentType="newPassword"
        />

        {error ? (
          <Text style={[styles.error, { color: colors.danger, fontFamily: fonts.sans }]}>
            {error}
          </Text>
        ) : null}

        <PrimaryButton
          onPress={handleSubmit}
          loading={loading}
          disabled={!username || !email || !password || loading}
        >
          Create account
        </PrimaryButton>

        <Pressable
          onPress={() => router.push('/(auth)/login')}
          style={({ pressed }) => [styles.linkButton, pressed && { opacity: 0.7 }]}
        >
          <Text style={[styles.linkText, { color: colors.muted, fontFamily: fonts.sans }]}>
            Already have an account?{' '}
            <Text style={[styles.linkAccent, { color: colors.accent, fontFamily: fonts.sans }]}>
              Log in
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
