import { ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';

import { useTheme } from '../../src/components/theme/ThemeProvider';
import { Screen } from '../../src/components/ui/Screen';

export default function ExploreScreen() {
  const { colors, fonts } = useTheme();
  const { width } = useWindowDimensions();
  const columnGap = 12;
  const columns = 2;
  const cardWidth = (width - 24 * 2 - columnGap * (columns - 1)) / columns;

  return (
    <Screen contentStyle={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={[styles.title, { color: colors.text, fontFamily: fonts.sans }]}>Explore</Text>
          <Text style={[styles.subtitle, { color: colors.muted, fontFamily: fonts.sans }]}
          >
            Discover curated looks, pins, and styling ideas.
          </Text>
        </View>

        <View style={[styles.grid, { gap: columnGap }]}>
          {Array.from({ length: 12 }).map((_, index) => (
            <View
              key={index}
              style={[
                styles.card,
                {
                  width: cardWidth,
                  backgroundColor: colors.card,
                  borderColor: colors.border,
                },
              ]}
            >
              <View
                style={[
                  styles.cardLabel,
                  { backgroundColor: colors.card2, borderColor: colors.border },
                ]}
              >
                <Text style={[styles.cardText, { color: colors.text, fontFamily: fonts.sans }]}
                >
                  Editorial pin {index + 1}
                </Text>
              </View>
            </View>
          ))}
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
  header: {
    gap: 8,
  },
  title: {
    fontSize: 22,
    fontWeight: '600',
    letterSpacing: -0.4,
  },
  subtitle: {
    fontSize: 13,
    lineHeight: 18,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  card: {
    aspectRatio: 3 / 4,
    borderRadius: 18,
    borderWidth: 1,
    overflow: 'hidden',
    marginBottom: 12,
  },
  cardLabel: {
    position: 'absolute',
    left: 10,
    right: 10,
    bottom: 10,
    borderRadius: 12,
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderWidth: 1,
  },
  cardText: {
    fontSize: 11,
  },
});
