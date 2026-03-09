export type Tokens = { access: string; refresh: string };

const TOKENS_KEY = "tenue_tokens";

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null ? (value as Record<string, unknown>) : null;
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

export function parseApiError(data: unknown, fallback = "Request failed"): string {
  if (typeof data === "string") return data;

  const obj = asRecord(data);
  const detail = obj ? obj.detail : undefined;

  if (Array.isArray(detail)) {
    const first = asRecord(detail[0]);
    if (first?.msg) return String(first.msg);
  }

  if (obj) {
    const detailObj = asRecord(obj.detail);
    if (detailObj?.error) return String(detailObj.error);
    if (detailObj?.message) return String(detailObj.message);
    if (typeof obj.detail === "string") return obj.detail;
    if (obj.error) return String(obj.error);
  }

  return (
    fallback
  );
}

export function getErrorMessage(error: unknown, fallback = "Request failed"): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return parseApiError(error, fallback);
}

export function buildApiUrl(path: string): string {
  const base = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/+$/, "");
  if (!base) throw new Error("NEXT_PUBLIC_API_URL is not set");
  return path.startsWith("/") ? `${base}${path}` : `${base}/${path}`;
}

export async function apiFetch<T>(
  path: string,
  opts?: RequestInit & { auth?: boolean }
): Promise<T> {
  const { auth, ...init } = opts ?? {};
  const headers = new Headers(init.headers);
  const isFormData = typeof FormData !== "undefined" && init.body instanceof FormData;
  if (init.body != null && !headers.has("Content-Type") && !isFormData) {
    headers.set("Content-Type", "application/json");
  }

  if (auth) {
    const tokens = getTokens();
    if (!tokens?.access) throw new ApiError("Not authenticated", 401, null);
    headers.set("Authorization", `Bearer ${tokens.access}`);
  }

  const url = buildApiUrl(path);
  const res = await fetch(url, {
    ...init,
    headers,
  });

  const text = await res.text();
  let parsed: unknown = null;
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
