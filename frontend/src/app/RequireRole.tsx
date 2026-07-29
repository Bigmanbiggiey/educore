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
 */
export function RequireRole({ roles }: RequireRoleProps) {
  const { roles: userRoles } = useAuth();
  const hasAccess = roles.some((role) => userRoles.includes(role));

  if (!hasAccess) return <Navigate to="/" replace />;
  return <Outlet />;
}
