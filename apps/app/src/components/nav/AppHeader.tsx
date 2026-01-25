import { StyleSheet, Text, View } from 'react-native';

import { ThemeLogo } from '../theme/ThemeLogo';
import { useTheme } from '../theme/ThemeProvider';

type AppHeaderProps = {
  title?: string;
};

export function AppHeader({ title }: AppHeaderProps) {
  const { colors, fonts } = useTheme();

  return (
    <View style={styles.container}>
      <ThemeLogo size={16} variant="mark" />
      {title ? (
        <Text style={[styles.title, { color: colors.text, fontFamily: fonts.sans }]}>
          {title}
        </Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 13,
    fontWeight: '600',
  },
});
