import Image from "next/image";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { ThemeLogo } from "@/components/theme/ThemeLogo";

export function AuthShell({
  mode,
  children,
}: {
  mode: "login" | "register";
  children: React.ReactNode;
}) {
  const isLogin = mode === "login";

  return (
    <div className="min-h-screen bg-[radial-gradient(1200px_600px_at_-10%_-10%,rgba(var(--accent)/0.14),transparent_60%),linear-gradient(to_bottom,rgb(var(--surface)),rgb(var(--surface-2)))] text-[rgb(var(--fg))] dark:bg-[radial-gradient(900px_500px_at_-10%_-10%,rgba(var(--accent)/0.18),transparent_60%),linear-gradient(to_bottom,rgb(var(--surface)),rgb(var(--surface-2)))]">
      {/* Theme toggle */}
      <div className="absolute right-6 top-6 z-20">
        <ThemeToggle />
      </div>

      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
        {/* FORM SIDE */}
        <div
          className={[
            "flex items-center justify-center px-6 py-12 lg:px-16",
            isLogin ? "order-1" : "order-2",
          ].join(" ")}
        >
          <div className="w-full max-w-md">
            <div className="mb-10">
              <ThemeLogo
                className="mb-4 block h-auto w-[32px]"
                width={32}
                height={32}
                lightSrc="/brand/t_black.png"
                darkSrc="/brand/t_white.png"
              />
              <h1 className="mt-1 text-3xl font-semibold tracking-[-0.02em]">
                {isLogin ? "Welcome back 👋" : "Create your account"}
              </h1>
              <p className="mt-2 text-sm text-[rgb(var(--muted))]">
                {isLogin
                  ? "Sign in to continue building your profile."
                  : "Choose a username and start curating your world."}
              </p>
            </div>

            {/* PREMIUM CARD */}
            <div className="relative">
              <div className="pointer-events-none absolute -inset-2 rounded-[28px] bg-[radial-gradient(360px_180px_at_20%_-20%,rgba(var(--accent)/0.25),transparent_60%)] blur-2xl dark:bg-[radial-gradient(360px_180px_at_20%_-20%,rgba(var(--accent)/0.35),transparent_60%)]" />
              <div
                className={[
                  "relative rounded-3xl p-8",
                  "bg-[linear-gradient(180deg,rgb(var(--card))_0%,rgb(var(--card-2))_100%)]",
                  "shadow-[0_35px_90px_-45px_rgba(2,6,23,0.45)]",
                  "ring-1 ring-[rgb(var(--border))]/70",
                  "dark:shadow-[0_35px_90px_-45px_rgba(0,0,0,0.75)]",
                  "overflow-hidden",
                ].join(" ")}
              >
                <div className="pointer-events-none absolute inset-0 opacity-[0.18] [background-image:radial-gradient(rgba(255,255,255,0.16)_1px,transparent_1px)] [background-size:3px_3px] dark:opacity-[0.18]" />
                <div className="pointer-events-none absolute inset-x-0 top-0 h-16 rounded-t-3xl bg-[radial-gradient(120px_40px_at_20%_30%,rgba(var(--accent)/0.25),transparent_70%)] opacity-70 dark:opacity-90" />
                <div className="pointer-events-none absolute inset-x-6 top-0 h-px bg-[linear-gradient(to_right,transparent,rgba(var(--border)/0.9),transparent)]" />
                <div className="relative">{children}</div>
              </div>
            </div>

            <p className="mt-6 text-xs text-[rgb(var(--muted))]">
              By continuing, you agree to tenue’s terms and privacy policy.
            </p>
          </div>
        </div>

        {/* ART SIDE */}
        <div
          className={[
            "relative hidden lg:block",
            isLogin ? "order-2" : "order-1",
          ].join(" ")}
        >
          {/* Framed art */}
          <div className="absolute inset-10 overflow-hidden rounded-3xl shadow-2xl ring-1 ring-black/20 dark:ring-white/10">
            <Image
              src="/auth/flowers.jpg"
              alt="Artwork"
              fill
              priority
              className="object-cover"
              sizes="(min-width: 1024px) 50vw, 0vw"
            />
            {/* vignette */}
            <div className="absolute inset-0 bg-[linear-gradient(to_bottom,rgba(var(--surface)/0.10),rgba(var(--surface-2)/0.35))] dark:bg-[linear-gradient(to_bottom,rgba(var(--surface)/0.18),rgba(var(--surface-2)/0.45))]" />
            <div className="absolute inset-0 bg-gradient-to-t from-black/45 via-black/10 to-transparent dark:from-black/55 dark:via-black/20" />
          </div>

          {/* subtle glow around frame */}
          <div className="pointer-events-none absolute inset-10 rounded-3xl ring-1 ring-inset ring-white/10" />
        </div>
      </div>
    </div>
  );
}
