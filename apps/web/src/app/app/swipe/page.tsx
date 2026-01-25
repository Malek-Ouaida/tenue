export default function SwipePage() {
  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-8">
      <div className="rounded-3xl bg-[rgb(var(--card))] p-6 ring-1 ring-[rgb(var(--border))]/70">
        <h1 className="text-xl font-semibold text-[rgb(var(--fg))]">Swipe Shopping</h1>
        <p className="mt-2 text-sm text-[rgb(var(--muted))]">
          Tinder-style shopping feed (coming soon).
        </p>

        <div className="mt-6 flex flex-col items-center gap-4">
          <div className="relative w-full max-w-md overflow-hidden rounded-[28px] bg-[rgb(var(--card-2))] p-6 text-center ring-1 ring-[rgb(var(--border))]/70">
            <div className="absolute inset-0 bg-[radial-gradient(240px_120px_at_20%_20%,rgba(var(--accent)/0.18),transparent_60%),radial-gradient(240px_120px_at_80%_80%,rgba(var(--accent-2)/0.16),transparent_65%)]" />
            <div className="relative">
              <div className="text-sm font-medium text-[rgb(var(--fg))]">Card mock</div>
              <div className="mt-2 text-xs text-[rgb(var(--muted))]">Outfit preview + details</div>
              <div className="mt-6 h-48 w-full rounded-2xl bg-[rgb(var(--card))] ring-1 ring-[rgb(var(--border))]/70" />
            </div>
          </div>

          <div className="flex w-full max-w-md items-center gap-3">
            <button
              type="button"
              className="h-11 flex-1 rounded-2xl bg-[rgb(var(--card-2))] text-sm font-medium text-[rgb(var(--fg))] ring-1 ring-[rgb(var(--border))]/70 transition hover:bg-[rgb(var(--card))]"
            >
              Nope
            </button>
            <button
              type="button"
              className="h-11 flex-1 rounded-2xl text-sm font-medium text-white shadow-[0_12px_30px_-16px_rgba(2,6,23,0.55)] transition hover:brightness-105 active:brightness-95
                bg-[linear-gradient(135deg,rgb(var(--accent))_0%,rgb(var(--accent-2))_100%)]
                dark:text-zinc-950 dark:bg-[linear-gradient(135deg,rgba(var(--accent)/0.9)_0%,rgba(var(--accent-2)/0.9)_100%)]"
            >
              Save
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
