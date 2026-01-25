"use client";

import * as React from "react";
import { Eye, EyeOff } from "lucide-react";

export function FloatingInput({
  label,
  type = "text",
  value,
  onChange,
  onBlur,
  name,
  autoComplete,
  error,
  disabled,
}: {
  label: string;
  type?: string;
  value?: string;
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
  onBlur?: React.FocusEventHandler<HTMLInputElement>;
  name?: string;
  autoComplete?: string;
  error?: string;
  disabled?: boolean;
}) {
  const [show, setShow] = React.useState(false);
  const isPassword = type === "password";
  const inputType = isPassword ? (show ? "text" : "password") : type;
  const hasValue = !!value && value.length > 0;

  return (
    <div className="grid gap-1">
      <div
        className={[
          "relative rounded-2xl",
          "bg-[linear-gradient(180deg,rgb(var(--card))_0%,rgb(var(--card-2))_100%)]",
          "shadow-[0_10px_25px_-18px_rgba(2,6,23,0.45)]",
          "ring-1 ring-[rgb(var(--border))]/70",
          "focus-within:ring-2 focus-within:ring-[rgb(var(--ring))]/30",
          error ? "ring-red-500/30 dark:ring-red-500/30" : "",
          disabled ? "opacity-60" : "",
        ].join(" ")}
      >
        <div className="pointer-events-none absolute inset-x-2 top-1 h-px bg-[linear-gradient(to_right,transparent,rgba(255,255,255,0.45),transparent)] dark:bg-[linear-gradient(to_right,transparent,rgba(255,255,255,0.15),transparent)]" />
        <label
          className={[
            "absolute left-4 select-none transition-all",
            hasValue
              ? "top-2 text-[11px] text-[rgb(var(--muted))]"
              : "top-4 text-sm text-[rgb(var(--muted))]",
          ].join(" ")}
        >
          {label}
        </label>

        <input
          name={name}
          type={inputType}
          value={value}
          onChange={onChange}
          onBlur={onBlur}
          autoComplete={autoComplete}
          disabled={disabled}
          className={[
            "w-full bg-transparent outline-none",
            "px-4 pb-3 pt-6 text-sm",
            "text-[rgb(var(--fg))] placeholder:text-[rgb(var(--muted))]",
          ].join(" ")}
        />

        {isPassword && (
          <button
            type="button"
            onClick={() => setShow((s) => !s)}
            className="absolute right-3 top-3.5 inline-flex h-9 w-9 items-center justify-center rounded-xl hover:bg-[rgb(var(--card-2))]"
            aria-label={show ? "Hide password" : "Show password"}
            tabIndex={-1}
          >
            {show ? (
              <EyeOff className="h-4 w-4 text-[rgb(var(--muted))]" />
            ) : (
              <Eye className="h-4 w-4 text-[rgb(var(--muted))]" />
            )}
          </button>
        )}
      </div>

      {error ? (
        <p className="text-[11px] text-red-600 dark:text-red-300">{error}</p>
      ) : null}
    </div>
  );
}
