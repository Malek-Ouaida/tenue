export type Tokens = { access: string; refresh: string };

const TOKENS_KEY = "tenue_tokens";

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

export function getTokens(): Tokens | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(TOKENS_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (!parsed?.access || !parsed?.refresh) return null;
    return { access: String(parsed.access), refresh: String(parsed.refresh) };
  } catch {
    return null;
  }
}

export function setTokens(tokens: Tokens): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKENS_KEY, JSON.stringify(tokens));
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKENS_KEY);
}

export function parseApiError(data: any, fallback = "Request failed"): string {
  if (typeof data === "string") return data;

  if (Array.isArray(data?.detail)) {
    const first = data.detail[0];
    if (first?.msg) return String(first.msg);
  }

  return (
    data?.detail?.error ||
    data?.detail?.message ||
    data?.detail ||
    data?.error ||
    fallback
  );
}

export async function apiFetch<T>(
  path: string,
  opts?: RequestInit & { auth?: boolean }
): Promise<T> {
  const base = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/+$/, "");
  if (!base) throw new Error("NEXT_PUBLIC_API_URL is not set");

  const { auth, ...init } = opts ?? {};
  const headers = new Headers(init.headers);
  if (init.body != null && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (auth) {
    const tokens = getTokens();
    if (!tokens?.access) throw new ApiError("Not authenticated", 401, null);
    headers.set("Authorization", `Bearer ${tokens.access}`);
  }

  const url = path.startsWith("/") ? `${base}${path}` : `${base}/${path}`;
  const res = await fetch(url, {
    ...init,
    headers,
  });

  const text = await res.text();
  let parsed: any = null;
  let raw: string | null = null;
  if (text) {
    raw = text;
    try {
      parsed = JSON.parse(text);
    } catch {
      if (res.ok) {
        throw new ApiError("Invalid JSON response", res.status, text);
      }
    }
  }

  if (!res.ok) {
    const data = parsed ?? raw;
    throw new ApiError(parseApiError(data), res.status, data);
  }

  return (parsed ?? null) as T;
}
