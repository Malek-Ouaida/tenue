"use client";

import type { RefObject } from "react";
import { PrimaryButton, SecondaryButton } from "@/components/ui/Buttons";

type LandingHeroProps = {
  onSignUpClick: () => void;
  onLogInClick: () => void;
  isTransitioning?: boolean;
  heroRef?: RefObject<HTMLDivElement | null>;
};

export function LandingHero({
  onSignUpClick,
  onLogInClick,
  isTransitioning,
  heroRef,
}: LandingHeroProps) {
  return (
    <section className="relative z-20 flex min-h-[calc(100vh-96px)] flex-col items-center px-6 pb-16">
      <div
        ref={heroRef}
        className="flex flex-1 flex-col items-center justify-center text-center"
      >
        <h1 className="mt-5 max-w-2xl text-4xl font-semibold tracking-[-0.04em] text-[rgb(var(--fg))] sm:text-5xl md:text-6xl">
          Your space for style inspiration
        </h1>
        <p className="mt-5 max-w-xl text-sm text-[rgb(var(--muted))] sm:text-base">
          Curate outfits, collect references, and refine your signature in one
          calm, beautiful place.
        </p>

        <div className="mt-9 flex flex-row flex-wrap items-center justify-center gap-3">
          <PrimaryButton
            type="button"
            disabled={isTransitioning}
            className="h-11 w-auto px-7 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgb(var(--ring))] focus-visible:ring-offset-2 focus-visible:ring-offset-[rgb(var(--surface))]"
            onClick={() => onSignUpClick()}
          >
            Sign up
          </PrimaryButton>
          <SecondaryButton
            type="button"
            disabled={isTransitioning}
            onClick={() => onLogInClick()}
            className="h-11 w-auto px-6 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgb(var(--ring))] focus-visible:ring-offset-2 focus-visible:ring-offset-[rgb(var(--surface))] disabled:opacity-60 disabled:cursor-not-allowed"
          >
            Log in
          </SecondaryButton>
        </div>
      </div>
    </section>
  );
}
