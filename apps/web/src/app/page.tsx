"use client";

import { useEffect, useState } from "react";

type ApiResult = { ok: boolean; db?: number } | null;

export default function HomePage() {
  const base = process.env.NEXT_PUBLIC_API_URL ?? "";
  const [data, setData] = useState<ApiResult>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const run = async () => {
      try {
        if (!base) throw new Error("NEXT_PUBLIC_API_URL is not set");

        const res = await fetch(`${base}/db/ping`, { cache: "no-store" });

        const text = await res.text();
        if (!res.ok) {
          throw new Error(`HTTP ${res.status} ${res.statusText}\n${text}`);
        }

        setData(text ? (JSON.parse(text) as ApiResult) : null);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : String(e));
      }
    };

    run();
  }, [base]);

  return (
    <main style={{ maxWidth: 720, margin: "40px auto", padding: "0 16px" }}>
      <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 12 }}>tenue</h1>

      <p style={{ marginBottom: 16 }}>
        API URL: <code>{base || "(missing NEXT_PUBLIC_API_URL)"}</code>
      </p>

      {error ? (
        <div style={{ padding: 12, border: "1px solid #ddd", borderRadius: 8 }}>
          <p style={{ fontWeight: 600, marginBottom: 8 }}>Error</p>
          <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{error}</pre>
        </div>
      ) : (
        <div style={{ padding: 12, border: "1px solid #ddd", borderRadius: 8 }}>
          <p style={{ fontWeight: 600, marginBottom: 8 }}>Response</p>
          <pre style={{ margin: 0 }}>{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}
    </main>
  );
}
