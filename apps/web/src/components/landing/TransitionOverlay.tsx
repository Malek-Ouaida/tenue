"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";

type Phase = "idle" | "cover";

export function TransitionOverlay() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [pending, setPending] = useState(false);
  const timeoutRef = useRef<number | null>(null);
  const pathname = usePathname();
  const triggerPathRef = useRef<string | null>(null);
  const coverStartedAtRef = useRef<number | null>(null);

  useEffect(() => {
    const handleTrigger = () => {
      if (timeoutRef.current) window.clearTimeout(timeoutRef.current);
      triggerPathRef.current = pathname;
      coverStartedAtRef.current = performance.now();
      setPhase("cover");
      setPending(true);
    };

    window.addEventListener("landing-transition", handleTrigger);

    return () => {
      window.removeEventListener("landing-transition", handleTrigger);
      if (timeoutRef.current) window.clearTimeout(timeoutRef.current);
    };
  }, []);

  useEffect(() => {
    if (!pending) return;
    if (triggerPathRef.current && pathname === triggerPathRef.current) return;
    const elapsed = coverStartedAtRef.current
      ? performance.now() - coverStartedAtRef.current
      : 0;
    const delay = Math.max(0, 180 - elapsed);
    timeoutRef.current = window.setTimeout(() => {
      setPhase("idle");
      setPending(false);
      triggerPathRef.current = null;
      coverStartedAtRef.current = null;
    }, delay + 200);
  }, [pathname, pending]);

  return (
    <div
      aria-hidden="true"
      className={[
        "pointer-events-none fixed inset-0 z-[70]",
        "bg-[radial-gradient(1200px_600px_at_-10%_-10%,rgba(var(--accent)/0.14),transparent_60%),linear-gradient(to_bottom,rgb(var(--surface)),rgb(var(--surface-2)))]",
        "dark:bg-[radial-gradient(900px_500px_at_-10%_-10%,rgba(var(--accent)/0.18),transparent_60%),linear-gradient(to_bottom,rgb(var(--surface)),rgb(var(--surface-2)))]",
        phase === "cover" ? "opacity-100" : "opacity-0",
        "transition-opacity duration-200 ease-out",
      ].join(" ")}
    />
  );
}
