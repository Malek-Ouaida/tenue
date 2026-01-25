"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { FloatingTiles } from "@/components/landing/FloatingTiles";
import { LandingHero } from "@/components/landing/LandingHero";
import { TopNav } from "@/components/landing/TopNav";
import { useLandingTransition } from "@/components/landing/useLandingTransition";
import { floatingTiles } from "@/components/landing/tiles";

type TileOffset = Record<string, { x: number; y: number }>;

export function Landing() {
  const router = useRouter();
  const heroRef = useRef<HTMLDivElement>(null);
  const [tileOffsets, setTileOffsets] = useState<TileOffset>({});
  const [tilesVisible, setTilesVisible] = useState(false);

  const { startTransition, isTransitioning, hideTiles, heroHidden, overlayTiles, phase } =
    useLandingTransition(floatingTiles);

  const handleSignUp = useCallback(() => {
    startTransition("/register");
  }, [startTransition]);

  const handleLogIn = useCallback(() => {
    startTransition("/login");
  }, [startTransition]);

  useEffect(() => {
    router.prefetch("/login");
    router.prefetch("/register");
  }, [router]);

  useEffect(() => {
    const computeOffsets = () => {
      if (!heroRef.current) return;
      const heroRect = heroRef.current.getBoundingClientRect();
      const padding = window.innerWidth < 640 ? 48 : window.innerWidth < 1024 ? 72 : 96;
      const safeZone = {
        left: heroRect.left - padding,
        right: heroRect.right + padding,
        top: heroRect.top - padding,
        bottom: heroRect.bottom + padding,
      };
      const safeCenterX = (safeZone.left + safeZone.right) / 2;
      const safeCenterY = (safeZone.top + safeZone.bottom) / 2;

      const nodes = Array.from(
        document.querySelectorAll<HTMLElement>("[data-floating-tile]"),
      );
      const nextOffsets: TileOffset = {};

      nodes.forEach((node) => {
        const id = node.dataset.tileId;
        if (!id) return;
        const rect = node.getBoundingClientRect();
        if (!rect.width || !rect.height) return;

        const intersects =
          rect.left < safeZone.right &&
          rect.right > safeZone.left &&
          rect.top < safeZone.bottom &&
          rect.bottom > safeZone.top;

        if (!intersects) return;

        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const dirX = centerX - safeCenterX;
        const dirY = centerY - safeCenterY;
        const buffer = padding * 0.15;

        let dx = 0;
        let dy = 0;

        if (Math.abs(dirX) >= Math.abs(dirY)) {
          dx = dirX >= 0 ? safeZone.right - rect.left + buffer : safeZone.left - rect.right - buffer;
        } else {
          dy = dirY >= 0 ? safeZone.bottom - rect.top + buffer : safeZone.top - rect.bottom - buffer;
        }

        nextOffsets[id] = { x: dx, y: dy };
      });

      setTileOffsets(nextOffsets);
      setTilesVisible(true);
    };

    const frame = requestAnimationFrame(computeOffsets);
    const timeout = window.setTimeout(computeOffsets, 200);
    window.addEventListener("resize", computeOffsets);

    return () => {
      cancelAnimationFrame(frame);
      window.clearTimeout(timeout);
      window.removeEventListener("resize", computeOffsets);
    };
  }, []);

  const overlayVariants = useMemo(
    () => ({
      idle: (tile: (typeof overlayTiles)[number]) => ({
        x: 0,
        y: 0,
        scale: 1,
        rotate: tile.rotate,
        filter: "blur(0px)",
      }),
      gather: (tile: (typeof overlayTiles)[number]) => ({
        x: tile.dx + tile.clusterX,
        y: tile.dy + tile.clusterY,
        scale: 0.965,
        rotate: tile.rotate * 0.55,
        filter: "blur(0px)",
        transition: { duration: 0.32, ease: [0.22, 1, 0.36, 1] },
      }),
      compress: (tile: (typeof overlayTiles)[number]) => ({
        x: tile.dx + tile.clusterX * 0.7,
        y: tile.dy + tile.clusterY * 0.7,
        scale: 0.94,
        rotate: tile.rotate * 0.35,
        filter: `blur(${tile.blur + 0.4}px)`,
        transition: { duration: 0.12, ease: [0.4, 0, 0.2, 1] },
      }),
      explode: (tile: (typeof overlayTiles)[number]) => ({
        x: tile.dx + tile.clusterX * 0.7,
        y: tile.dy + tile.clusterY * 0.7,
        scale: tile.explodeScale,
        rotate: tile.rotate * 0.2,
        opacity: 0,
        filter: `blur(${tile.blur + 2.6}px)`,
        transition: { duration: 0.18, ease: [0.2, 0.9, 0.3, 1] },
      }),
    }),
    [overlayTiles],
  );

  return (
    <div className="relative min-h-screen overflow-hidden bg-[radial-gradient(1200px_600px_at_-10%_-10%,rgba(var(--accent)/0.14),transparent_60%),linear-gradient(to_bottom,rgb(var(--surface)),rgb(var(--surface-2)))] text-[rgb(var(--fg))] dark:bg-[radial-gradient(900px_500px_at_-10%_-10%,rgba(var(--accent)/0.18),transparent_60%),linear-gradient(to_bottom,rgb(var(--surface)),rgb(var(--surface-2)))]">
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            "radial-gradient(80% 60% at 50% 18%, rgb(var(--surface) / 0.08) 0%, rgb(var(--surface-2) / 0.4) 60%, rgb(var(--surface-2) / 0.7) 100%)",
        }}
      />
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.05] mix-blend-soft-light"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120' viewBox='0 0 120 120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='120' height='120' filter='url(%23n)' opacity='0.4'/%3E%3C/svg%3E\")",
        }}
      />

      <FloatingTiles
        tiles={floatingTiles}
        isFrozen={isTransitioning}
        isHidden={hideTiles}
        offsets={tileOffsets}
        isVisible={tilesVisible}
      />

      <AnimatePresence>
        {!heroHidden && (
          <motion.div
            key="landing-ui"
            className="relative z-20"
            initial={{ opacity: 1 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, transition: { duration: 0.12, ease: "easeOut" } }}
          >
            <TopNav />
            <LandingHero
              heroRef={heroRef}
              onSignUpClick={handleSignUp}
              onLogInClick={handleLogIn}
              isTransitioning={isTransitioning}
            />
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {overlayTiles.length > 0 && (
          <motion.div
            key="tile-overlay"
            className="pointer-events-none fixed inset-0 z-[55]"
            initial={{ opacity: 1 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            {overlayTiles.map((tile) => (
              <motion.div
                key={tile.id}
                custom={tile}
                initial={{
                  x: 0,
                  y: 0,
                  scale: 1,
                  rotate: tile.rotate,
                  opacity: 1,
                  filter: "blur(0px)",
                }}
                animate={phase}
                variants={overlayVariants}
                className="absolute will-change-transform"
                style={{
                  left: tile.rect.left,
                  top: tile.rect.top,
                  width: tile.rect.width,
                  height: tile.rect.height,
                  zIndex: tile.z,
                }}
              >
                <div
                  className="relative h-full w-full overflow-hidden rounded-[22px] bg-cover bg-center shadow-[0_24px_80px_rgb(var(--fg)/0.32)]"
                  style={{ backgroundImage: `url(${tile.src})` }}
                  aria-hidden="true"
                >
                  <div
                    className="absolute inset-0"
                    style={{
                      backgroundImage:
                        "linear-gradient(to top, rgb(var(--surface-2) / 0.55), transparent 55%, rgb(var(--surface) / 0.18))",
                    }}
                  />
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
