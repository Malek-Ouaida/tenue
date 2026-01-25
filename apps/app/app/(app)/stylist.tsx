import { StyleSheet, Text } from 'react-native';

import { useTheme } from '../../src/components/theme/ThemeProvider';
import { Card } from '../../src/components/ui/Card';
import { Screen } from '../../src/components/ui/Screen';

export default function ScreenComponent() {
  const { colors, fonts } = useTheme();
  const titleMap: Record<string, string> = {
    'try-on': 'Try On',
    stylist: 'AI Stylist',
    'should-i-buy': 'Should I Buy?',
  };

  const key = '$name' as keyof typeof titleMap;
  const title = titleMap[key] ?? 'Screen';

  return (
    <Screen contentStyle={styles.container}>
      <Card>
        <Text style={[styles.title, { color: colors.text, fontFamily: fonts.sans }]}>{title}</Text>
        <Text style={[styles.subtitle, { color: colors.muted, fontFamily: fonts.sans }]}
        >
          Coming soon.
        </Text>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingTop: 16,
    paddingBottom: 96,
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
  },
  subtitle: {
    fontSize: 13,
    marginTop: 8,
  },
});
