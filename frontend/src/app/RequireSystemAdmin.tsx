import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "./providers/AuthProvider";

export interface SystemAdminOutletContext {
  actAs: (institutionId: string, institutionName: string) => Promise<void>;
}

/**
 * Client-side gate only, for UX — never the authorization boundary; the
 * API's own `IsPlatformStaff` permission class enforces this regardless
 * of what the client renders (docs/frontend-architecture.md §1). Parallel
 * to `RequireRole`, not a variant of it: System Admin access is granted
 * via `is_platform_staff` (docs/permissions.md §7), never a role name, so
 * there's no `roles` array to check here.
 *
 * Passes `actAs` down via `Outlet` context rather than the portal
 * importing `useAuth` directly — `eslint-plugin-boundaries` forbids
 * `portals`/`features` from importing `app` (docs/frontend-architecture.md
 * §1), and `react-router-dom`'s context mechanism is the sanctioned way
 * to thread app-layer state past that boundary without violating it.
 */
export function RequireSystemAdmin() {
  const { isPlatformStaff, actAs } = useAuth();

  if (!isPlatformStaff) return <Navigate to="/" replace />;
  return <Outlet context={{ actAs } satisfies SystemAdminOutletContext} />;
}
