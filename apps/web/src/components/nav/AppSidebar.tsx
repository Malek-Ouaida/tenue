"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Shirt,
  Sparkles,
  CheckCircle2,
  Camera,
  User,
  Heart,
} from "lucide-react";
import { ThemeToggle } from "@/components/theme/ThemeToggle";

const NAV_ITEMS = [
  { label: "Explore", href: "/app", icon: Home },
  { label: "Swipe", href: "/app/swipe", icon: Heart },
  { label: "Closet", href: "/app/closet", icon: Shirt },
  { label: "AI Stylist", href: "/app/stylist", icon: Sparkles },
  { label: "Should I Buy?", href: "/app/should-i-buy", icon: CheckCircle2 },
  { label: "Try On", href: "/app/try-on", icon: Camera },
  { label: "Profile", href: "/app/me", icon: User },
];

function isActivePath(pathname: string, href: string) {
  if (href === "/app") return pathname === "/app";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-full flex-col rounded-[28px] bg-[rgb(var(--card))] px-4 py-5 ring-1 ring-[rgb(var(--border))]/70">
      <Link href="/app" className="group mb-6 flex items-center gap-3 px-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[rgb(var(--fg))] text-lg font-semibold text-[rgb(var(--surface))]">
          t
        </div>
        <div>
          <div className="text-sm font-semibold tracking-[-0.02em] text-[rgb(var(--fg))]">
            tenue
          </div>
          <div className="text-xs text-[rgb(var(--muted))]">Curated wardrobe</div>
        </div>
      </Link>

      <div className="mb-3 px-2 text-[11px] font-medium uppercase tracking-[0.2em] text-[rgb(var(--muted))]">
        Navigation
      </div>

      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          const active = isActivePath(pathname, item.href);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={[
                "flex items-center gap-3 rounded-2xl px-3 py-2 text-sm font-medium transition",
                active
                  ? "bg-[rgb(var(--fg))] text-[rgb(var(--surface))]"
                  : "text-[rgb(var(--fg))] hover:bg-[rgb(var(--card-2))]",
              ].join(" ")}
            >
              <Icon className="h-4 w-4" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto flex items-center justify-between gap-3 rounded-2xl bg-[rgb(var(--card-2))] px-3 py-3 ring-1 ring-[rgb(var(--border))]/70">
        <div>
          <div className="text-xs font-medium text-[rgb(var(--fg))]">Theme</div>
          <div className="text-[11px] text-[rgb(var(--muted))]">Light / Dark</div>
        </div>
        <ThemeToggle />
      </div>

      <div className="mt-3 px-2 text-[11px] text-[rgb(var(--muted))]">
        Tenue • Build your closet
      </div>
    </div>
  );
}
