import type { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Only the two variants an actual call site needs today
   * (docs/ui-guidelines.md lists five; outline/ghost/danger land when a
   * real consumer needs them, not speculatively). */
  variant?: "primary" | "secondary";
}

const BASE =
  "rounded-xl px-4 py-2 font-medium transition disabled:cursor-not-allowed disabled:opacity-60";

const VARIANTS: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary: "bg-primary text-white hover:opacity-90",
  secondary: "border border-border bg-surface text-text hover:bg-surface-muted",
};

export function Button({ variant = "primary", className = "", ...props }: ButtonProps) {
  return <button className={`${BASE} ${VARIANTS[variant]} ${className}`} {...props} />;
}
