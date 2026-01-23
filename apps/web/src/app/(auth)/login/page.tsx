"use client";

import Link from "next/link";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { AuthShell } from "@/app/components/auth/AuthShell";
import { FloatingInput } from "@/app/components/ui/FloatingInput";
import { OAuthButton, PrimaryButton } from "@/app/components/ui/Buttons";

const API_URL = process.env.NEXT_PUBLIC_API_URL!;

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "At least 8 characters"),
});

type FormValues = z.infer<typeof schema>;

function parseErr(data: any) {
  return data?.detail?.error || data?.detail?.message || data?.detail || data?.error || "Login failed";
}

export default function LoginPage() {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" },
    mode: "onChange",
  });

  const { watch, formState, handleSubmit } = form;
  const email = watch("email");
  const password = watch("password");

  const onSubmit = handleSubmit(async (values) => {
    const t = toast.loading("Signing in…");
    try {
      const res = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(parseErr(data));

      localStorage.setItem("tenue_tokens", JSON.stringify({ access: data.access_token, refresh: data.refresh_token }));
      toast.success("Welcome back.", { id: t });
      window.location.href = "/me";
    } catch (e: any) {
      toast.error(e.message, { id: t });
    }
  });

  return (
    <AuthShell mode="login">
      <motion.form
        onSubmit={onSubmit}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: "easeOut" }}
        className="grid gap-4"
      >
        <FloatingInput
          label="Email"
          value={email}
          onChange={(e) => form.setValue("email", e.target.value, { shouldValidate: true })}
          onBlur={() => form.trigger("email")}
          autoComplete="email"
          error={formState.errors.email?.message}
        />

        <FloatingInput
          label="Password"
          type="password"
          value={password}
          onChange={(e) => form.setValue("password", e.target.value, { shouldValidate: true })}
          onBlur={() => form.trigger("password")}
          autoComplete="current-password"
          error={formState.errors.password?.message}
        />

        <div className="flex items-center justify-end">
          <button type="button" className="text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-white">
            Forgot password?
          </button>
        </div>

        <PrimaryButton disabled={!formState.isValid || formState.isSubmitting}>
          {formState.isSubmitting ? "Signing in…" : "Sign in"}
        </PrimaryButton>

        <div className="relative my-1">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-zinc-200 dark:border-zinc-800" />
          </div>
          <div className="relative flex justify-center text-xs">
            <span className="bg-white px-2 text-zinc-400 dark:bg-zinc-950">or</span>
          </div>
        </div>

        <OAuthButton provider="google" onClick={() => toast.message("OAuth later (Sprint 2).")} />
        <OAuthButton provider="facebook" onClick={() => toast.message("OAuth later (Sprint 2).")} />

        <div className="text-center text-xs text-zinc-500">
          Don’t have an account?{" "}
          <Link className="text-zinc-900 underline underline-offset-4 dark:text-white" href="/register">
            Sign up
          </Link>
        </div>
      </motion.form>
    </AuthShell>
  );
}
