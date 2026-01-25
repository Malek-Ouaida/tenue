"use client";

import Image from "next/image";
import { useEffect, useRef } from "react";

export type FloatingTile = {
  id: string;
  src: string;
  alt?: string;
  priority?: boolean;
  sizes?: string;
  width: string;
  height: string;
  x: string;
  y: string;
  depth: number;
  z: number;
  className?: string;
  overlayClassName?: string;
  drift: {
    ampX: number;
    ampY: number;
    speed: number;
    phase: number;
  };
};

export function FloatingTiles({
  tiles,
  isFrozen,
  isHidden,
  offsets,
  isVisible = true,
}: {
  tiles: FloatingTile[];
  isFrozen?: boolean;
  isHidden?: boolean;
  offsets?: Record<string, { x: number; y: number }>;
  isVisible?: boolean;
}) {
  const tileRefs = useRef<Array<HTMLDivElement | null>>([]);

  useEffect(() => {
    const tileElements = tileRefs.current;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    if (prefersReducedMotion) {
      tileElements.forEach((el, index) => {
        const tile = tiles[index];
        if (!el || !tile) return;
        const offset = offsets?.[tile.id];
        const x = offset?.x ?? 0;
        const y = offset?.y ?? 0;
        el.style.transform = `translate3d(${x.toFixed(2)}px, ${y.toFixed(2)}px, 0)`;
      });
      return;
    }

    if (isFrozen) return;

    const supportsPointer = window.matchMedia("(pointer: fine)").matches;
    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;

    const handleMove = (event: MouseEvent) => {
      if (!supportsPointer) return;
      const width = window.innerWidth || 1;
      const height = window.innerHeight || 1;
      const x = event.clientX / width;
      const y = event.clientY / height;
      targetX = (x - 0.5) * 2;
      targetY = (y - 0.5) * 2;
    };

    const handleOut = (event: MouseEvent) => {
      if (!event.relatedTarget) {
        targetX = 0;
        targetY = 0;
      }
    };

    if (supportsPointer) {
      window.addEventListener("mousemove", handleMove);
      window.addEventListener("mouseout", handleOut);
    }

    const start = performance.now();
    let frame = 0;

    const update = () => {
      const now = performance.now();
      const time = (now - start) / 1000;

      currentX += (targetX - currentX) * 0.06;
      currentY += (targetY - currentY) * 0.06;

      tiles.forEach((tile, index) => {
        const el = tileElements[index];
        if (!el) return;

        const offset = offsets?.[tile.id];
        const driftX =
          Math.sin(time * tile.drift.speed + tile.drift.phase) * tile.drift.ampX;
        const driftY =
          Math.cos(time * tile.drift.speed + tile.drift.phase) * tile.drift.ampY;
        const parallaxX = supportsPointer ? currentX * tile.depth * 18 : 0;
        const parallaxY = supportsPointer ? currentY * tile.depth * 18 : 0;
        const x = driftX + parallaxX + (offset?.x ?? 0);
        const y = driftY + parallaxY + (offset?.y ?? 0);

        el.style.transform = `translate3d(${x.toFixed(2)}px, ${y.toFixed(2)}px, 0)`;
      });

      frame = requestAnimationFrame(update);
    };

    frame = requestAnimationFrame(update);

    return () => {
      if (supportsPointer) {
        window.removeEventListener("mousemove", handleMove);
        window.removeEventListener("mouseout", handleOut);
      }
      cancelAnimationFrame(frame);
    };
  }, [tiles, isFrozen, offsets]);

  useEffect(() => {
    if (!offsets) return;
    tileRefs.current.forEach((el, index) => {
      const tile = tiles[index];
      if (!el || !tile) return;
      const offset = offsets[tile.id];
      if (!offset) return;
      el.style.transform = `translate3d(${offset.x.toFixed(2)}px, ${offset.y.toFixed(
        2,
      )}px, 0)`;
    });
  }, [offsets, tiles]);

  return (
    <div
      className={[
        "pointer-events-none absolute inset-0 transition-opacity duration-100",
        isHidden || !isVisible ? "opacity-0" : "opacity-100",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {tiles.map((tile, index) => (
        <div
          key={tile.id}
          className={[
            "absolute -translate-x-1/2 -translate-y-1/2",
            tile.className,
          ]
            .filter(Boolean)
            .join(" ")}
          style={{ left: tile.x, top: tile.y, width: tile.width, height: tile.height, zIndex: tile.z }}
        >
          <div
            ref={(el) => {
              tileRefs.current[index] = el;
            }}
            data-floating-tile
            data-tile-id={tile.id}
            className="pointer-events-auto h-full w-full will-change-transform"
          >
            <div className="group relative h-full w-full overflow-hidden rounded-[22px] bg-[rgb(var(--card))]/60 shadow-[0_24px_80px_rgb(var(--fg)/0.35)] ring-1 ring-[rgb(var(--border))]/70 transition duration-500 ease-out hover:shadow-[0_30px_110px_rgb(var(--fg)/0.45)] motion-reduce:transition-none">
              <Image
                src={tile.src}
                alt={tile.alt ?? ""}
                fill
                sizes={
                  tile.sizes ??
                  "(min-width: 1280px) 240px, (min-width: 768px) 200px, 160px"
                }
                className="object-cover transition duration-500 ease-out group-hover:scale-[1.03] motion-reduce:transform-none motion-reduce:group-hover:scale-100"
                priority={tile.priority}
                aria-hidden={tile.alt ? undefined : true}
              />
              <div
                className={["absolute inset-0", tile.overlayClassName].filter(Boolean).join(" ")}
                style={{
                  backgroundImage:
                    "linear-gradient(to top, rgb(var(--surface-2) / 0.55), transparent 55%, rgb(var(--surface) / 0.18))",
                }}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
