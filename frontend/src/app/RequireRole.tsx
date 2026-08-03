import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "./providers/AuthProvider";

interface RequireRoleProps {
  roles: string[];
}

/**
 * Client-side gate only, for UX (hiding nav, redirecting) — never the
 * authorization boundary; the API's own `IsInstitutionMember`/`HasRole`
 * permission classes enforce this regardless of what the client renders
 * (docs/frontend-architecture.md §1). Only rendered inside `RequireAuth`,
 * so `status` here is always "authenticated".
 *
 * Also passes during an active break-glass act-as session
 * (docs/permissions.md §7), regardless of `roles` — mirrors the same
 * short-circuit the backend's `IsInstitutionMember`/`HasRole`/
 * `HasPermission` already grant an acting System Admin, who holds no real
 * role at all.
 */
export function RequireRole({ roles }: RequireRoleProps) {
  const { roles: userRoles, actingAsInstitution } = useAuth();
  const hasAccess = actingAsInstitution !== null || roles.some((role) => userRoles.includes(role));

  if (!hasAccess) return <Navigate to="/" replace />;
  return <Outlet />;
}
