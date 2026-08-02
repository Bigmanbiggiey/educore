import { Inbox } from "lucide-react";
import type { ComponentType, ReactNode } from "react";

interface EmptyStateProps {
  message: string;
  /** Defaults to a generic inbox icon — pass a more specific Lucide icon
   * per feature (e.g. `Users` for an empty student roster) once one is
   * worth choosing deliberately. */
  icon?: ComponentType<{ className?: string }>;
  action?: ReactNode;
}

/** Required for every list/table view that can be empty
 * (docs/ui-guidelines.md: illustration + helpful message + CTA). */
export function EmptyState({ message, icon: Icon = Inbox, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-3 p-8 text-center">
      <Icon className="h-10 w-10 text-text/30" />
      <p className="text-sm text-text/70">{message}</p>
      {action}
    </div>
  );
}
