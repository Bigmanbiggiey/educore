import type { ReactNode } from "react";

import { Skeleton } from "@/shared/components/Skeleton";

interface QueryBoundaryProps<T> {
  /** The subset of a TanStack Query result this needs — accepting the
   * minimal shape (not the full `UseQueryResult<T>`) keeps this usable
   * with `useQuery`, `useSuspenseQuery`, or a hand-assembled result alike. */
  query: {
    isPending: boolean;
    isError: boolean;
    error: unknown;
    data: T | undefined;
  };
  loadingFallback?: ReactNode;
  errorFallback?: (error: unknown) => ReactNode;
  children: (data: T) => ReactNode;
}

function defaultErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong loading this data.";
}

/** Drives loading/error UI off TanStack Query's `isPending`/`isError`
 * uniformly (docs/frontend-architecture.md §8) instead of every feature
 * hand-rolling its own spinner/error branch. */
export function QueryBoundary<T>({
  query,
  loadingFallback,
  errorFallback,
  children,
}: QueryBoundaryProps<T>) {
  if (query.isPending) {
    return <>{loadingFallback ?? <Skeleton lines={3} />}</>;
  }
  if (query.isError) {
    return (
      <>
        {errorFallback ? (
          errorFallback(query.error)
        ) : (
          <p role="alert" className="text-sm text-danger">
            {defaultErrorMessage(query.error)}
          </p>
        )}
      </>
    );
  }
  return <>{children(query.data as T)}</>;
}
