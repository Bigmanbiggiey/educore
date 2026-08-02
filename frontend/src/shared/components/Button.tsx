import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/shared/utils/cn";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** The full five-variant set docs/ui-guidelines.md fixes. */
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
}

const BASE =
  "rounded-button px-4 py-2 font-medium transition disabled:cursor-not-allowed disabled:opacity-60";

const VARIANTS: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary: "bg-primary text-white hover:opacity-90",
  secondary: "border border-border bg-surface text-text hover:bg-surface-muted",
  outline: "border border-primary text-primary hover:bg-primary/10",
  ghost: "text-text hover:bg-surface-muted",
  danger: "bg-danger text-white hover:opacity-90",
};

export function Button({ variant = "primary", className, ...props }: ButtonProps) {
  return <button className={cn(BASE, VARIANTS[variant], className)} {...props} />;
}
