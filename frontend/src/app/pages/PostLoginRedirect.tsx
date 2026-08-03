import { Link, Navigate } from "react-router-dom";

import { PORTAL_DISPLAY_NAMES, portalSlugsForRoles } from "../portal-routing";
import { useAuth } from "../providers/AuthProvider";

/**
 * The "/" route, only ever reached inside `RequireAuth` (status is always
 * "authenticated" here). Lands the user directly in their portal if they
 * hold exactly one role at this institution; shows a lightweight picker
 * if they hold several — a Deputy Principal who also teaches is a real,
 * common case (docs/frontend-architecture.md §1).
 */
export function PostLoginRedirect() {
  const { roles, isPlatformStaff, logout } = useAuth();
  const slugs = portalSlugsForRoles(roles);

  // docs/permissions.md §7: granted via `is_platform_staff`, never a role,
  // so it never appears in `roles`/`portalSlugsForRoles` — checked first,
  // ahead of the role-based picker below.
  if (isPlatformStaff) return <Navigate to="/system-admin" replace />;

  if (slugs.length === 1) return <Navigate to={`/${slugs[0]}`} replace />;

  if (slugs.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="w-full max-w-sm rounded-2xl border border-border bg-surface p-8 text-center shadow-md">
          <p className="text-text">
            Your account has no active role at this institution yet. Contact your administrator.
          </p>
          <button
            type="button"
            onClick={() => void logout()}
            className="mt-4 text-sm text-primary hover:underline"
          >
            Sign out
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-sm rounded-2xl border border-border bg-surface p-8 shadow-md">
        <h1 className="mb-6 text-center text-2xl font-semibold text-text">Choose a portal</h1>
        <div className="flex flex-col gap-2">
          {slugs.map((slug) => (
            <Link
              key={slug}
              to={`/${slug}`}
              className="rounded-[10px] border border-border px-4 py-3 text-center text-text hover:bg-surface-muted"
            >
              {PORTAL_DISPLAY_NAMES[slug] ?? slug}
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
