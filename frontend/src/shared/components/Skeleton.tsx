import { cn } from "@/shared/utils/cn";

interface SkeletonProps {
  className?: string;
  /** Renders this many stacked lines instead of one block — for a list of
   * table rows waiting on data. */
  lines?: number;
}

/** Loading placeholder — docs/ui-guidelines.md: "Use everywhere. Never
 * show blank screens." Default consumer is `QueryBoundary` below, but any
 * feature can render one directly for a smaller inline loading spot. */
export function Skeleton({ className, lines = 1 }: SkeletonProps) {
  if (lines > 1) {
    return (
      <div className="flex flex-col gap-2">
        {Array.from({ length: lines }, (_, i) => (
          <div
            key={i}
            className={cn("h-4 animate-pulse rounded-input bg-surface-muted", className)}
          />
        ))}
      </div>
    );
  }
  return <div className={cn("h-4 animate-pulse rounded-input bg-surface-muted", className)} />;
}
