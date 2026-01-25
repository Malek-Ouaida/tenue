import React from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { ThemeLogo } from '../theme/ThemeLogo';
import { ThemeToggle } from '../theme/ThemeToggle';
import { useTheme } from '../theme/ThemeProvider';
import { Screen } from '../ui/Screen';
import { Card } from '../ui/Card';

type AuthShellProps = {
  mode: 'login' | 'register';
  children: React.ReactNode;
};

export function AuthShell({ mode, children }: AuthShellProps) {
  const { colors, fonts, spacing } = useTheme();
  const isLogin = mode === 'login';

  return (
    <Screen>
      <View style={styles.topRow}>
        <ThemeLogo size={22} variant="mark" />
        <ThemeToggle size="sm" />
      </View>

      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.select({ ios: 'padding', android: undefined })}
      >
        <ScrollView
          contentContainerStyle={[styles.scroll, { paddingTop: spacing.lg }]}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.header}>
            <Text style={[styles.title, { color: colors.text, fontFamily: fonts.sans }]}
            >
              {isLogin ? 'Welcome back' : 'Create your account'}
            </Text>
            <Text style={[styles.subtitle, { color: colors.muted, fontFamily: fonts.sans }]}
            >
              {isLogin
                ? 'Sign in to continue building your profile.'
                : 'Choose a username and start curating your world.'}
            </Text>
          </View>

          <Card>
            {children}
          </Card>

          <Text style={[styles.legal, { color: colors.muted, fontFamily: fonts.sans }]}>
            By continuing, you agree to tenue's terms and privacy policy.
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 8,
  },
  scroll: {
    flexGrow: 1,
    paddingBottom: 24,
  },
  header: {
    marginBottom: 20,
    gap: 8,
  },
  title: {
    fontSize: 28,
    fontWeight: '600',
    letterSpacing: -0.3,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
  },
  legal: {
    fontSize: 12,
    marginTop: 16,
    textAlign: 'center',
  },
});
