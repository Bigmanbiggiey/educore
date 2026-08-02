import type { HTMLAttributes } from "react";

import { cn } from "@/shared/utils/cn";

type CardProps = HTMLAttributes<HTMLDivElement>;

/**
 * The one surface container every dashboard tile, list, and future form
 * panel sits in (docs/ui-guidelines.md: card radius 16px) — per
 * docs/frontend-architecture.md §5, a feature composes this rather than
 * building its own bordered `div`.
 */
export function Card({ className, ...props }: CardProps) {
  return (
    <div
      className={cn("rounded-card border border-border bg-surface p-6 shadow-sm", className)}
      {...props}
    />
  );
}
