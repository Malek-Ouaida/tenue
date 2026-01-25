"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Shirt, Camera, User, Heart } from "lucide-react";

const NAV_ITEMS = [
  { label: "Explore", href: "/app", icon: Home },
  { label: "Swipe", href: "/app/swipe", icon: Heart },
  { label: "Closet", href: "/app/closet", icon: Shirt },
  { label: "Try On", href: "/app/try-on", icon: Camera },
  { label: "Profile", href: "/app/me", icon: User },
];

function isActivePath(pathname: string, href: string) {
  if (href === "/app") return pathname === "/app";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function MobileNav() {
  const pathname = usePathname();

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 border-t border-[rgb(var(--border))]/70 bg-[rgb(var(--surface))]/80 backdrop-blur lg:hidden">
      <nav className="mx-auto flex max-w-md items-center justify-between px-4 py-2">
        {NAV_ITEMS.map((item) => {
          const active = isActivePath(pathname, item.href);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={[
                "flex flex-1 flex-col items-center gap-1 rounded-2xl px-2 py-2 text-[11px] font-medium transition",
                active
                  ? "bg-[rgb(var(--card))] text-[rgb(var(--fg))] ring-1 ring-[rgb(var(--border))]/70"
                  : "text-[rgb(var(--muted))]",
              ].join(" ")}
            >
              <Icon className="h-4 w-4" />
              <span className="leading-none">{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
