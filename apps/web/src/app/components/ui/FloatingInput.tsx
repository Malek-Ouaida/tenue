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

  const hasValue = !!value;

  return (
    <div className="grid gap-1">
      <div
        className={[
          "relative rounded-2xl border bg-white/70 backdrop-blur",
          "border-zinc-200 shadow-sm",
          "focus-within:ring-4 focus-within:ring-zinc-200/60 focus-within:border-zinc-300",
          "dark:bg-zinc-950/60 dark:border-zinc-800 dark:focus-within:ring-zinc-800/60 dark:focus-within:border-zinc-700",
          error ? "border-red-300 dark:border-red-900/60" : "",
          disabled ? "opacity-60" : ""
        ].join(" ")}
      >
        <label
          className={[
            "absolute left-4 transition-all pointer-events-none",
            hasValue ? "top-2 text-[11px] text-zinc-500" : "top-4 text-sm text-zinc-400",
            "dark:text-zinc-400"
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
            "text-zinc-950 dark:text-zinc-50"
          ].join(" ")}
        />

        {isPassword && (
          <button
            type="button"
            onClick={() => setShow((s) => !s)}
            className="absolute right-3 top-3.5 h-9 w-9 rounded-xl hover:bg-zinc-100 dark:hover:bg-zinc-900 inline-flex items-center justify-center"
            aria-label={show ? "Hide password" : "Show password"}
          >
            {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        )}
      </div>

      {error ? <p className="text-[11px] text-red-600 dark:text-red-300">{error}</p> : null}
    </div>
  );
}
