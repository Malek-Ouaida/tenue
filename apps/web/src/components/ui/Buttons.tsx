"use client";

import { Facebook } from "lucide-react";

function GoogleIcon() {
  return (
    <svg viewBox="0 0 48 48" className="h-4 w-4">
      <path
        fill="#FFC107"
        d="M43.6 20.5H42V20H24v8h11.3C33.8 32.7 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.2 6.1 29.4 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.2-.1-2.3-.4-3.5z"
      />
      <path
        fill="#FF3D00"
        d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.2 6.1 29.4 4 24 4c-7.7 0-14.4 4.3-17.7 10.7z"
      />
      <path
        fill="#4CAF50"
        d="M24 44c5.2 0 10-2 13.6-5.2l-6.3-5.2C29.5 35.1 26.9 36 24 36c-5.3 0-9.8-3.4-11.3-8.1l-6.5 5C9.4 39.6 16.2 44 24 44z"
      />
      <path
        fill="#1976D2"
        d="M43.6 20.5H42V20H24v8h11.3c-1 2.7-2.9 5-5.3 6.4l.1.1 6.3 5.2C39.9 36.6 44 31.8 44 24c0-1.2-.1-2.3-.4-3.5z"
      />
    </svg>
  );
}

export function PrimaryButton({
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={[
        "h-11 w-full rounded-2xl text-sm font-medium transition",
        "text-white",
        "bg-[linear-gradient(135deg,rgb(var(--accent))_0%,rgb(var(--accent-2))_100%)]",
        "shadow-[0_12px_30px_-16px_rgba(2,6,23,0.55)]",
        "hover:brightness-105 active:brightness-95",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        "dark:text-zinc-950",
        "dark:bg-[linear-gradient(135deg,rgba(var(--accent)/0.9)_0%,rgba(var(--accent-2)/0.9)_100%)]",
      ].join(" ")}
    >
      {children}
    </button>
  );
}

export function OAuthButton({
  provider,
  ...props
}: { provider: "google" | "facebook" } & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const label = provider === "google" ? "Continue with Google" : "Continue with Facebook";

  return (
    <button
      {...props}
      type="button"
      className={[
        "h-11 w-full rounded-2xl transition",
        "bg-[rgb(var(--card))] text-[rgb(var(--fg))]",
        "ring-1 ring-[rgb(var(--border))]/70",
        "shadow-sm hover:shadow-md",
        "hover:bg-[rgb(var(--card-2))]",
        "inline-flex items-center justify-center gap-2 text-sm font-medium",
      ].join(" ")}
    >
      {provider === "google" ? <GoogleIcon /> : <Facebook className="h-4 w-4" />}
      {label}
    </button>
  );
}
