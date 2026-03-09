import { ApiError, apiFetch, getErrorMessage } from "@/lib/api";

type TelemetryMeta = Record<string, unknown> | undefined;

export async function trackEvent(event: string, details?: TelemetryMeta): Promise<void> {
  if (typeof window === "undefined") return;

  const payload = {
    event,
    path: window.location.pathname,
    details: details ?? null,
  };

  try {
    await apiFetch<{ ok: boolean }>("/events/client", {
      method: "POST",
      auth: true,
      body: JSON.stringify(payload),
    });
  } catch {
    try {
      await apiFetch<{ ok: boolean }>("/events/client/public", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    } catch {
      // Fail silently: telemetry should never block user flows.
    }
  }
}

export function trackError(
  event: string,
  error: unknown,
  details?: Record<string, unknown>
): Promise<void> {
  const payload: Record<string, unknown> = {
    ...details,
    message: getErrorMessage(error, "Unknown error"),
  };
  if (error instanceof ApiError) {
    payload.status = error.status;
  }
  return trackEvent(event, payload);
}
