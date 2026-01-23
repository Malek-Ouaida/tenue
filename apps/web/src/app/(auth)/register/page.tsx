"use client";

import Link from "next/link";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { AuthShell } from "@/app/components/auth/AuthShell";
import { FloatingInput } from "@/app/components/ui/FloatingInput";
import { PrimaryButton } from "@/app/components/ui/Buttons";

const API_URL = process.env.NEXT_PUBLIC_API_URL!;

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  username: z.string().min(3, "3–20 characters").max(20, "3–20 characters").regex(/^[a-z0-9_]+$/, "Only lowercase, numbers, underscore"),
  display_name: z.string().max(50).optional().or(z.literal("")),
  password: z.string().min(8, "At least 8 characters"),
});

type FormValues = z.infer<typeof schema>;

function parseErr(data: any) {
  return data?.detail?.error || data?.detail?.message || data?.detail || data?.error || "Registration failed";
}

export default function RegisterPage() {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", username: "", display_name: "", password: "" },
    mode: "onChange",
  });

  const v = form.watch();

  const onSubmit = form.handleSubmit(async (values) => {
    const t = toast.loading("Creating account…");
    try {
      const res = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: values.email,
          username: values.username,
          display_name: values.display_name ? values.display_name : null,
          password: values.password,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(parseErr(data));

      localStorage.setItem("tenue_tokens", JSON.stringify({ access: data.access_token, refresh: data.refresh_token }));
      toast.success("Account created.", { id: t });
      window.location.href = "/me";
    } catch (e: any) {
      toast.error(e.message, { id: t });
    }
  });

  return (
    <AuthShell mode="register">
      <motion.form
        onSubmit={onSubmit}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: "easeOut" }}
        className="grid gap-4"
      >
        <FloatingInput
          label="Email"
          value={v.email}
          onChange={(e) => form.setValue("email", e.target.value, { shouldValidate: true })}
          onBlur={() => form.trigger("email")}
          autoComplete="email"
          error={form.formState.errors.email?.message}
        />

        <div className="grid gap-2">
          <FloatingInput
            label="Username"
            value={v.username}
            onChange={(e) => form.setValue("username", e.target.value.toLowerCase(), { shouldValidate: true })}
            onBlur={() => form.trigger("username")}
            autoComplete="username"
            error={form.formState.errors.username?.message}
          />
          <p className="text-[11px] text-zinc-500">Lowercase, 3–20 chars, letters/numbers/underscore.</p>
        </div>

        <FloatingInput
          label="Display name (optional)"
          value={v.display_name ?? ""}
          onChange={(e) => form.setValue("display_name", e.target.value, { shouldValidate: true })}
          onBlur={() => form.trigger("display_name")}
          autoComplete="name"
          error={form.formState.errors.display_name?.message as any}
        />

        <FloatingInput
          label="Password"
          type="password"
          value={v.password}
          onChange={(e) => form.setValue("password", e.target.value, { shouldValidate: true })}
          onBlur={() => form.trigger("password")}
          autoComplete="new-password"
          error={form.formState.errors.password?.message}
        />

        <PrimaryButton disabled={!form.formState.isValid || form.formState.isSubmitting}>
          {form.formState.isSubmitting ? "Creating…" : "Create account"}
        </PrimaryButton>

        <div className="text-center text-xs text-zinc-500">
          Already have an account?{" "}
          <Link className="text-zinc-900 underline underline-offset-4 dark:text-white" href="/login">
            Sign in
          </Link>
        </div>
      </motion.form>
    </AuthShell>
  );
}
