"use client";

import Image from "next/image";
import Link from "next/link";
import { Heart, Bookmark, MessageCircle } from "lucide-react";
import type { PostItem } from "@/lib/social";

type PostCardProps = {
  post: PostItem;
  onToggleLike?: (post: PostItem) => Promise<void>;
  onToggleSave?: (post: PostItem) => Promise<void>;
  showCaption?: boolean;
};

export function PostCard({
  post,
  onToggleLike,
  onToggleSave,
  showCaption = true,
}: PostCardProps) {
  const media = post.media[0];

  return (
    <article className="overflow-hidden rounded-3xl bg-[rgb(var(--card))] ring-1 ring-[rgb(var(--border))]/70">
      {media ? (
        <Link href={`/posts/${post.id}`} className="relative block aspect-[4/5] w-full">
          <Image
            src={media.url}
            alt={post.caption || `${post.author.username} post`}
            fill
            className="object-cover"
            sizes="(min-width: 1024px) 560px, 100vw"
          />
        </Link>
      ) : null}

      <div className="space-y-3 p-4">
        <div className="flex items-center justify-between gap-3">
          <Link href={`/p/${post.author.username}`} className="text-sm font-semibold text-[rgb(var(--fg))]">
            @{post.author.username}
          </Link>
          <div className="text-xs text-[rgb(var(--muted))]">
            {new Date(post.created_at).toLocaleString()}
          </div>
        </div>

        {showCaption && post.caption ? (
          <p className="text-sm leading-relaxed text-[rgb(var(--fg))]">{post.caption}</p>
        ) : null}

        <div className="flex items-center gap-2 text-sm">
          <button
            type="button"
            onClick={() => void onToggleLike?.(post)}
            className="inline-flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-[rgb(var(--fg))] ring-1 ring-[rgb(var(--border))]/70 transition hover:bg-[rgb(var(--card-2))]"
          >
            <Heart className={`h-4 w-4 ${post.viewer_liked ? "fill-current" : ""}`} />
            <span>{post.like_count}</span>
          </button>

          <Link
            href={`/posts/${post.id}`}
            className="inline-flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-[rgb(var(--fg))] ring-1 ring-[rgb(var(--border))]/70 transition hover:bg-[rgb(var(--card-2))]"
          >
            <MessageCircle className="h-4 w-4" />
            <span>{post.comment_count}</span>
          </Link>

          <button
            type="button"
            onClick={() => void onToggleSave?.(post)}
            className="ml-auto inline-flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-[rgb(var(--fg))] ring-1 ring-[rgb(var(--border))]/70 transition hover:bg-[rgb(var(--card-2))]"
          >
            <Bookmark className={`h-4 w-4 ${post.viewer_saved ? "fill-current" : ""}`} />
          </button>
        </div>
      </div>
    </article>
  );
}
