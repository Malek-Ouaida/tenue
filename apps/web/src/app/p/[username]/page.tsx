"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { toast } from "sonner";

import { ApiError, clearTokens, getErrorMessage } from "@/lib/api";
import {
  type PostItem,
  type Relationship,
  type UserProfile,
  fetchProfile,
  fetchProfilePosts,
  fetchRelationship,
  followUser,
  unfollowUser,
} from "@/lib/social";
import { trackError, trackEvent } from "@/lib/telemetry";

export default function ProfilePage() {
  const params = useParams<{ username: string }>();
  const router = useRouter();
  const username = params?.username;

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [relationship, setRelationship] = useState<Relationship | null>(null);
  const [posts, setPosts] = useState<PostItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [busyFollow, setBusyFollow] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sentinelRef = useRef<HTMLDivElement | null>(null);

  const handleAuthError = useCallback(
    (error: unknown) => {
      if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
        clearTokens();
        router.replace("/login");
        return true;
      }
      return false;
    },
    [router]
  );

  const loadPosts = useCallback(
    async (cursor: string | null, append: boolean) => {
      if (!username) return;
      try {
        if (append) setLoadingMore(true);
        const page = await fetchProfilePosts(username, cursor, 20);
        setPosts((prev) => (append ? [...prev, ...page.items] : page.items));
        setNextCursor(page.next_cursor);
      } catch (e: unknown) {
        if (handleAuthError(e)) return;
        toast.error(getErrorMessage(e, "Failed to load profile posts."));
        void trackError("profile.posts_load_failed", e, { username, append });
      } finally {
        setLoadingMore(false);
      }
    },
    [handleAuthError, username]
  );

  const loadProfile = useCallback(async () => {
    if (!username) return;
    setLoadingInitial(true);
    setError(null);
    try {
      const [profileData, relationData] = await Promise.all([
        fetchProfile(username),
        fetchRelationship(username),
      ]);
      setProfile(profileData);
      setRelationship(relationData);
      await loadPosts(null, false);
      void trackEvent("profile.open", { username });
    } catch (e: unknown) {
      if (handleAuthError(e)) return;
      const message = getErrorMessage(e, "Failed to load profile.");
      setError(message);
      toast.error(message);
      void trackError("profile.load_failed", e, { username });
    } finally {
      setLoadingInitial(false);
    }
  }, [handleAuthError, loadPosts, username]);

  useEffect(() => {
    void loadProfile();
  }, [loadProfile]);

  useEffect(() => {
    const node = sentinelRef.current;
    if (!node || !nextCursor || loadingMore || loadingInitial) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting && nextCursor) {
          void loadPosts(nextCursor, true);
        }
      },
      { rootMargin: "200px" }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [loadPosts, loadingInitial, loadingMore, nextCursor]);

  const toggleFollow = async () => {
    if (!username || !relationship || busyFollow) return;

    const currentlyFollowing = relationship.is_following;
    setBusyFollow(true);

    setRelationship({ ...relationship, is_following: !currentlyFollowing });
    setProfile((prev) =>
      prev
        ? {
            ...prev,
            followers_count: Math.max(
              0,
              prev.followers_count + (currentlyFollowing ? -1 : 1)
            ),
          }
        : prev
    );

    try {
      if (currentlyFollowing) await unfollowUser(username);
      else await followUser(username);
      void trackEvent("profile.follow_toggled", { username, follow: !currentlyFollowing });
    } catch (e: unknown) {
      if (handleAuthError(e)) return;
      setRelationship({ ...relationship, is_following: currentlyFollowing });
      setProfile((prev) =>
        prev
          ? {
              ...prev,
              followers_count: Math.max(
                0,
                prev.followers_count + (currentlyFollowing ? 1 : -1)
              ),
            }
          : prev
      );
      toast.error(getErrorMessage(e, "Failed to update follow."));
      void trackError("profile.follow_toggle_failed", e, { username });
    } finally {
      setBusyFollow(false);
    }
  };

  if (loadingInitial) {
    return <div className="mx-auto w-full max-w-5xl px-4 py-6 text-sm text-[rgb(var(--muted))]">Loading profile...</div>;
  }

  if (!profile || error) {
    return (
      <div className="mx-auto w-full max-w-5xl space-y-3 px-4 py-6">
        <p className="text-sm text-[rgb(var(--muted))]">{error || "Profile not found."}</p>
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

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6 px-4 py-6">
      <section className="rounded-3xl bg-[rgb(var(--card))] p-5 ring-1 ring-[rgb(var(--border))]/70">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-2">
            <h1 className="text-2xl font-semibold text-[rgb(var(--fg))]">@{profile.username}</h1>
            <p className="text-sm text-[rgb(var(--muted))]">{profile.display_name || "No display name"}</p>
            <p className="text-sm text-[rgb(var(--fg))]">{profile.bio || "No bio yet."}</p>
            <div className="flex items-center gap-4 text-xs text-[rgb(var(--muted))]">
              <span>{profile.followers_count} followers</span>
              <span>{profile.following_count} following</span>
            </div>
          </div>

          {relationship ? (
            <button
              type="button"
              disabled={busyFollow}
              onClick={() => void toggleFollow()}
              className="inline-flex h-10 items-center justify-center rounded-2xl bg-[rgb(var(--fg))] px-4 text-sm font-medium text-[rgb(var(--surface))] disabled:opacity-60"
            >
              {relationship.is_following ? "Following" : "Follow"}
            </button>
          ) : null}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-[rgb(var(--fg))]">Posts</h2>
        {posts.length === 0 ? (
          <p className="text-sm text-[rgb(var(--muted))]">No posts yet.</p>
        ) : (
          <div className="grid grid-cols-3 gap-2 sm:gap-3">
            {posts.map((post) => {
              const media = post.media[0];
              return (
                <Link
                  key={post.id}
                  href={`/posts/${post.id}`}
                  className="relative aspect-square overflow-hidden rounded-2xl bg-[rgb(var(--card))] ring-1 ring-[rgb(var(--border))]/70"
                >
                  {media ? (
                    <Image
                      src={media.url}
                      alt={post.caption || `Post ${post.id}`}
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
      </section>

      {loadingMore ? <p className="text-sm text-[rgb(var(--muted))]">Loading more posts...</p> : null}
      <div ref={sentinelRef} className="h-6 w-full" />
    </div>
  );
}
