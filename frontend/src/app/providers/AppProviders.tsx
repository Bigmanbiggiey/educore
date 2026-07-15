import { QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

import { queryClient } from "@/shared/lib/query-client";

/**
 * AuthProvider (current user + institution memberships) and ThemeProvider
 * (dark mode + per-institution branding, docs/frontend-architecture.md §6)
 * are added here in Phase 1, alongside the accounts/institutions backend
 * work they depend on.
 */
export function AppProviders({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
