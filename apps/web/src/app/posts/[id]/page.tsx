"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { toast } from "sonner";

import { ApiError, clearTokens, getErrorMessage } from "@/lib/api";
import {
  type CommentItem,
  type EngagementState,
  type PostItem,
  createComment,
  deleteComment,
  fetchComments,
  fetchPost,
  likePost,
  savePost,
  unlikePost,
  unsavePost,
} from "@/lib/social";
import { PostCard } from "@/components/social/PostCard";

export default function PostDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const postId = params?.id;

  const [post, setPost] = useState<PostItem | null>(null);
  const [comments, setComments] = useState<CommentItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [commentBody, setCommentBody] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadingComments, setLoadingComments] = useState(false);

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

  const loadComments = useCallback(
    async (cursor: string | null, append: boolean) => {
      if (!postId) return;
      try {
        setLoadingComments(true);
        const page = await fetchComments(postId, cursor, 20);
        setComments((prev) => (append ? [...prev, ...page.items] : page.items));
        setNextCursor(page.next_cursor);
      } catch (e: unknown) {
        if (handleAuthError(e)) return;
        toast.error(getErrorMessage(e, "Failed to load comments."));
      } finally {
        setLoadingComments(false);
      }
    },
    [handleAuthError, postId]
  );

  useEffect(() => {
    if (!postId) return;

    const load = async () => {
      setLoading(true);
      try {
        const detail = await fetchPost(postId);
        setPost(detail);
        await loadComments(null, false);
      } catch (e: unknown) {
        if (handleAuthError(e)) return;
        toast.error(getErrorMessage(e, "Failed to load post."));
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, [handleAuthError, loadComments, postId]);

  const applyEngagement = useCallback((payload: EngagementState) => {
    setPost((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        like_count: payload.like_count,
        viewer_liked: payload.viewer_liked,
        viewer_saved: payload.viewer_saved,
      };
    });
  }, []);

  const onToggleLike = useCallback(
    async (item: PostItem) => {
      const optimistic: EngagementState = {
        like_count: item.viewer_liked ? Math.max(0, item.like_count - 1) : item.like_count + 1,
        viewer_liked: !item.viewer_liked,
        viewer_saved: item.viewer_saved,
      };
      applyEngagement(optimistic);

      try {
        const payload = item.viewer_liked ? await unlikePost(item.id) : await likePost(item.id);
        applyEngagement(payload);
      } catch (e: unknown) {
        applyEngagement({
          like_count: item.like_count,
          viewer_liked: item.viewer_liked,
          viewer_saved: item.viewer_saved,
        });
        toast.error(getErrorMessage(e, "Failed to update like."));
      }
    },
    [applyEngagement]
  );

  const onToggleSave = useCallback(
    async (item: PostItem) => {
      const optimistic: EngagementState = {
        like_count: item.like_count,
        viewer_liked: item.viewer_liked,
        viewer_saved: !item.viewer_saved,
      };
      applyEngagement(optimistic);

      try {
        const payload = item.viewer_saved ? await unsavePost(item.id) : await savePost(item.id);
        applyEngagement(payload);
      } catch (e: unknown) {
        applyEngagement({
          like_count: item.like_count,
          viewer_liked: item.viewer_liked,
          viewer_saved: item.viewer_saved,
        });
        toast.error(getErrorMessage(e, "Failed to update save."));
      }
    },
    [applyEngagement]
  );

  const onCommentSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!postId || !commentBody.trim()) return;

    try {
      const created = await createComment(postId, commentBody.trim());
      setComments((prev) => [created, ...prev]);
      setCommentBody("");
      setPost((prev) => (prev ? { ...prev, comment_count: prev.comment_count + 1 } : prev));
    } catch (e: unknown) {
      if (handleAuthError(e)) return;
      toast.error(getErrorMessage(e, "Failed to add comment."));
    }
  };

  const onDeleteComment = async (commentId: string) => {
    if (!postId) return;
    try {
      await deleteComment(commentId);
      setComments((prev) => prev.filter((comment) => comment.id !== commentId));
      setPost((prev) =>
        prev
          ? {
              ...prev,
              comment_count: Math.max(0, prev.comment_count - 1),
            }
          : prev
      );
    } catch (e: unknown) {
      if (handleAuthError(e)) return;
      toast.error(getErrorMessage(e, "Failed to delete comment."));
    }
  };

  if (loading) {
    return <main className="mx-auto w-full max-w-2xl px-4 py-6 text-sm text-[rgb(var(--muted))]">Loading post...</main>;
  }

  if (!post) {
    return <main className="mx-auto w-full max-w-2xl px-4 py-6 text-sm text-[rgb(var(--muted))]">Post not found.</main>;
  }

  return (
    <main className="mx-auto w-full max-w-2xl space-y-6 px-4 py-6">
      <PostCard post={post} onToggleLike={onToggleLike} onToggleSave={onToggleSave} />

      <section className="space-y-3 rounded-3xl bg-[rgb(var(--card))] p-4 ring-1 ring-[rgb(var(--border))]/70">
        <h2 className="text-sm font-semibold text-[rgb(var(--fg))]">Comments</h2>

        <form onSubmit={onCommentSubmit} className="flex gap-2">
          <input
            value={commentBody}
            onChange={(event) => setCommentBody(event.target.value)}
            maxLength={1000}
            placeholder="Write a comment"
            className="h-10 flex-1 rounded-xl border border-[rgb(var(--border))]/70 bg-[rgb(var(--surface))] px-3 text-sm text-[rgb(var(--fg))] outline-none"
          />
          <button
            type="submit"
            disabled={!commentBody.trim()}
            className="rounded-xl bg-[rgb(var(--fg))] px-4 text-sm font-medium text-[rgb(var(--surface))] disabled:opacity-60"
          >
            Post
          </button>
        </form>

        <div className="space-y-3">
          {comments.map((comment) => (
            <article
              key={comment.id}
              className="rounded-2xl bg-[rgb(var(--card-2))] px-3 py-2 text-sm text-[rgb(var(--fg))]"
            >
              <div className="mb-1 flex items-center justify-between gap-2 text-xs text-[rgb(var(--muted))]">
                <span>@{comment.author.username}</span>
                {comment.can_delete ? (
                  <button
                    type="button"
                    onClick={() => void onDeleteComment(comment.id)}
                    className="rounded-lg px-2 py-0.5 text-xs text-[rgb(var(--fg))] ring-1 ring-[rgb(var(--border))]/70"
                  >
                    Delete
                  </button>
                ) : null}
              </div>
              <p>{comment.body}</p>
            </article>
          ))}
        </div>

        {nextCursor ? (
          <button
            type="button"
            disabled={loadingComments}
            onClick={() => void loadComments(nextCursor, true)}
            className="rounded-xl bg-[rgb(var(--card-2))] px-3 py-1.5 text-xs text-[rgb(var(--fg))] ring-1 ring-[rgb(var(--border))]/70 disabled:opacity-60"
          >
            {loadingComments ? "Loading..." : "Load more comments"}
          </button>
        ) : null}
      </section>
    </main>
  );
}
