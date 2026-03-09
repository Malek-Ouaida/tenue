import { apiFetch } from "@/lib/api";

export type Author = {
  username: string;
  display_name: string | null;
  avatar_url: string | null;
};

export type PostMedia = {
  url: string;
  width: number | null;
  height: number | null;
  order: number;
};

export type PostItem = {
  id: string;
  created_at: string;
  caption: string | null;
  author: Author;
  media: PostMedia[];
  like_count: number;
  comment_count: number;
  viewer_liked: boolean;
  viewer_saved: boolean;
};

export type FeedPage = {
  items: PostItem[];
  next_cursor: string | null;
};

export type CreatePostPayload = {
  caption?: string | null;
  media: Array<{
    key: string;
    width?: number | null;
    height?: number | null;
    order?: number;
  }>;
};

export type EngagementState = {
  like_count: number;
  viewer_liked: boolean;
  viewer_saved: boolean;
};

export type CommentItem = {
  id: string;
  post_id: string;
  created_at: string;
  body: string;
  author: Author;
  can_delete: boolean;
};

export type CommentsPage = {
  items: CommentItem[];
  next_cursor: string | null;
};

export type UserProfile = {
  user_id: string;
  username: string;
  display_name: string | null;
  bio: string | null;
  avatar_key: string | null;
  followers_count: number;
  following_count: number;
};

export type PublicProfileItem = {
  username: string;
  display_name: string | null;
  bio: string | null;
  avatar_url: string | null;
};

export type ProfilesPage = {
  items: PublicProfileItem[];
  next_cursor: string | null;
};

export type Relationship = {
  is_following: boolean;
  is_followed_by: boolean;
};

export type FollowAction = {
  ok: boolean;
  status: string;
};

export type UploadResult = {
  ok: boolean;
  key: string;
  url: string;
  content_type: string;
  size_bytes: number;
  width: number;
  height: number;
};

function withQuery(path: string, query: Record<string, string | number | null | undefined>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === null || value === undefined || value === "") continue;
    params.set(key, String(value));
  }
  const qs = params.toString();
  return qs ? `${path}?${qs}` : path;
}

export async function fetchFollowingFeed(cursor?: string | null, limit = 20): Promise<FeedPage> {
  return apiFetch<FeedPage>(withQuery("/feed", { cursor, limit }), { auth: true, cache: "no-store" });
}

export async function fetchExploreFeed(
  cursor?: string | null,
  limit = 20,
  mode: "recent" | "trending" = "recent"
): Promise<FeedPage> {
  return apiFetch<FeedPage>(withQuery("/explore", { mode, cursor, limit }), {
    auth: true,
    cache: "no-store",
  });
}

export async function fetchProfilePosts(
  username: string,
  cursor?: string | null,
  limit = 20
): Promise<FeedPage> {
  return apiFetch<FeedPage>(withQuery(`/users/${encodeURIComponent(username)}/posts`, { cursor, limit }), {
    auth: true,
    cache: "no-store",
  });
}

export async function fetchMySavedPosts(cursor?: string | null, limit = 20): Promise<FeedPage> {
  return apiFetch<FeedPage>(withQuery("/users/me/saved-posts", { cursor, limit }), {
    auth: true,
    cache: "no-store",
  });
}

export async function createPost(payload: CreatePostPayload): Promise<PostItem> {
  return apiFetch<PostItem>("/posts", {
    method: "POST",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export async function fetchPost(postId: string): Promise<PostItem> {
  return apiFetch<PostItem>(`/posts/${postId}`, { auth: true, cache: "no-store" });
}

export async function deletePost(postId: string): Promise<{ ok: boolean }> {
  return apiFetch<{ ok: boolean }>(`/posts/${postId}`, { method: "DELETE", auth: true });
}

export async function likePost(postId: string): Promise<EngagementState> {
  return apiFetch<EngagementState>(`/posts/${postId}/like`, { method: "POST", auth: true });
}

export async function unlikePost(postId: string): Promise<EngagementState> {
  return apiFetch<EngagementState>(`/posts/${postId}/like`, { method: "DELETE", auth: true });
}

export async function savePost(postId: string): Promise<EngagementState> {
  return apiFetch<EngagementState>(`/posts/${postId}/save`, { method: "POST", auth: true });
}

export async function unsavePost(postId: string): Promise<EngagementState> {
  return apiFetch<EngagementState>(`/posts/${postId}/save`, { method: "DELETE", auth: true });
}

export async function createComment(postId: string, body: string): Promise<CommentItem> {
  return apiFetch<CommentItem>(`/posts/${postId}/comments`, {
    method: "POST",
    auth: true,
    body: JSON.stringify({ body }),
  });
}

export async function fetchComments(
  postId: string,
  cursor?: string | null,
  limit = 20
): Promise<CommentsPage> {
  return apiFetch<CommentsPage>(withQuery(`/posts/${postId}/comments`, { cursor, limit }), {
    auth: true,
    cache: "no-store",
  });
}

export async function deleteComment(commentId: string): Promise<{ ok: boolean }> {
  return apiFetch<{ ok: boolean }>(`/comments/${commentId}`, { method: "DELETE", auth: true });
}

export async function uploadImage(file: File): Promise<UploadResult> {
  const form = new FormData();
  form.append("file", file);
  return apiFetch<UploadResult>("/s3/upload", {
    method: "POST",
    auth: true,
    body: form,
  });
}

export async function fetchProfile(username: string): Promise<UserProfile> {
  return apiFetch<UserProfile>(`/users/${encodeURIComponent(username)}`, {
    auth: true,
    cache: "no-store",
  });
}

export async function fetchRelationship(username: string): Promise<Relationship> {
  return apiFetch<Relationship>(`/users/${encodeURIComponent(username)}/relationship`, {
    auth: true,
    cache: "no-store",
  });
}

export async function followUser(username: string): Promise<FollowAction> {
  return apiFetch<FollowAction>(`/users/${encodeURIComponent(username)}/follow`, {
    method: "POST",
    auth: true,
  });
}

export async function unfollowUser(username: string): Promise<FollowAction> {
  return apiFetch<FollowAction>(`/users/${encodeURIComponent(username)}/follow`, {
    method: "DELETE",
    auth: true,
  });
}

export async function fetchFollowers(
  username: string,
  cursor?: string | null,
  limit = 20
): Promise<ProfilesPage> {
  return apiFetch<ProfilesPage>(
    withQuery(`/users/${encodeURIComponent(username)}/followers`, { cursor, limit }),
    {
      auth: true,
      cache: "no-store",
    }
  );
}

export async function fetchFollowing(
  username: string,
  cursor?: string | null,
  limit = 20
): Promise<ProfilesPage> {
  return apiFetch<ProfilesPage>(
    withQuery(`/users/${encodeURIComponent(username)}/following`, { cursor, limit }),
    {
      auth: true,
      cache: "no-store",
    }
  );
}
