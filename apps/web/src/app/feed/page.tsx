"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { ApiError, clearTokens, getErrorMessage } from "@/lib/api";
import {
  type EngagementState,
  type PostItem,
  fetchFollowingFeed,
  likePost,
  savePost,
  unlikePost,
  unsavePost,
} from "@/lib/social";
import { trackError, trackEvent } from "@/lib/telemetry";
import { PostCard } from "@/components/social/PostCard";

export default function FeedPage() {
  const router = useRouter();
  const [posts, setPosts] = useState<PostItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
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

  const applyEngagement = useCallback((postId: string, payload: EngagementState) => {
    setPosts((prev) =>
      prev.map((item) =>
        item.id === postId
          ? {
              ...item,
              like_count: payload.like_count,
              viewer_liked: payload.viewer_liked,
              viewer_saved: payload.viewer_saved,
            }
          : item
      )
    );
  }, []);

  const loadPage = useCallback(
    async (cursor: string | null, append: boolean) => {
      try {
        if (append) setLoadingMore(true);
        else setLoadingInitial(true);

        const page = await fetchFollowingFeed(cursor, 20);
        setPosts((prev) => (append ? [...prev, ...page.items] : page.items));
        setNextCursor(page.next_cursor);
        setError(null);
        void trackEvent("feed.loaded", { append, count: page.items.length });
      } catch (e: unknown) {
        if (handleAuthError(e)) return;
        const message = getErrorMessage(e, "Failed to load feed.");
        setError(message);
        toast.error(message);
        void trackError("feed.load_failed", e, { append });
      } finally {
        setLoadingInitial(false);
        setLoadingMore(false);
      }
    },
    [handleAuthError]
  );

  useEffect(() => {
    void trackEvent("feed.open");
    void loadPage(null, false);
  }, [loadPage]);

  useEffect(() => {
    const node = sentinelRef.current;
    if (!node || !nextCursor || loadingMore || loadingInitial) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry?.isIntersecting && nextCursor) {
          void loadPage(nextCursor, true);
        }
      },
      { rootMargin: "200px" }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [nextCursor, loadingMore, loadingInitial, loadPage]);

  const onToggleLike = useCallback(
    async (post: PostItem) => {
      const optimistic: EngagementState = {
        like_count: post.viewer_liked ? Math.max(0, post.like_count - 1) : post.like_count + 1,
        viewer_liked: !post.viewer_liked,
        viewer_saved: post.viewer_saved,
      };

      applyEngagement(post.id, optimistic);
      try {
        const payload = post.viewer_liked ? await unlikePost(post.id) : await likePost(post.id);
        applyEngagement(post.id, payload);
      } catch (e: unknown) {
        applyEngagement(post.id, {
          like_count: post.like_count,
          viewer_liked: post.viewer_liked,
          viewer_saved: post.viewer_saved,
        });
        toast.error(getErrorMessage(e, "Failed to update like."));
        void trackError("feed.like_toggle_failed", e, { post_id: post.id });
      }
    },
    [applyEngagement]
  );

  const onToggleSave = useCallback(
    async (post: PostItem) => {
      const optimistic: EngagementState = {
        like_count: post.like_count,
        viewer_liked: post.viewer_liked,
        viewer_saved: !post.viewer_saved,
      };

      applyEngagement(post.id, optimistic);
      try {
        const payload = post.viewer_saved ? await unsavePost(post.id) : await savePost(post.id);
        applyEngagement(post.id, payload);
      } catch (e: unknown) {
        applyEngagement(post.id, {
          like_count: post.like_count,
          viewer_liked: post.viewer_liked,
          viewer_saved: post.viewer_saved,
        });
        toast.error(getErrorMessage(e, "Failed to update save."));
        void trackError("feed.save_toggle_failed", e, { post_id: post.id });
      }
    },
    [applyEngagement]
  );

  return (
    <div className="mx-auto w-full max-w-2xl space-y-6 px-4 py-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold text-[rgb(var(--fg))]">Feed</h1>
        <p className="text-sm text-[rgb(var(--muted))]">Posts from people you follow and your own account.</p>
      </div>

      {error ? (
        <div className="space-y-3 rounded-2xl bg-[rgb(var(--card))] px-4 py-3 ring-1 ring-[rgb(var(--border))]/70">
          <p className="text-sm text-[rgb(var(--fg))]">{error}</p>
          <button
            type="button"
            onClick={() => void loadPage(null, false)}
            className="rounded-xl bg-[rgb(var(--card-2))] px-3 py-1.5 text-xs text-[rgb(var(--fg))] ring-1 ring-[rgb(var(--border))]/70"
          >
            Retry
          </button>
        </div>
      ) : null}

      <div className="space-y-5">
        {posts.map((post) => (
          <PostCard
            key={post.id}
            post={post}
            onToggleLike={onToggleLike}
            onToggleSave={onToggleSave}
          />
        ))}
      </div>

      {loadingInitial ? <p className="text-sm text-[rgb(var(--muted))]">Loading feed...</p> : null}
      {loadingMore ? <p className="text-sm text-[rgb(var(--muted))]">Loading more...</p> : null}
      {!loadingInitial && !error && posts.length === 0 ? (
        <div className="space-y-2 rounded-2xl bg-[rgb(var(--card))] px-4 py-3 ring-1 ring-[rgb(var(--border))]/70">
          <p className="text-sm text-[rgb(var(--muted))]">No posts in your feed yet.</p>
          <button
            type="button"
            onClick={() => router.push("/explore")}
            className="rounded-xl bg-[rgb(var(--card-2))] px-3 py-1.5 text-xs text-[rgb(var(--fg))] ring-1 ring-[rgb(var(--border))]/70"
          >
            Explore posts
          </button>
        </div>
      ) : null}

      <div ref={sentinelRef} className="h-6 w-full" />
    </div>
  );
}
