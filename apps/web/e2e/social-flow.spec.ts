import { expect, test } from "@playwright/test";

const FEED_RESPONSE = {
  items: [
    {
      id: "11111111-1111-1111-1111-111111111111",
      created_at: "2026-01-01T12:00:00Z",
      caption: "hello fit",
      author: { username: "alice", display_name: "Alice", avatar_url: null },
      media: [
        {
          url: "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?w=1200",
          width: 1200,
          height: 1600,
          order: 0,
        },
      ],
      like_count: 0,
      comment_count: 0,
      viewer_liked: false,
      viewer_saved: false,
    },
  ],
  next_cursor: null,
};

test("login redirects to /feed after successful auth", async ({ page }) => {
  await page.route("**/events/client", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true }) });
  });
  await page.route("**/auth/login", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ access_token: "a", refresh_token: "r" }),
    });
  });
  await page.route("**/feed?*", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(FEED_RESPONSE) });
  });
  await page.route("**/feed", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(FEED_RESPONSE) });
  });

  await page.goto("/login");
  await page.locator("input").nth(0).fill("alice@example.com");
  await page.locator("input").nth(1).fill("Password123!");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page).toHaveURL(/\/feed$/);
  await expect(page.getByText("hello fit")).toBeVisible();
});

test("feed like toggles optimistically and rolls back on API failure", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("tenue_tokens", JSON.stringify({ access: "a", refresh: "r" }));
  });

  await page.route("**/events/client", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true }) });
  });
  await page.route("**/feed?*", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(FEED_RESPONSE) });
  });
  await page.route("**/feed", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(FEED_RESPONSE) });
  });
  await page.route("**/posts/11111111-1111-1111-1111-111111111111/like", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 200));
    await route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ detail: { error: "internal_error" } }),
    });
  });

  await page.goto("/feed");

  const likeButton = page.getByTestId("like-11111111-1111-1111-1111-111111111111");
  await expect(likeButton).toContainText("0");
  await likeButton.click();

  await expect(likeButton).toContainText("1");
  await expect(likeButton).toContainText("0");
});
