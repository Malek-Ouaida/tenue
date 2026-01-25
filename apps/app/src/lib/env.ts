export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

if (!process.env.EXPO_PUBLIC_API_BASE_URL) {
  console.warn(
    'EXPO_PUBLIC_API_BASE_URL is not set. Using http://127.0.0.1:8000 by default.',
  );
}
