import Link from "next/link";
import { ThemeLogo } from "@/components/theme/ThemeLogo";

export function TopNav() {
  return (
    <header className="relative z-20 px-6 pt-6">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-start">
        <Link
          href="/"
          className="flex items-center gap-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgb(var(--fg))]/70 focus-visible:ring-offset-2 focus-visible:ring-offset-[rgb(var(--surface))]"
          aria-label="Tenue home"
        >
          <ThemeLogo
            width={120}
            height={28}
            className="h-7 w-auto"
            lightSrc="/brand/tenue_black.png"
            darkSrc="/brand/tenue_white.png"
          />
        </Link>
      </div>
    </header>
  );
}
