"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { ApiError, clearTokens, getErrorMessage } from "@/lib/api";
import {
  type EngagementState,
  type PostItem,
  fetchExploreFeed,
  likePost,
  savePost,
  unlikePost,
  unsavePost,
} from "@/lib/social";
import { PostCard } from "@/components/social/PostCard";

export default function ExplorePage() {
  const router = useRouter();
  const [posts, setPosts] = useState<PostItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const sentinelRef = useRef<HTMLDivElement | null>(null);

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

        const page = await fetchExploreFeed(cursor, 20, "recent");
        setPosts((prev) => (append ? [...prev, ...page.items] : page.items));
        setNextCursor(page.next_cursor);
      } catch (e: unknown) {
        if (e instanceof ApiError && (e.status === 401 || e.status === 403)) {
          clearTokens();
          router.replace("/login");
          return;
        }
        toast.error(getErrorMessage(e, "Failed to load explore feed."));
      } finally {
        setLoadingInitial(false);
        setLoadingMore(false);
      }
    },
    [router]
  );

  useEffect(() => {
    void loadPage(null, false);
  }, [loadPage]);

  useEffect(() => {
    const node = sentinelRef.current;
    if (!node || !nextCursor || loadingMore || loadingInitial) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting && nextCursor) {
          void loadPage(nextCursor, true);
        }
      },
      { rootMargin: "200px" }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [loadPage, loadingInitial, loadingMore, nextCursor]);

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
      }
    },
    [applyEngagement]
  );

  return (
    <main className="mx-auto w-full max-w-2xl space-y-6 px-4 py-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold text-[rgb(var(--fg))]">Explore</h1>
        <p className="text-sm text-[rgb(var(--muted))]">Global discovery feed (recent mode).</p>
      </div>

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

      {loadingInitial ? <p className="text-sm text-[rgb(var(--muted))]">Loading explore feed...</p> : null}
      {loadingMore ? <p className="text-sm text-[rgb(var(--muted))]">Loading more...</p> : null}
      {!loadingInitial && posts.length === 0 ? (
        <p className="text-sm text-[rgb(var(--muted))]">No posts to explore yet.</p>
      ) : null}

      <div ref={sentinelRef} className="h-6 w-full" />
    </main>
  );
}
