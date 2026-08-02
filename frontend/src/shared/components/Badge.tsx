import type { HTMLAttributes } from "react";

import { cn } from "@/shared/utils/cn";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: "neutral" | "success" | "warning" | "danger";
}

const TONES: Record<NonNullable<BadgeProps["tone"]>, string> = {
  neutral: "bg-surface-muted text-text",
  success: "bg-success-muted text-success",
  warning: "bg-warning-muted text-warning",
  danger: "bg-danger-muted text-danger",
};

/** A status pill — e.g. an invoice's paid/overdue state, a loan's
 * returned/active state. One shared component so every feature's status
 * indicator looks the same, per docs/frontend-architecture.md §5. */
export function Badge({ tone = "neutral", className, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        TONES[tone],
        className,
      )}
      {...props}
    />
  );
}
