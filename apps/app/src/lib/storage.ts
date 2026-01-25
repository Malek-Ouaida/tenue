import AsyncStorage from '@react-native-async-storage/async-storage';

export type Tokens = {
  accessToken: string;
  refreshToken: string;
};

const ACCESS_KEY = 'tenue.accessToken';
const REFRESH_KEY = 'tenue.refreshToken';

export async function getTokens(): Promise<Tokens | null> {
  const [[, accessToken], [, refreshToken]] = await AsyncStorage.multiGet([
    ACCESS_KEY,
    REFRESH_KEY,
  ]);

  if (!accessToken || !refreshToken) return null;
  return { accessToken, refreshToken };
}

export async function setTokens(tokens: Tokens): Promise<void> {
  await AsyncStorage.multiSet([
    [ACCESS_KEY, tokens.accessToken],
    [REFRESH_KEY, tokens.refreshToken],
  ]);
}

export async function clearTokens(): Promise<void> {
  await AsyncStorage.multiRemove([ACCESS_KEY, REFRESH_KEY]);
}

export async function getAccessToken(): Promise<string | null> {
  return AsyncStorage.getItem(ACCESS_KEY);
}

export async function getRefreshToken(): Promise<string | null> {
  return AsyncStorage.getItem(REFRESH_KEY);
}
