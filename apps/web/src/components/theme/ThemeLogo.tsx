"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useTheme } from "next-themes";

export function ThemeLogo({
  width = 140,
  height = 36,
  className,
  lightSrc = "/brand/tenue_black.png",
  darkSrc = "/brand/tenue_white.png",
}: {
  width?: number;
  height?: number;
  className?: string;
  lightSrc?: string;
  darkSrc?: string;
}) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return <div style={{ width, height }} className={className} />;
  }

  const src = resolvedTheme === "dark" ? darkSrc : lightSrc;

  return (
    <Image
      src={src}
      alt="tenue"
      width={width}
      height={height}
      className={className}
      priority
    />
  );
}
