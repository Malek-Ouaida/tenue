import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  const { className, ...rest } = props;
  return (
    <input
      {...rest}
      className={twMerge(
        clsx(
          "h-11 w-full rounded-xl border border-[rgb(var(--border))] bg-[rgb(var(--card))] px-3 text-sm",
          "placeholder:text-[rgb(var(--muted))]",
          "text-[rgb(var(--fg))]",
          "outline-none focus:ring-4 focus:ring-[rgb(var(--ring))]/20 focus:border-[rgb(var(--ring))]/40",
          className
        )
      )}
    />
  );
}
