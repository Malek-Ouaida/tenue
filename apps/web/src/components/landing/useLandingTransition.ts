"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import type { FloatingTile } from "@/components/landing/FloatingTiles";

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

type OverlayTile = {
  id: string;
  src: string;
  rect: { left: number; top: number; width: number; height: number };
  dx: number;
  dy: number;
  clusterX: number;
  clusterY: number;
  depth: number;
  z: number;
  rotate: number;
  blur: number;
  explodeScale: number;
};

type Phase = "idle" | "gather" | "compress" | "explode";

export function useLandingTransition(tiles: FloatingTile[]) {
  const router = useRouter();
  const runningRef = useRef(false);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [hideTiles, setHideTiles] = useState(false);
  const [heroHidden, setHeroHidden] = useState(false);
  const [overlayTiles, setOverlayTiles] = useState<OverlayTile[]>([]);
  const [phase, setPhase] = useState<Phase>("idle");

  const tilesById = useMemo(
    () => new Map(tiles.map((tile) => [tile.id, tile])),
    [tiles],
  );

  const startTransition = useCallback(
    async (href: string) => {
      if (runningRef.current) return;
      runningRef.current = true;

      const prefersReducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)",
      ).matches;
      const coarsePointer = window.matchMedia("(pointer: coarse)").matches;
      const markTransition = () => {
        try {
          window.sessionStorage.setItem("landing-transition", "1");
        } catch {
          // no-op
        }
      };

      setHeroHidden(true);
      setIsTransitioning(true);

      if (prefersReducedMotion) {
        markTransition();
        window.dispatchEvent(new Event("landing-transition"));
        await wait(120);
        router.push(href);
        runningRef.current = false;
        return;
      }

      await wait(90);

      const tileNodes = Array.from(
        document.querySelectorAll<HTMLElement>("[data-floating-tile]"),
      );

      if (!tileNodes.length) {
        markTransition();
        window.dispatchEvent(new Event("landing-transition"));
        await wait(120);
        router.push(href);
        runningRef.current = false;
        return;
      }

      const centerX = window.innerWidth / 2;
      const centerY = window.innerHeight / 2;

      const baseRadius = window.innerWidth < 640 ? 10 : window.innerWidth < 1024 ? 14 : 18;
      const goldenAngle = Math.PI * (3 - Math.sqrt(5));

      const overlays: OverlayTile[] = tileNodes
        .map((node, index) => {
          const id = node.dataset.tileId;
          const tile = id ? tilesById.get(id) : undefined;
          if (!tile) return null;
          const rect = node.getBoundingClientRect();
          if (!rect.width || !rect.height) return null;
          const tileCenterX = rect.left + rect.width / 2;
          const tileCenterY = rect.top + rect.height / 2;
          const depth = tile.depth;
          const rotate = (index % 2 === 0 ? 1 : -1) * (2 + depth * 3);
          const blur = depth < 0.2 ? 0.8 : 0.4;

          return {
            id: tile.id,
            src: tile.src,
            rect: { left: rect.left, top: rect.top, width: rect.width, height: rect.height },
            dx: centerX - tileCenterX,
            dy: centerY - tileCenterY,
            clusterX: 0,
            clusterY: 0,
            depth,
            z: tile.z,
            rotate,
            blur,
            explodeScale: 1.7 + depth * 1.2,
          };
        })
        .filter(Boolean) as OverlayTile[];

      const sortedByDepth = [...overlays].sort((a, b) => b.depth - a.depth);
      sortedByDepth.forEach((tile, index) => {
        const radius = Math.min(baseRadius * Math.sqrt(index + 1), baseRadius * 4.2);
        const angle = index * goldenAngle;
        tile.clusterX = Math.cos(angle) * radius;
        tile.clusterY = Math.sin(angle) * radius * 0.85;
      });

      setOverlayTiles(overlays);
      requestAnimationFrame(() => setHideTiles(true));

      if (coarsePointer) {
        setPhase("gather");
        await wait(160);
        setPhase("explode");
        markTransition();
        window.dispatchEvent(new Event("landing-transition"));
        await wait(120);
        router.push(href);
        return;
      }

      setPhase("gather");
      await wait(320);
      setPhase("compress");
      await wait(110);
      setPhase("explode");
      markTransition();
      window.dispatchEvent(new Event("landing-transition"));
      await wait(120);
      router.push(href);
    },
    [router, tilesById],
  );

  return { startTransition, isTransitioning, hideTiles, heroHidden, overlayTiles, phase };
}
