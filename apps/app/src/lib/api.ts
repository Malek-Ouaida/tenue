import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import { router } from 'expo-router';

import { API_BASE_URL } from './env';
import { clearTokens, getTokens, setTokens, Tokens } from './storage';

type TokenPayload = {
  access_token?: string;
  refresh_token?: string;
  accessToken?: string;
  refreshToken?: string;
};

const baseURL = API_BASE_URL.replace(/\/$/, '');

export const api = axios.create({
  baseURL,
  timeout: 15000,
});

const refreshClient = axios.create({
  baseURL,
  timeout: 15000,
});

let refreshPromise: Promise<Tokens | null> | null = null;

function extractTokens(payload: TokenPayload | null | undefined): Tokens | null {
  if (!payload) return null;
  const access = payload.access_token ?? payload.accessToken;
  const refresh = payload.refresh_token ?? payload.refreshToken;
  if (typeof access === 'string' && typeof refresh === 'string') {
    return { accessToken: access, refreshToken: refresh };
  }
  return null;
}

async function refreshTokens(): Promise<Tokens | null> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    try {
      const current = await getTokens();
      if (!current?.refreshToken) return null;

      const response = await refreshClient.post('/auth/refresh', {
        refresh_token: current.refreshToken,
      });

      const next = extractTokens(response.data as TokenPayload);
      if (next) {
        await setTokens(next);
        return next;
      }

      return null;
    } catch {
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

api.interceptors.request.use(async (config) => {
  const tokens = await getTokens();
  if (tokens?.accessToken) {
    config.headers = {
      ...config.headers,
      Authorization: `Bearer ${tokens.accessToken}`,
    };
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const status = error.response?.status;
    const config = error.config as AxiosRequestConfig & { _retry?: boolean };

    if (!config || status !== 401) {
      return Promise.reject(error);
    }

    const url = config.url ?? '';
    const isAuthRoute = url.includes('/auth/login') || url.includes('/auth/register') || url.includes('/auth/refresh');

    if (config._retry || isAuthRoute) {
      return Promise.reject(error);
    }

    config._retry = true;

    const nextTokens = await refreshTokens();
    if (nextTokens?.accessToken) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${nextTokens.accessToken}`,
      };
      return api(config);
    }

    await clearTokens();
    try {
      router.replace('/(auth)/login');
    } catch {
      // ignore navigation errors outside router context
    }

    return Promise.reject(error);
  },
);

export async function register(payload: {
  username: string;
  email: string;
  password: string;
  display_name?: string | null;
}) {
  const response = await api.post('/auth/register', payload);
  const tokens = extractTokens(response.data as TokenPayload);
  if (tokens) await setTokens(tokens);
  return response.data;
}

export async function login(payload: { email: string; password: string }) {
  const response = await api.post('/auth/login', payload);
  const tokens = extractTokens(response.data as TokenPayload);
  if (tokens) await setTokens(tokens);
  return response.data;
}

export async function refresh() {
  const tokens = await refreshTokens();
  return tokens;
}

export async function logout() {
  const response = await api.post('/auth/logout');
  await clearTokens();
  return response.data;
}

export async function logoutAll() {
  const response = await api.post('/auth/logout-all');
  await clearTokens();
  return response.data;
}

export async function getMe() {
  const response = await api.get('/users/me');
  return response.data;
}

export async function updateMe(payload: Record<string, unknown>) {
  const response = await api.patch('/users/me', payload);
  return response.data;
}

export async function getUser(username: string) {
  const response = await api.get(`/users/${username}`);
  return response.data;
}
