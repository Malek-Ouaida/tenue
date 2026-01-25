import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { PrimaryButton, SecondaryButton } from '../../src/components/ui/Buttons';
import { useTheme } from '../../src/components/theme/ThemeProvider';
import { Screen } from '../../src/components/ui/Screen';

export default function SwipeScreen() {
  const { colors, fonts } = useTheme();

  return (
    <Screen contentStyle={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}
        >
          <Text style={[styles.title, { color: colors.text, fontFamily: fonts.sans }]}
          >
            Swipe Shopping
          </Text>
          <Text style={[styles.subtitle, { color: colors.muted, fontFamily: fonts.sans }]}
          >
            Tinder-style shopping feed (coming soon).
          </Text>

          <View style={styles.mockWrap}>
            <View
              style={[
                styles.mockCard,
                { backgroundColor: colors.card2, borderColor: colors.border },
              ]}
            >
              <View style={styles.mockContent}>
                <Text style={[styles.mockTitle, { color: colors.text, fontFamily: fonts.sans }]}
                >
                  Card mock
                </Text>
                <Text style={[styles.mockSubtitle, { color: colors.muted, fontFamily: fonts.sans }]}
                >
                  Outfit preview + details
                </Text>
                <View
                  style={[
                    styles.mockImage,
                    { backgroundColor: colors.card, borderColor: colors.border },
                  ]}
                />
              </View>
            </View>

            <View style={styles.actions}>
              <SecondaryButton onPress={() => {}}>Nope</SecondaryButton>
              <PrimaryButton onPress={() => {}}>Save</PrimaryButton>
            </View>
          </View>
        </View>
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
  card: {
    borderRadius: 20,
    borderWidth: 1,
    padding: 20,
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
  },
  subtitle: {
    fontSize: 13,
    marginTop: 8,
  },
  mockWrap: {
    marginTop: 20,
    gap: 16,
  },
  mockCard: {
    borderRadius: 20,
    borderWidth: 1,
    padding: 16,
  },
  mockContent: {
    gap: 8,
  },
  mockTitle: {
    fontSize: 14,
    fontWeight: '600',
  },
  mockSubtitle: {
    fontSize: 12,
  },
  mockImage: {
    height: 180,
    borderRadius: 16,
    borderWidth: 1,
    marginTop: 12,
  },
  actions: {
    gap: 12,
  },
});
