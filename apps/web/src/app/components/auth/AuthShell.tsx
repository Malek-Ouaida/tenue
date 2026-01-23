import Image from "next/image";
import { ThemeToggle } from "@/app/components/theme/ThemeToggle";

export function AuthShell({
  mode,
  children
}: {
  mode: "login" | "register";
  children: React.ReactNode;
}) {
  const isLogin = mode === "login";

  return (
    <div className="min-h-screen">
      <div className="absolute right-6 top-6 z-20">
        <ThemeToggle />
      </div>

      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
        {/* FORM SIDE */}
        <div className={["flex items-center justify-center p-6 lg:p-12", isLogin ? "order-1" : "order-2"].join(" ")}>
          <div className="w-full max-w-md">
            <div className="mb-8">
              <div className="text-xs font-medium tracking-wide text-zinc-500 dark:text-zinc-400">
                tenue
              </div>
              <h1 className="mt-2 text-3xl font-semibold tracking-tight">
                {isLogin ? "Welcome back 👋" : "Create your account"}
              </h1>
              <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
                {isLogin
                  ? "Sign in to continue building your profile."
                  : "Choose a username and start curating your world."}
              </p>
            </div>

            <div
              className={[
                "rounded-2xl border border-zinc-200 bg-white/70 backdrop-blur",
                "shadow-[0_20px_60px_-30px_rgba(0,0,0,0.25)]",
                "p-6 lg:p-7",
                "dark:border-zinc-800 dark:bg-zinc-950/60"
              ].join(" ")}
            >
              {children}
            </div>

            <p className="mt-6 text-xs text-zinc-400">
              By continuing, you agree to tenue’s terms and privacy policy.
            </p>
          </div>
        </div>

        {/* ART SIDE */}
        <div className={["relative hidden lg:block", isLogin ? "order-2" : "order-1"].join(" ")}>
          {/* Soft page gradient */}
          <div className="absolute inset-0 bg-gradient-to-b from-zinc-50 to-white dark:from-zinc-950 dark:to-black" />

          {/* Framed artwork */}
          <div className="absolute inset-10 rounded-3xl overflow-hidden shadow-2xl ring-1 ring-black/10 dark:ring-white/10">
            <Image
              src="/auth/flowers.jpg"
              alt="Artwork"
              fill
              priority
              className="object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/55 via-black/10 to-transparent" />
          </div>

          {/* Subtle shine */}
          <div className="pointer-events-none absolute inset-10 rounded-3xl ring-1 ring-inset ring-white/10" />
        </div>
      </div>
    </div>
  );
}
