"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { ApiError, clearTokens, getErrorMessage } from "@/lib/api";
import { compressImage } from "@/lib/image-compress";
import { createPost, uploadImage } from "@/lib/social";

export default function NewPostPage() {
  const router = useRouter();
  const [caption, setCaption] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);

  const canSubmit = useMemo(() => files.length > 0 && !submitting, [files.length, submitting]);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!canSubmit) return;

    setSubmitting(true);
    const toastId = toast.loading("Publishing post...");

    try {
      const media: Array<{ key: string; width: number; height: number; order: number }> = [];

      for (let i = 0; i < files.length; i += 1) {
        const original = files[i];
        if (!original) continue;

        setProgress(`Processing image ${i + 1}/${files.length}`);
        const compressed = await compressImage(original, { maxDimension: 1600, quality: 0.8 });

        setProgress(`Uploading image ${i + 1}/${files.length}`);
        const uploaded = await uploadImage(compressed);

        media.push({
          key: uploaded.key,
          width: uploaded.width,
          height: uploaded.height,
          order: i,
        });
      }

      setProgress("Creating post");
      const created = await createPost({
        caption: caption.trim() || null,
        media,
      });

      toast.success("Post created.", { id: toastId });
      router.push(`/posts/${created.id}`);
    } catch (e: unknown) {
      if (e instanceof ApiError && (e.status === 401 || e.status === 403)) {
        clearTokens();
        router.replace("/login");
        return;
      }

      toast.error(getErrorMessage(e, "Failed to create post."), { id: toastId });
    } finally {
      setSubmitting(false);
      setProgress(null);
    }
  };

  return (
    <main className="mx-auto w-full max-w-2xl space-y-6 px-4 py-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold text-[rgb(var(--fg))]">Create Post</h1>
        <p className="text-sm text-[rgb(var(--muted))]">
          Images are compressed in-browser with safe fallback to originals.
        </p>
      </div>

      <form
        onSubmit={onSubmit}
        className="space-y-4 rounded-3xl bg-[rgb(var(--card))] p-5 ring-1 ring-[rgb(var(--border))]/70"
      >
        <div className="space-y-2">
          <label htmlFor="caption" className="block text-sm font-medium text-[rgb(var(--fg))]">
            Caption
          </label>
          <textarea
            id="caption"
            maxLength={2000}
            value={caption}
            onChange={(event) => setCaption(event.target.value)}
            placeholder="Write a caption..."
            className="min-h-28 w-full rounded-2xl border border-[rgb(var(--border))]/70 bg-[rgb(var(--surface))] px-3 py-2 text-sm text-[rgb(var(--fg))] outline-none"
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="media" className="block text-sm font-medium text-[rgb(var(--fg))]">
            Images
          </label>
          <input
            id="media"
            type="file"
            accept="image/*"
            multiple
            onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
            className="block w-full rounded-2xl border border-[rgb(var(--border))]/70 bg-[rgb(var(--surface))] px-3 py-2 text-sm text-[rgb(var(--fg))]"
          />
        </div>

        {files.length > 0 ? (
          <ul className="space-y-1 text-xs text-[rgb(var(--muted))]">
            {files.map((file) => (
              <li key={`${file.name}-${file.size}`}>{file.name}</li>
            ))}
          </ul>
        ) : null}

        {progress ? <p className="text-sm text-[rgb(var(--muted))]">{progress}...</p> : null}

        <button
          type="submit"
          disabled={!canSubmit}
          className="inline-flex h-11 items-center justify-center rounded-2xl bg-[rgb(var(--fg))] px-5 text-sm font-medium text-[rgb(var(--surface))] transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitting ? "Publishing..." : "Publish post"}
        </button>
      </form>
    </main>
  );
}
