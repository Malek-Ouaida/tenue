# Tenue Mobile (Expo)

## Dev
- Install deps from the repo root with `pnpm install`
- Start the app with `pnpm -C apps/app start`
- iOS simulator: press `i` in the Expo CLI
- Android: press `a` (device or emulator)

## Environment
Create `apps/app/.env` with:

```
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

For physical devices, replace `127.0.0.1` with your machine LAN IP (for example `http://192.168.1.10:8000`).
