import { useEffect, useMemo, useRef } from 'react';
import {
  Animated,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { router } from 'expo-router';

import { ThemeLogo } from '../src/components/theme/ThemeLogo';
import { ThemeToggle } from '../src/components/theme/ThemeToggle';
import { PrimaryButton } from '../src/components/ui/Buttons';
import { Screen } from '../src/components/ui/Screen';
import { useTheme } from '../src/components/theme/ThemeProvider';

export default function LandingScreen() {
  const { colors, fonts, spacing, radius } = useTheme();
  const fade = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(fade, {
      toValue: 1,
      duration: 220,
      useNativeDriver: true,
    }).start();
  }, [fade]);

  const heroStyle = useMemo(
    () => ({
      opacity: fade,
      transform: [
        {
          translateY: fade.interpolate({
            inputRange: [0, 1],
            outputRange: [10, 0],
          }),
        },
      ],
    }),
    [fade],
  );

  return (
    <Screen>
      <View style={styles.glowWrap} pointerEvents="none">
        <View
          style={[
            styles.glow,
            {
              backgroundColor: colors.accent,
              opacity: 0.2,
              top: -120,
              left: -80,
            },
          ]}
        />
        <View
          style={[
            styles.glow,
            {
              backgroundColor: colors.accent2,
              opacity: 0.16,
              bottom: -140,
              right: -100,
            },
          ]}
        />
      </View>

      <View style={[styles.topRow, { paddingTop: spacing.sm }]}
      >
        <ThemeLogo size={18} variant="wordmark" />
        <ThemeToggle size="sm" />
      </View>

      <Animated.View style={[styles.hero, heroStyle]}>
        <View style={styles.heroContent}>
          <Text style={[styles.title, { color: colors.text, fontFamily: fonts.sans }]}
          >
            Your space for style inspiration
          </Text>
          <Text style={[styles.subtitle, { color: colors.muted, fontFamily: fonts.sans }]}
          >
            Curate outfits, collect references, and refine your signature in one calm, beautiful place.
          </Text>
        </View>

        <View style={styles.actions}>
          <PrimaryButton onPress={() => router.push('/(auth)/login')}>
            Get started
          </PrimaryButton>
          <Pressable
            onPress={() => router.push('/(auth)/register')}
            style={({ pressed }) => [styles.linkButton, pressed && { opacity: 0.7 }]}
          >
            <Text style={[styles.linkText, { color: colors.muted, fontFamily: fonts.sans }]}
            >
              New here?{' '}
              <Text style={[styles.linkAccent, { color: colors.accent, fontFamily: fonts.sans }]}
              >
                Sign up
              </Text>
            </Text>
          </Pressable>
        </View>
      </Animated.View>

      <View
        style={[
          styles.card,
          {
            borderRadius: radius.lg,
            borderColor: colors.border,
            backgroundColor: colors.surface,
          },
        ]}
      >
        <Text style={[styles.cardTitle, { color: colors.text, fontFamily: fonts.sans }]}
        >
          Calm, curated, yours
        </Text>
        <Text style={[styles.cardBody, { color: colors.muted, fontFamily: fonts.sans }]}
        >
          Build a wardrobe map, save looks, and keep your personal style in one place.
        </Text>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  glowWrap: {
    ...StyleSheet.absoluteFillObject,
  },
  glow: {
    position: 'absolute',
    width: 260,
    height: 260,
    borderRadius: 260,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  hero: {
    flex: 1,
    justifyContent: 'center',
    paddingTop: 12,
  },
  heroContent: {
    gap: 12,
  },
  title: {
    fontSize: 30,
    fontWeight: '600',
    letterSpacing: -0.4,
    lineHeight: 36,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
  },
  actions: {
    marginTop: 28,
    gap: 12,
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
  card: {
    borderWidth: 1,
    padding: 16,
    marginBottom: 24,
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 6,
  },
  cardBody: {
    fontSize: 13,
    lineHeight: 18,
  },
});
