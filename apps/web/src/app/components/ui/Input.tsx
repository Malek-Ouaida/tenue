import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  const { className, ...rest } = props;
  return (
    <input
      {...rest}
      className={twMerge(
        clsx(
          "h-11 w-full rounded-xl border border-zinc-200 bg-white px-3 text-sm",
          "placeholder:text-zinc-400",
          "outline-none focus:ring-4 focus:ring-zinc-200/70 focus:border-zinc-300",
          "dark:border-zinc-800 dark:bg-zinc-950 dark:focus:ring-zinc-800/70 dark:focus:border-zinc-700",
          className
        )
      )}
    />
  );
}
