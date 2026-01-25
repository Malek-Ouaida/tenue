export default function ExplorePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-[-0.02em] text-[rgb(var(--fg))]">
          Explore
        </h1>
        <p className="mt-2 text-sm text-[rgb(var(--muted))]">
          Discover curated looks, pins, and styling ideas.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        {Array.from({ length: 12 }).map((_, index) => (
          <div
            key={index}
            className="relative aspect-[3/4] overflow-hidden rounded-2xl bg-[rgb(var(--card))] ring-1 ring-[rgb(var(--border))]/70"
          >
            <div className="absolute inset-0 bg-[radial-gradient(240px_120px_at_20%_20%,rgba(var(--accent)/0.18),transparent_60%),radial-gradient(240px_120px_at_80%_80%,rgba(var(--accent-2)/0.16),transparent_65%)]" />
            <div className="absolute inset-0 opacity-[0.12] [background-image:radial-gradient(rgba(255,255,255,0.2)_1px,transparent_1px)] [background-size:3px_3px]" />
            <div className="absolute bottom-3 left-3 right-3 rounded-xl bg-[rgb(var(--card-2))]/80 px-3 py-2 text-xs text-[rgb(var(--fg))] ring-1 ring-[rgb(var(--border))]/70">
              Editorial pin {index + 1}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
