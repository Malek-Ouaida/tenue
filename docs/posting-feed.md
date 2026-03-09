# Posting & Feed (Sprint 2)

## Endpoints

### Posts
- `POST /posts`
- `GET /posts/{post_id}`
- `DELETE /posts/{post_id}` (owner only)
- `POST /posts/{post_id}/like`
- `DELETE /posts/{post_id}/like`
- `POST /posts/{post_id}/save`
- `DELETE /posts/{post_id}/save`
- `POST /posts/{post_id}/comments`
- `GET /posts/{post_id}/comments`
- `DELETE /comments/{comment_id}` (owner only)

### Feeds
- `GET /feed` (following + self)
- `GET /explore?mode=recent` (`mode=trending` reserved; currently recent behavior)

### Profiles / Social Graph
- `GET /users/{username}/posts`
- `POST /users/{username}/follow`
- `DELETE /users/{username}/follow`
- `GET /users/{username}/followers`
- `GET /users/{username}/following`

### Upload
- `POST /s3/upload` (auth required, image allowlist + size guard + server-side MIME detection)

## Cursor Pagination Contract
All list endpoints return:

```json
{
  "items": [],
  "next_cursor": "base64url({\"created_at\":\"...\",\"id\":\"...\"}) | null"
}
```

Ordering everywhere is deterministic keyset pagination on:
- `created_at DESC`
- `id DESC` (tie-breaker)

## Example Requests

### Create Post
```bash
curl -X POST "$BASE_URL/posts" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{
    "caption": "Sunset fit",
    "media": [
      {"key":"uploads/abc.jpg","width":1080,"height":1350,"order":0}
    ]
  }'
```

### Following Feed
```bash
curl "$BASE_URL/feed?limit=20&cursor=$CURSOR" \
  -H "Authorization: Bearer $ACCESS"
```

### Comment Create
```bash
curl -X POST "$BASE_URL/posts/$POST_ID/comments" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"body":"Great look"}'
```

## Local Run

### Infrastructure
```bash
docker compose -f infra/docker-compose.yml up -d
```

### API
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Web
```bash
cd apps/web
pnpm install
pnpm dev
```

### API Checks
```bash
cd apps/api
source .venv/bin/activate
python -m ruff check app tests
python -m pytest tests -q
```

## Security
- Rate limits on login, post create, comment create, follow/unfollow, like/save toggles.
- Strict server-side image validation (JPEG/PNG/WebP), file size cap, MIME sniffing.
- Owner-only delete for posts/comments.
- Structured audit logs for login, upload, follow/unfollow, post/comment/engagement mutations.
