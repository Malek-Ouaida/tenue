import { Tabs } from 'expo-router';
import { Camera, CheckCircle2, Heart, Home, Shirt, Sparkles, User } from 'lucide-react-native';

import { AppHeader } from '../../src/components/nav/AppHeader';
import { ThemeToggle } from '../../src/components/theme/ThemeToggle';
import { useTheme } from '../../src/components/theme/ThemeProvider';

export default function AppLayout() {
  const { colors, fonts } = useTheme();
  const titleMap: Record<string, string> = {
    index: 'Explore',
    swipe: 'Swipe',
    closet: 'Closet',
    'try-on': 'Try On',
    me: 'Profile',
    stylist: 'AI Stylist',
    'should-i-buy': 'Should I Buy?',
  };

  return (
    <Tabs
      screenOptions={({ route }) => ({
        headerShown: true,
        headerStyle: {
          backgroundColor: colors.surface,
        },
        headerShadowVisible: false,
        headerTitle: () => <AppHeader title={titleMap[route.name] ?? 'Tenue'} />,
        headerRight: () => <ThemeToggle size="sm" />,
        headerRightContainerStyle: {
          paddingRight: 16,
        },
        sceneContainerStyle: {
          backgroundColor: colors.background,
        },
        tabBarActiveTintColor: colors.text,
        tabBarInactiveTintColor: colors.muted,
        tabBarHideOnKeyboard: true,
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          borderTopWidth: 1,
          height: 62,
          paddingBottom: 8,
          paddingTop: 6,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontFamily: fonts.sans,
          marginTop: 4,
        },
        tabBarItemStyle: {
          borderRadius: 14,
          marginHorizontal: 4,
          paddingVertical: 4,
        },
        tabBarActiveBackgroundColor: colors.card,
      })}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Explore',
          tabBarIcon: ({ color, size }) => <Home size={size ?? 18} color={color} />,
        }}
      />
      <Tabs.Screen
        name="swipe"
        options={{
          title: 'Swipe',
          tabBarIcon: ({ color, size }) => <Heart size={size ?? 18} color={color} />,
        }}
      />
      <Tabs.Screen
        name="closet"
        options={{
          title: 'Closet',
          tabBarIcon: ({ color, size }) => <Shirt size={size ?? 18} color={color} />,
        }}
      />
      <Tabs.Screen
        name="try-on"
        options={{
          title: 'Try On',
          tabBarIcon: ({ color, size }) => <Camera size={size ?? 18} color={color} />,
        }}
      />
      <Tabs.Screen
        name="me"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color, size }) => <User size={size ?? 18} color={color} />,
        }}
      />
      <Tabs.Screen
        name="stylist"
        options={{
          href: null,
          title: 'AI Stylist',
          tabBarIcon: ({ color, size }) => <Sparkles size={size ?? 18} color={color} />,
        }}
      />
      <Tabs.Screen
        name="should-i-buy"
        options={{
          href: null,
          title: 'Should I Buy?',
          tabBarIcon: ({ color, size }) => <CheckCircle2 size={size ?? 18} color={color} />,
        }}
      />
    </Tabs>
  );
}
