"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import Link from "next/link";
import Image from "next/image";
import { Bookmark, Grid3X3, Settings } from "lucide-react";

import { apiFetch, ApiError, clearTokens, getErrorMessage } from "@/lib/api";
import { fetchMySavedPosts, fetchProfilePosts, type PostItem } from "@/lib/social";
import { trackError, trackEvent } from "@/lib/telemetry";

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
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"posts" | "saved">("posts");

  const [posts, setPosts] = useState<PostItem[]>([]);
  const [postsCursor, setPostsCursor] = useState<string | null>(null);
  const [saved, setSaved] = useState<PostItem[]>([]);
  const [savedCursor, setSavedCursor] = useState<string | null>(null);
  const [loadingPosts, setLoadingPosts] = useState(false);
  const [loadingSaved, setLoadingSaved] = useState(false);

  const sentinelRef = useRef<HTMLDivElement | null>(null);

  const handleAuthError = useCallback(
    (error: unknown) => {
      if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
        clearTokens();
        toast.error("Session expired. Please sign in again.");
        router.replace("/login");
        return true;
      }
      return false;
    },
    [router]
  );

  const loadProfile = useCallback(async () => {
    setLoadingProfile(true);
    setError(null);
    try {
      const data = await apiFetch<Me>("/users/me", { auth: true, cache: "no-store" });
      setMe(data);
      void trackEvent("me.open", { username: data.username });
      return data;
    } catch (e: unknown) {
      if (handleAuthError(e)) return null;
      const message = getErrorMessage(e, "Failed to load profile.");
      setError(message);
      toast.error(message);
      void trackError("me.load_failed", e);
      return null;
    } finally {
      setLoadingProfile(false);
    }
  }, [handleAuthError]);

  const loadPosts = useCallback(
    async (username: string, cursor: string | null, append: boolean) => {
      try {
        setLoadingPosts(true);
        const page = await fetchProfilePosts(username, cursor, 20);
        setPosts((prev) => (append ? [...prev, ...page.items] : page.items));
        setPostsCursor(page.next_cursor);
      } catch (e: unknown) {
        if (handleAuthError(e)) return;
        toast.error(getErrorMessage(e, "Failed to load your posts."));
        void trackError("me.posts_load_failed", e, { append });
      } finally {
        setLoadingPosts(false);
      }
    },
    [handleAuthError]
  );

  const loadSaved = useCallback(
    async (cursor: string | null, append: boolean) => {
      try {
        setLoadingSaved(true);
        const page = await fetchMySavedPosts(cursor, 20);
        setSaved((prev) => (append ? [...prev, ...page.items] : page.items));
        setSavedCursor(page.next_cursor);
      } catch (e: unknown) {
        if (handleAuthError(e)) return;
        toast.error(getErrorMessage(e, "Failed to load saved posts."));
        void trackError("me.saved_load_failed", e, { append });
      } finally {
        setLoadingSaved(false);
      }
    },
    [handleAuthError]
  );

  useEffect(() => {
    let active = true;

    const load = async () => {
      const profile = await loadProfile();
      if (!active || !profile) return;
      await Promise.all([loadPosts(profile.username, null, false), loadSaved(null, false)]);
    };

    void load();
    return () => {
      active = false;
    };
  }, [loadPosts, loadProfile, loadSaved]);

  useEffect(() => {
    const node = sentinelRef.current;
    if (!node) return;

    const hasMore = tab === "posts" ? postsCursor : savedCursor;
    const isLoading = tab === "posts" ? loadingPosts : loadingSaved;
    if (!hasMore || isLoading || loadingProfile) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (!entries[0]?.isIntersecting || !hasMore) return;
        if (tab === "posts" && me?.username) {
          void loadPosts(me.username, hasMore, true);
        } else if (tab === "saved") {
          void loadSaved(hasMore, true);
        }
      },
      { rootMargin: "200px" }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [loadingPosts, loadingProfile, loadingSaved, loadPosts, loadSaved, me?.username, postsCursor, savedCursor, tab]);

  const displayName = useMemo(() => {
    if (!me) return "";
    return me.display_name?.trim() ? me.display_name : me.username;
  }, [me]);

  const avatarFallback = useMemo(() => {
    if (!me) return "";
    return initials(displayName || me.username);
  }, [me, displayName]);
  const avatarSrc = useMemo(() => {
    if (!me?.avatar_key) return null;
    return me.avatar_key.startsWith("http://") || me.avatar_key.startsWith("https://")
      ? me.avatar_key
      : null;
  }, [me?.avatar_key]);

  if (loadingProfile) {
    return <div className="mx-auto w-full max-w-5xl px-4 py-6 text-sm text-[rgb(var(--muted))]">Loading profile...</div>;
  }

  if (!me || error) {
    return (
      <div className="mx-auto w-full max-w-5xl space-y-3 px-4 py-6">
        <p className="text-sm text-[rgb(var(--muted))]">{error || "Profile unavailable."}</p>
        <button
          type="button"
          onClick={() => void loadProfile()}
          className="rounded-xl bg-[rgb(var(--card))] px-3 py-1.5 text-xs text-[rgb(var(--fg))] ring-1 ring-[rgb(var(--border))]/70"
        >
          Retry
        </button>
      </div>
    );
  }

  const activeItems = tab === "posts" ? posts : saved;
  const activeLoading = tab === "posts" ? loadingPosts : loadingSaved;

  return (
    <div className="mx-auto w-full max-w-5xl px-4 pb-16 pt-6 md:px-6">
      <div className="mb-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="text-sm font-semibold tracking-[-0.01em] text-[rgb(var(--fg))]">@{me.username}</div>
          <div className="hidden text-xs text-[rgb(var(--muted))] md:block">Tenue profile</div>
        </div>

        <button
          type="button"
          onClick={() => toast.message("Settings (coming soon).")}
          className="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-[rgb(var(--card))] text-[rgb(var(--fg))] ring-1 ring-[rgb(var(--border))]/70 transition hover:bg-[rgb(var(--card-2))]"
          aria-label="Settings"
        >
          <Settings className="h-4 w-4" />
        </button>
      </div>

      <div className="overflow-hidden rounded-[28px] bg-[rgb(var(--card))] ring-1 ring-[rgb(var(--border))]/70">
        <div className="relative h-44 md:h-56">
          <div className="absolute inset-0 bg-[radial-gradient(1100px_400px_at_20%_-20%,rgba(var(--accent)/0.35),transparent_60%),radial-gradient(900px_350px_at_80%_0%,rgba(var(--accent-2)/0.25),transparent_55%),linear-gradient(to_bottom,rgb(var(--surface)),rgb(var(--surface-2)))]" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/35 via-black/10 to-transparent dark:from-black/50 dark:via-black/20" />
        </div>

        <div className="relative px-5 pb-6 pt-0 md:px-8">
          <div className="-mt-10 flex flex-col gap-4 md:-mt-12 md:flex-row md:items-end md:justify-between">
            <div className="flex items-end gap-4">
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

              <div className="pb-1">
                <h1 className="text-xl font-semibold tracking-[-0.03em] text-[rgb(var(--fg))] md:text-2xl">
                  {displayName}
                </h1>
                <p className="mt-1 text-sm text-[rgb(var(--muted))]">@{me.username}</p>
              </div>
            </div>
          </div>

          <div className="mt-5 grid gap-3">
            <p className="text-sm leading-relaxed text-[rgb(var(--fg))]">
              {me.bio ? me.bio : <span className="text-[rgb(var(--muted))]">No bio yet. Add one that feels you.</span>}
            </p>
          </div>

          <div className="mt-6 grid grid-cols-3 divide-x divide-[rgb(var(--border))]/70 overflow-hidden rounded-2xl bg-[rgb(var(--card-2))] ring-1 ring-[rgb(var(--border))]/70">
            {[
              { label: "Posts", value: String(posts.length) },
              { label: "Followers", value: String(me.followers_count) },
              { label: "Following", value: String(me.following_count) },
            ].map((s) => (
              <div key={s.label} className="px-4 py-3 text-center">
                <div className="text-sm font-semibold tracking-[-0.02em] text-[rgb(var(--fg))]">{s.value}</div>
                <div className="mt-0.5 text-[11px] text-[rgb(var(--muted))]">{s.label}</div>
              </div>
            ))}
          </div>

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

          <div className="mt-5 pb-2">
            {activeItems.length === 0 && !activeLoading ? (
              <p className="text-center text-xs text-[rgb(var(--muted))]">
                {tab === "posts" ? "You have not posted yet." : "You have no saved posts yet."}
              </p>
            ) : (
              <div className="grid grid-cols-3 gap-2 md:gap-3">
                {activeItems.map((item) => {
                  const media = item.media[0];
                  return (
                    <Link
                      key={item.id}
                      href={`/posts/${item.id}`}
                      className="relative aspect-square overflow-hidden rounded-2xl bg-[rgb(var(--card-2))] ring-1 ring-[rgb(var(--border))]/70"
                    >
                      {media ? (
                        <Image
                          src={media.url}
                          alt={item.caption || `Post ${item.id}`}
                          fill
                          className="object-cover"
                          sizes="(min-width: 768px) 33vw, 33vw"
                        />
                      ) : null}
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {activeLoading ? <p className="mt-4 text-sm text-[rgb(var(--muted))]">Loading more...</p> : null}
      <div ref={sentinelRef} className="h-6 w-full" />
    </div>
  );
}
