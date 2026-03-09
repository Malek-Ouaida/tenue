"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { AuthShell } from "@/components/auth/AuthShell";
import { FloatingInput } from "@/components/ui/FloatingInput";
import { PrimaryButton } from "@/components/ui/Buttons";
import { apiFetch, getErrorMessage, setTokens } from "@/lib/api";
import { trackError, trackEvent } from "@/lib/telemetry";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  username: z
    .string()
    .min(3, "3–20 characters")
    .max(20, "3–20 characters")
    .regex(/^[a-z0-9_]+$/, "Only lowercase, numbers, underscore"),
  display_name: z.string().max(50).optional().or(z.literal("")),
  password: z.string().min(8, "At least 8 characters"),
});

type FormValues = z.infer<typeof schema>;
type AuthResponse = { access_token: string; refresh_token: string };

export default function RegisterPage() {
  const router = useRouter();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", username: "", display_name: "", password: "" },
    mode: "onChange",
  });
  const [skipIntro] = useState(() => {
    if (typeof window === "undefined") return false;
    const flag = window.sessionStorage.getItem("landing-transition") === "1";
    if (flag) window.sessionStorage.removeItem("landing-transition");
    return flag;
  });

  const v = form.watch();

  useEffect(() => {
    void trackEvent("auth.register_open");
  }, []);

  const onSubmit = form.handleSubmit(async (values) => {
    const t = toast.loading("Creating account…");
    try {
      const data = await apiFetch<AuthResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email: values.email,
          username: values.username,
          display_name: values.display_name ? values.display_name : null,
          password: values.password,
        }),
      });

      setTokens({ access: data.access_token, refresh: data.refresh_token });

      toast.success("Account created.", { id: t });
      void trackEvent("auth.register_success");
      router.push("/feed");
    } catch (e: unknown) {
      toast.error(getErrorMessage(e, "Failed to create account."), { id: t });
      void trackError("auth.register_failed", e);
    }
  });

  return (
    <AuthShell mode="register">
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

        <div className="grid gap-2">
          <FloatingInput
            label="Username"
            value={v.username}
            onChange={(e) =>
              form.setValue("username", e.target.value.toLowerCase(), {
                shouldValidate: true,
              })
            }
            onBlur={() => form.trigger("username")}
            autoComplete="username"
            error={form.formState.errors.username?.message}
          />
          <p className="text-[11px] text-[rgb(var(--muted))]">
            Lowercase, 3–20 chars, letters/numbers/underscore.
          </p>
        </div>

        <FloatingInput
          label="Display name (optional)"
          value={v.display_name ?? ""}
          onChange={(e) =>
            form.setValue("display_name", e.target.value, {
              shouldValidate: true,
            })
          }
          onBlur={() => form.trigger("display_name")}
          autoComplete="name"
          error={form.formState.errors.display_name?.message as string | undefined}
        />

        <FloatingInput
          label="Password"
          type="password"
          value={v.password}
          onChange={(e) =>
            form.setValue("password", e.target.value, { shouldValidate: true })
          }
          onBlur={() => form.trigger("password")}
          autoComplete="new-password"
          error={form.formState.errors.password?.message}
        />

        <PrimaryButton disabled={!form.formState.isValid || form.formState.isSubmitting}>
          {form.formState.isSubmitting ? "Creating…" : "Create account"}
        </PrimaryButton>

        <div className="text-center text-xs text-[rgb(var(--muted))]">
          Already have an account?{" "}
          <Link
            className="text-[rgb(var(--fg))] underline underline-offset-4"
            href="/login"
          >
            Sign in
          </Link>
        </div>
      </motion.form>
    </AuthShell>
  );
}
