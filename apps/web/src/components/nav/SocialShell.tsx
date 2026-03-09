"use client";

import { Search } from "lucide-react";
import { usePathname } from "next/navigation";

import { AppSidebar } from "@/components/nav/AppSidebar";
import { MobileNav } from "@/components/nav/MobileNav";
import { Input } from "@/components/ui/Input";

function useSocialShell(pathname: string): boolean {
  return (
    pathname === "/feed" ||
    pathname.startsWith("/feed/") ||
    pathname === "/explore" ||
    pathname.startsWith("/explore/") ||
    pathname === "/post/new" ||
    pathname.startsWith("/posts/") ||
    pathname.startsWith("/p/") ||
    pathname === "/app" ||
    pathname.startsWith("/app/")
  );
}

export function SocialShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const showShell = useSocialShell(pathname);

  if (!showShell) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-[rgb(var(--surface))]">
      <div className="mx-auto flex w-full max-w-[1400px] gap-6 px-4 pb-24 pt-6 lg:px-6 lg:pb-8">
        <aside className="sticky top-6 hidden h-[calc(100vh-3rem)] w-[272px] shrink-0 lg:block">
          <AppSidebar />
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <div className="mx-auto w-full max-w-6xl">
            <div className="mb-6 flex items-center gap-3 rounded-2xl bg-[rgb(var(--card))] px-4 py-3 ring-1 ring-[rgb(var(--border))]/70">
              <Search className="h-4 w-4 text-[rgb(var(--muted))]" />
              <Input
                placeholder="Search creators, posts, and tags (coming soon)"
                className="h-10 border-0 bg-transparent px-0 text-[rgb(var(--fg))] focus:ring-0"
              />
            </div>

            <main className="min-w-0">{children}</main>
          </div>
        </div>
      </div>

      <MobileNav />
    </div>
  );
}
