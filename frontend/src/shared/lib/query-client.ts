import { QueryClient } from "@tanstack/react-query";

/**
 * Global defaults; individual feature hooks override staleTime per
 * resource sensitivity (e.g. near-zero for finance balances, near-Infinity
 * for rarely-changing reference data). See docs/frontend-architecture.md §3.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});
