"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import Image from "next/image";
import { Grid3X3, Bookmark, Share2, Settings } from "lucide-react";

import { apiFetch, clearTokens, ApiError, getErrorMessage } from "@/lib/api";

type Me = {
  user_id: string;
  email?: string | null;
  username: string;
  display_name: string | null;
  bio?: string | null;
  avatar_key?: string | null;
  followers_count: number;
  following_count: number;
};

function initials(name: string) {
  const parts = name.trim().split(/\s+/).slice(0, 2);
  return parts.map((p) => p[0]?.toUpperCase()).join("");
}

export default function MePage() {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"posts" | "saved">("posts");
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let active = true;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await apiFetch<Me>("/users/me", { auth: true, cache: "no-store" });
        if (!active) return;
        setMe(data);
      } catch (e: unknown) {
        if (!active) return;
        setMe(null);
        if (e instanceof ApiError && (e.status === 401 || e.status === 403)) {
          clearTokens();
          toast.error("Session expired. Please sign in again.");
          router.replace("/login");
          return;
        }

        const message = getErrorMessage(e, "Failed to load profile.");
        setError(message);
        toast.error(message);
      } finally {
        if (active) setLoading(false);
      }
    };

    load();
    return () => {
      active = false;
    };
  }, [router, retryCount]);

  const displayName = useMemo(() => {
    if (!me) return "";
    return me.display_name?.trim() ? me.display_name : me.username;
  }, [me]);

  const avatarFallback = useMemo(() => {
    if (!me) return "";
    return initials(displayName || me.username);
  }, [me, displayName]);

  const avatarSrc = me?.avatar_key ?? null;
  const handleRetry = () => setRetryCount((count) => count + 1);

  return (
    <main className="mx-auto w-full max-w-5xl px-4 pb-16 pt-6 md:px-6">
      {/* Top bar */}
      <div className="mb-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="text-sm font-semibold tracking-[-0.01em] text-[rgb(var(--fg))]">
            {loading || !me ? "Profile" : `@${me.username}`}
          </div>
          <div className="hidden text-xs text-[rgb(var(--muted))] md:block">
            Tenue • Private profile
          </div>
        </div>

        <button
          type="button"
          onClick={() => toast.message("Settings (Sprint 2).")}
          className="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-[rgb(var(--card))] text-[rgb(var(--fg))] ring-1 ring-[rgb(var(--border))]/70 transition hover:bg-[rgb(var(--card-2))]"
          aria-label="Settings"
        >
          <Settings className="h-4 w-4" />
        </button>
      </div>

      {error ? (
        <div className="mb-5 flex items-center justify-between gap-3 rounded-2xl border border-[rgb(var(--border))]/70 bg-[rgb(var(--card))] px-4 py-3 text-sm text-[rgb(var(--fg))]">
          <span>{error}</span>
          <button
            type="button"
            onClick={handleRetry}
            disabled={loading}
            className="rounded-xl bg-[rgb(var(--card-2))] px-3 py-1.5 text-xs font-medium text-[rgb(var(--fg))] ring-1 ring-[rgb(var(--border))]/70 transition hover:bg-[rgb(var(--card))] disabled:opacity-60"
          >
            Retry
          </button>
        </div>
      ) : null}

      {/* Profile shell */}
      <div className="overflow-hidden rounded-[28px] bg-[rgb(var(--card))] ring-1 ring-[rgb(var(--border))]/70">
        {/* Cover */}
        <div className="relative h-44 md:h-56">
          <div className="absolute inset-0 bg-[radial-gradient(1100px_400px_at_20%_-20%,rgba(var(--accent)/0.35),transparent_60%),radial-gradient(900px_350px_at_80%_0%,rgba(var(--accent-2)/0.25),transparent_55%),linear-gradient(to_bottom,rgb(var(--surface)),rgb(var(--surface-2)))]" />
          <div className="absolute inset-0 opacity-[0.15] [background-image:radial-gradient(rgba(255,255,255,0.18)_1px,transparent_1px)] [background-size:3px_3px]" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/35 via-black/10 to-transparent dark:from-black/50 dark:via-black/20" />
        </div>

        {/* Body */}
        <div className="relative px-5 pb-6 pt-0 md:px-8">
          {/* Avatar row */}
          <div className="-mt-10 flex flex-col gap-4 md:-mt-12 md:flex-row md:items-end md:justify-between">
            <div className="flex items-end gap-4">
              {/* Avatar */}
              <div className="relative">
                <div className="absolute -inset-2 rounded-[26px] bg-[radial-gradient(120px_80px_at_30%_20%,rgba(var(--accent)/0.35),transparent_70%)] blur-xl" />
                <div className="relative h-20 w-20 overflow-hidden rounded-[22px] bg-[rgb(var(--card-2))] ring-2 ring-[rgb(var(--card))] md:h-24 md:w-24">
                  {avatarSrc ? (
                    <Image
                      src={avatarSrc}
                      alt="Avatar"
                      fill
                      className="object-cover"
                      sizes="(min-width: 768px) 96px, 80px"
                      priority
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center">
                      <div className="text-lg font-semibold tracking-[-0.02em] text-[rgb(var(--fg))] md:text-xl">
                        {avatarFallback}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Name + handle */}
              <div className="pb-1">
                {loading ? (
                  <div className="grid gap-2">
                    <div className="h-5 w-44 animate-pulse rounded-lg bg-[rgb(var(--border))]/60" />
                    <div className="h-4 w-28 animate-pulse rounded-lg bg-[rgb(var(--border))]/40" />
                  </div>
                ) : (
                  <>
                    <h1 className="text-xl font-semibold tracking-[-0.03em] text-[rgb(var(--fg))] md:text-2xl">
                      {displayName}
                    </h1>
                    <p className="mt-1 text-sm text-[rgb(var(--muted))]">@{me?.username}</p>
                  </>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 md:pb-2">
              <button
                type="button"
                onClick={() => router.push("/app/me/edit")}
                className="h-10 flex-1 rounded-2xl px-4 text-sm font-medium text-white shadow-[0_12px_30px_-16px_rgba(2,6,23,0.55)] transition hover:brightness-105 active:brightness-95 md:flex-none
                  bg-[linear-gradient(135deg,rgb(var(--accent))_0%,rgb(var(--accent-2))_100%)]
                  dark:text-zinc-950 dark:bg-[linear-gradient(135deg,rgba(var(--accent)/0.9)_0%,rgba(var(--accent-2)/0.9)_100%)]"
              >
                Edit profile
              </button>

              <button
                type="button"
                onClick={() => toast.message("Share profile (Sprint 2).")}
                className="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-[rgb(var(--card))] text-[rgb(var(--fg))] ring-1 ring-[rgb(var(--border))]/70 transition hover:bg-[rgb(var(--card-2))]"
                aria-label="Share"
              >
                <Share2 className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Bio + meta */}
          <div className="mt-5 grid gap-3">
            <p className="text-sm leading-relaxed text-[rgb(var(--fg))]">
              {loading ? (
                <span className="inline-block h-4 w-80 animate-pulse rounded-lg bg-[rgb(var(--border))]/40" />
              ) : error ? (
                <span className="text-[rgb(var(--muted))]">Profile details unavailable.</span>
              ) : me?.bio ? (
                me.bio
              ) : (
                <span className="text-[rgb(var(--muted))]">No bio yet. Add one that feels you.</span>
              )}
            </p>

            {!loading && me?.email ? (
              <div className="text-xs text-[rgb(var(--muted))]">
                <span className="font-medium text-[rgb(var(--fg))]">Email:</span>{" "}
                <span>{me.email}</span>
              </div>
            ) : null}
          </div>

          {/* Stats row (placeholders) */}
          <div className="mt-6 grid grid-cols-3 divide-x divide-[rgb(var(--border))]/70 overflow-hidden rounded-2xl bg-[rgb(var(--card-2))] ring-1 ring-[rgb(var(--border))]/70">
            {[
              { label: "Posts", value: loading || error ? "—" : "0" },
              {
                label: "Followers",
                value: loading || error ? "—" : String(me?.followers_count ?? 0),
              },
              {
                label: "Following",
                value: loading || error ? "—" : String(me?.following_count ?? 0),
              },
            ].map((s) => (
              <div key={s.label} className="px-4 py-3 text-center">
                <div className="text-sm font-semibold tracking-[-0.02em] text-[rgb(var(--fg))]">
                  {s.value}
                </div>
                <div className="mt-0.5 text-[11px] text-[rgb(var(--muted))]">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Tabs */}
          <div className="mt-6 flex items-center justify-center gap-2">
            <button
              type="button"
              onClick={() => setTab("posts")}
              className={[
                "inline-flex items-center gap-2 rounded-2xl px-4 py-2 text-sm font-medium ring-1 transition",
                tab === "posts"
                  ? "bg-[rgb(var(--card))] text-[rgb(var(--fg))] ring-[rgb(var(--border))]/80"
                  : "bg-transparent text-[rgb(var(--muted))] ring-transparent hover:bg-[rgb(var(--card-2))] hover:text-[rgb(var(--fg))]",
              ].join(" ")}
            >
              <Grid3X3 className="h-4 w-4" />
              Posts
            </button>

            <button
              type="button"
              onClick={() => setTab("saved")}
              className={[
                "inline-flex items-center gap-2 rounded-2xl px-4 py-2 text-sm font-medium ring-1 transition",
                tab === "saved"
                  ? "bg-[rgb(var(--card))] text-[rgb(var(--fg))] ring-[rgb(var(--border))]/80"
                  : "bg-transparent text-[rgb(var(--muted))] ring-transparent hover:bg-[rgb(var(--card-2))] hover:text-[rgb(var(--fg))]",
              ].join(" ")}
            >
              <Bookmark className="h-4 w-4" />
              Saved
            </button>
          </div>

          {/* Grid */}
          <div className="mt-5 pb-2">
            <div className="grid grid-cols-3 gap-2 md:gap-3">
              {Array.from({ length: 12 }).map((_, i) => (
                <div
                  key={i}
                  className="relative aspect-square overflow-hidden rounded-2xl bg-[rgb(var(--card-2))] ring-1 ring-[rgb(var(--border))]/70"
                >
                  {/* Placeholder aesthetic skeleton */}
                  <div className="absolute inset-0 bg-[radial-gradient(220px_120px_at_20%_10%,rgba(var(--accent)/0.16),transparent_60%),radial-gradient(220px_120px_at_80%_90%,rgba(var(--accent-2)/0.12),transparent_65%)]" />
                  <div className="absolute inset-0 opacity-[0.12] [background-image:radial-gradient(rgba(255,255,255,0.18)_1px,transparent_1px)] [background-size:3px_3px]" />
                </div>
              ))}
            </div>

            <div className="mt-4 text-center text-xs text-[rgb(var(--muted))]">
              {tab === "posts"
                ? "Your posts will appear here."
                : "Your saved items will appear here."}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
