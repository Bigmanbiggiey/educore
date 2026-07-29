import { QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

import { queryClient } from "@/shared/lib/query-client";

import { AuthProvider } from "./AuthProvider";

/**
 * ThemeProvider (dark mode + per-institution branding,
 * docs/frontend-architecture.md §6) lands once `institutions` branding
 * fields are actually consumed somewhere — not built speculatively now.
 */
export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  );
}
