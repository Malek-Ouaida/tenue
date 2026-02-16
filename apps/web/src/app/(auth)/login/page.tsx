"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { AuthShell } from "@/components/auth/AuthShell";
import { FloatingInput } from "@/components/ui/FloatingInput";
import { OAuthButton, PrimaryButton } from "@/components/ui/Buttons";
import { apiFetch, getErrorMessage, setTokens } from "@/lib/api";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "At least 8 characters"),
});

type FormValues = z.infer<typeof schema>;
type AuthResponse = { access_token: string; refresh_token: string };

export default function LoginPage() {
  const router = useRouter();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" },
    mode: "onChange",
  });
  const [skipIntro] = useState(() => {
    if (typeof window === "undefined") return false;
    const flag = window.sessionStorage.getItem("landing-transition") === "1";
    if (flag) window.sessionStorage.removeItem("landing-transition");
    return flag;
  });

  const v = form.watch();

  const onSubmit = form.handleSubmit(async (values) => {
    const t = toast.loading("Signing in…");
    try {
      const data = await apiFetch<AuthResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify(values),
      });

      setTokens({ access: data.access_token, refresh: data.refresh_token });

      toast.success("Welcome back.", { id: t });
      router.push("/app/me");
    } catch (e: unknown) {
      toast.error(getErrorMessage(e, "Failed to sign in."), { id: t });
    }
  });

  return (
    <AuthShell mode="login">
      <motion.form
        onSubmit={onSubmit}
        initial={skipIntro ? false : { opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={skipIntro ? undefined : { duration: 0.35, ease: "easeOut" }}
        className="grid gap-4"
      >
        <FloatingInput
          label="Email"
          value={v.email}
          onChange={(e) =>
            form.setValue("email", e.target.value, { shouldValidate: true })
          }
          onBlur={() => form.trigger("email")}
          autoComplete="email"
          error={form.formState.errors.email?.message}
        />

        <FloatingInput
          label="Password"
          type="password"
          value={v.password}
          onChange={(e) =>
            form.setValue("password", e.target.value, { shouldValidate: true })
          }
          onBlur={() => form.trigger("password")}
          autoComplete="current-password"
          error={form.formState.errors.password?.message}
        />

        <div className="flex items-center justify-end">
          <button
            type="button"
            className="text-xs text-[rgb(var(--muted))] hover:text-[rgb(var(--fg))]"
            onClick={() => toast.message("Forgot password (Sprint 2).")}
          >
            Forgot password?
          </button>
        </div>

        <PrimaryButton disabled={!form.formState.isValid || form.formState.isSubmitting}>
          {form.formState.isSubmitting ? "Signing in…" : "Sign in"}
        </PrimaryButton>

        <div className="relative my-1">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-[rgb(var(--border))]" />
          </div>
          <div className="relative flex justify-center text-xs">
            <span className="bg-[rgb(var(--surface))] px-2 text-[rgb(var(--muted))]">
              or
            </span>
          </div>
        </div>

        <OAuthButton provider="google" onClick={() => toast.message("OAuth later (Sprint 2).")} />
        <OAuthButton provider="facebook" onClick={() => toast.message("OAuth later (Sprint 2).")} />

        <div className="text-center text-xs text-[rgb(var(--muted))]">
          Don’t have an account?{" "}
          <Link
            className="text-[rgb(var(--fg))] underline underline-offset-4"
            href="/register"
          >
            Sign up
          </Link>
        </div>
      </motion.form>
    </AuthShell>
  );
}
