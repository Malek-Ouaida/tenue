import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from 'react-native';
import { Bookmark, Grid3X3, Share2, Settings } from 'lucide-react-native';
import { LinearGradient } from 'expo-linear-gradient';

import { useTheme } from '../../src/components/theme/ThemeProvider';
import { PrimaryButton, SecondaryButton } from '../../src/components/ui/Buttons';
import { Screen } from '../../src/components/ui/Screen';
import { getMe } from '../../src/lib/api';

type Me = {
  user_id: string;
  email?: string | null;
  username: string;
  display_name: string | null;
  bio?: string | null;
  avatar_key?: string | null;
  followers_count: number;
  following_count: number;
};

function initials(name: string) {
  const parts = name.trim().split(/\s+/).slice(0, 2);
  return parts.map((p) => p[0]?.toUpperCase()).join('');
}

export default function MeScreen() {
  const { colors, fonts } = useTheme();
  const { width } = useWindowDimensions();
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<'posts' | 'saved'>('posts');
  const [retryCount, setRetryCount] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getMe();
      setMe(response);
    } catch {
      setError('Failed to load profile.');
      setMe(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, retryCount]);

  const displayName = useMemo(() => {
    if (!me) return '';
    return me.display_name?.trim() ? me.display_name : me.username;
  }, [me]);

  const avatarFallback = useMemo(() => {
    if (!me) return '';
    return initials(displayName || me.username);
  }, [me, displayName]);

  const gridSize = 3;
  const gridGap = 8;
  const gridWidth = width - 24 * 2;
  const cell = (gridWidth - gridGap * (gridSize - 1)) / gridSize;

  return (
    <Screen contentStyle={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
      <View style={styles.topBar}>
        <View>
          <Text style={[styles.topTitle, { color: colors.text, fontFamily: fonts.sans }]}
          >
            {loading || !me ? 'Profile' : `@${me.username}`}
          </Text>
          <Text style={[styles.topSubtitle, { color: colors.muted, fontFamily: fonts.sans }]}
          >
            Tenue • Private profile
          </Text>
        </View>
        <Pressable
          onPress={() => {}}
          style={[styles.iconButton, { backgroundColor: colors.card, borderColor: colors.border }]}
          accessibilityLabel="Settings"
        >
          <Settings size={16} color={colors.text} />
        </Pressable>
      </View>

      {error ? (
        <View style={[styles.errorRow, { backgroundColor: colors.card, borderColor: colors.border }]}
        >
          <Text style={[styles.errorText, { color: colors.text, fontFamily: fonts.sans }]}>{error}</Text>
          <Pressable
            onPress={() => setRetryCount((count) => count + 1)}
            disabled={loading}
            style={[styles.retryButton, { backgroundColor: colors.card2, borderColor: colors.border }]}
          >
            <Text style={[styles.retryLabel, { color: colors.text, fontFamily: fonts.sans }]}>Retry</Text>
          </Pressable>
        </View>
      ) : null}

      <View style={[styles.profileCard, { backgroundColor: colors.card, borderColor: colors.border }]}
      >
        <View style={styles.cover}>
          <LinearGradient
            colors={[colors.surface, colors.surface2]}
            start={{ x: 0.1, y: 0 }}
            end={{ x: 0.9, y: 1 }}
            style={StyleSheet.absoluteFillObject}
          />
          <View style={[styles.coverGlow, { backgroundColor: colors.accent }]} />
          <View style={styles.coverFade} />
        </View>

        <View style={styles.profileBody}>
          <View style={styles.avatarRow}>
            <View style={styles.avatarWrap}>
              <View style={[styles.avatarGlow, { backgroundColor: colors.accent }]} />
              <View style={[styles.avatar, { backgroundColor: colors.card2, borderColor: colors.card }]}
              >
                {me?.avatar_key ? (
                  <Image source={{ uri: me.avatar_key }} style={styles.avatarImage} />
                ) : (
                  <Text style={[styles.avatarText, { color: colors.text, fontFamily: fonts.sans }]}
                  >
                    {avatarFallback}
                  </Text>
                )}
              </View>
            </View>

            <View style={styles.nameBlock}>
              {loading ? (
                <View style={styles.skeletonBlock}>
                  <View style={[styles.skeleton, { backgroundColor: colors.border }]} />
                  <View style={[styles.skeletonSmall, { backgroundColor: colors.border }]} />
                </View>
              ) : (
                <>
                  <Text style={[styles.name, { color: colors.text, fontFamily: fonts.sans }]}
                  >
                    {displayName}
                  </Text>
                  <Text style={[styles.handle, { color: colors.muted, fontFamily: fonts.sans }]}
                  >
                    @{me?.username}
                  </Text>
                </>
              )}
            </View>
          </View>

          <View style={styles.actions}>
            <PrimaryButton onPress={() => {}}>Edit profile</PrimaryButton>
            <Pressable
              onPress={() => {}}
              style={[styles.iconButton, { backgroundColor: colors.card, borderColor: colors.border }]}
              accessibilityLabel="Share"
            >
              <Share2 size={16} color={colors.text} />
            </Pressable>
          </View>

          <View style={styles.bioBlock}>
            <Text style={[styles.bio, { color: colors.text, fontFamily: fonts.sans }]}>
              {loading ? (
                <Text style={[styles.bioPlaceholder, { color: colors.muted, fontFamily: fonts.sans }]}>
                  Loading profile...
                </Text>
              ) : error ? (
                <Text style={[styles.bioPlaceholder, { color: colors.muted, fontFamily: fonts.sans }]}>
                  Profile details unavailable.
                </Text>
              ) : me?.bio ? (
                me.bio
              ) : (
                <Text style={[styles.bioPlaceholder, { color: colors.muted, fontFamily: fonts.sans }]}>
                  No bio yet. Add one that feels you.
                </Text>
              )}
            </Text>

            {!loading && me?.email ? (
              <Text style={[styles.email, { color: colors.muted, fontFamily: fonts.sans }]}
              >
                <Text style={[styles.emailLabel, { color: colors.text, fontFamily: fonts.sans }]}
                >
                  Email: 
                </Text>
                {me.email}
              </Text>
            ) : null}
          </View>

          <View
            style={[
              styles.statsRow,
              { backgroundColor: colors.card2, borderColor: colors.border },
            ]}
          >
            {[
              { label: 'Posts', value: loading || error ? '—' : '0' },
              {
                label: 'Followers',
                value: loading || error ? '—' : String(me?.followers_count ?? 0),
              },
              {
                label: 'Following',
                value: loading || error ? '—' : String(me?.following_count ?? 0),
              },
            ].map((s) => (
              <View key={s.label} style={styles.statCell}>
                <Text style={[styles.statValue, { color: colors.text, fontFamily: fonts.sans }]}
                >
                  {s.value}
                </Text>
                <Text style={[styles.statLabel, { color: colors.muted, fontFamily: fonts.sans }]}
                >
                  {s.label}
                </Text>
              </View>
            ))}
          </View>

          <View style={styles.tabs}>
            <SecondaryButton onPress={() => setTab('posts')}>
              <View style={styles.tabInner}>
                <Grid3X3 size={16} color={tab === 'posts' ? colors.text : colors.muted} />
                <Text style={[styles.tabLabel, { color: tab === 'posts' ? colors.text : colors.muted, fontFamily: fonts.sans }]}>
                  Posts
                </Text>
              </View>
            </SecondaryButton>
            <SecondaryButton onPress={() => setTab('saved')}>
              <View style={styles.tabInner}>
                <Bookmark size={16} color={tab === 'saved' ? colors.text : colors.muted} />
                <Text style={[styles.tabLabel, { color: tab === 'saved' ? colors.text : colors.muted, fontFamily: fonts.sans }]}>
                  Saved
                </Text>
              </View>
            </SecondaryButton>
          </View>

          <View style={styles.grid}>
            {Array.from({ length: 12 }).map((_, i) => (
              <View
                key={i}
                style={[
                  styles.gridCell,
                  {
                    width: cell,
                    height: cell,
                    backgroundColor: colors.card2,
                    borderColor: colors.border,
                  },
                ]}
              >
              </View>
            ))}
          </View>

          <Text style={[styles.gridHint, { color: colors.muted, fontFamily: fonts.sans }]}
          >
            {tab === 'posts' ? 'Your posts will appear here.' : 'Your saved items will appear here.'}
          </Text>
        </View>
      </View>

        {loading ? (
          <View style={styles.loadingOverlay}>
            <ActivityIndicator color={colors.accent} />
          </View>
        ) : null}
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingTop: 16,
    paddingBottom: 96,
  },
  scroll: {
    gap: 16,
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  topTitle: {
    fontSize: 14,
    fontWeight: '600',
  },
  topSubtitle: {
    fontSize: 11,
  },
  iconButton: {
    height: 44,
    width: 44,
    borderRadius: 16,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  errorRow: {
    marginBottom: 16,
    borderRadius: 16,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
  },
  errorText: {
    fontSize: 12,
    flex: 1,
  },
  retryButton: {
    borderRadius: 12,
    borderWidth: 1,
    paddingHorizontal: 12,
    minHeight: 44,
    justifyContent: 'center',
  },
  retryLabel: {
    fontSize: 11,
    fontWeight: '600',
  },
  profileCard: {
    borderRadius: 28,
    borderWidth: 1,
    overflow: 'hidden',
  },
  cover: {
    height: 160,
  },
  coverGlow: {
    position: 'absolute',
    width: '70%',
    height: '60%',
    top: -30,
    left: -20,
    opacity: 0.35,
    borderRadius: 200,
  },
  coverFade: {
    position: 'absolute',
    inset: 0,
    backgroundColor: 'rgba(0,0,0,0.25)',
  },
  profileBody: {
    paddingHorizontal: 20,
    paddingBottom: 20,
    paddingTop: 0,
  },
  avatarRow: {
    marginTop: -40,
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 12,
  },
  avatarWrap: {
    width: 84,
    height: 84,
    justifyContent: 'center',
  },
  avatarGlow: {
    position: 'absolute',
    width: 100,
    height: 100,
    borderRadius: 30,
    opacity: 0.35,
    top: -8,
    left: -8,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 22,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  avatarImage: {
    width: '100%',
    height: '100%',
  },
  avatarText: {
    fontSize: 18,
    fontWeight: '600',
  },
  nameBlock: {
    marginTop: 6,
  },
  name: {
    fontSize: 20,
    fontWeight: '600',
  },
  handle: {
    fontSize: 12,
    marginTop: 4,
  },
  skeletonBlock: {
    gap: 8,
  },
  skeleton: {
    height: 16,
    width: 180,
    borderRadius: 8,
    opacity: 0.5,
  },
  skeletonSmall: {
    height: 12,
    width: 120,
    borderRadius: 8,
    opacity: 0.35,
  },
  actions: {
    marginTop: 16,
    flexDirection: 'row',
    gap: 12,
    alignItems: 'center',
  },
  bioBlock: {
    marginTop: 16,
    gap: 8,
  },
  bio: {
    fontSize: 13,
    lineHeight: 18,
  },
  bioPlaceholder: {
    fontSize: 13,
  },
  email: {
    fontSize: 11,
  },
  emailLabel: {
    fontWeight: '600',
  },
  statsRow: {
    marginTop: 16,
    borderRadius: 18,
    borderWidth: 1,
    flexDirection: 'row',
    overflow: 'hidden',
  },
  statCell: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 13,
    fontWeight: '600',
  },
  statLabel: {
    fontSize: 11,
    marginTop: 2,
  },
  tabs: {
    marginTop: 16,
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 10,
  },
  tabInner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  tabLabel: {
    fontSize: 13,
  },
  grid: {
    marginTop: 16,
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  gridCell: {
    borderRadius: 18,
    borderWidth: 1,
    overflow: 'hidden',
  },
  gridHint: {
    textAlign: 'center',
    fontSize: 11,
    marginTop: 12,
  },
  loadingOverlay: {
    paddingTop: 12,
  },
});
